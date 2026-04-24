#!/usr/bin/env python3
"""Autonomous harness optimization runner.

The runner keeps the current checkout untouched. It creates a fresh worktree
from a base ref, asks codex-subagent to make one scoped improvement, validates
the result, and only then opens a pull request.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_REGISTRY_PATH = (
    ROOT_DIR / "docs" / "architecture" / "harness-resources.toml"
)
DEFAULT_LOG_ROOT = ROOT_DIR / ".codex" / "sessions" / "harness_autopt"
DEFAULT_GATES = ("make doctor", "make lint", "make test")
PROTECTED_PREFIXES = (
    ".env",
    "secrets/",
    ".codex/auth",
    ".codex/history",
    ".codex/state",
    ".claude/settings.local.json",
    ".claude/.claude/",
)
RESOURCE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner:
    def run(
        self,
        cmd: list[str],
        cwd: Path,
        *,
        check: bool = False,
    ) -> CommandResult:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        result = CommandResult(proc.returncode, proc.stdout, proc.stderr)
        if check and result.returncode != 0:
            raise RuntimeError(
                f"command failed ({result.returncode}): {' '.join(cmd)}\n"
                f"{result.stderr or result.stdout}"
            )
        return result


@dataclass(frozen=True)
class HarnessResource:
    id: str
    kind: str
    authority: str
    paths: tuple[str, ...]
    mutable_paths: tuple[str, ...]
    validators: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    mutation_policy: str = "proposal"
    risk_level: str = "medium"
    goals: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiffGuardResult:
    ok: bool
    changed_files: tuple[str, ...]
    changed_lines: int
    violations: tuple[str, ...] = ()


@dataclass
class AutoptConfig:
    target: str
    goal: str
    candidate_count: int
    base: str
    worktree_root: Path
    create_pr: bool
    registry_path: Path = DEFAULT_REGISTRY_PATH
    log_root: Path = DEFAULT_LOG_ROOT
    max_changed_files: int = 8
    max_changed_lines: int = 800
    timeout_seconds: int = 900
    keep_worktree: bool = False
    dry_run: bool = False


@dataclass
class AutoptState:
    run_id: str
    branch: str
    worktree: Path
    target: str
    goal: str
    events: list[dict[str, Any]] = field(default_factory=list)
    pr_url: str | None = None

    def record(self, event: str, **payload: Any) -> None:
        self.events.append(
            {
                "event": event,
                "timestamp": datetime.now(UTC).isoformat(),
                **payload,
            }
        )


def load_resource_registry(path: Path) -> dict[str, HarnessResource]:
    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    resources: dict[str, HarnessResource] = {}
    for item in raw.get("resources", []):
        resource = HarnessResource(
            id=str(item["id"]),
            kind=str(item["kind"]),
            authority=str(item.get("authority", "canonical")),
            paths=tuple(str(path) for path in item.get("paths", [])),
            mutable_paths=tuple(
                str(path)
                for path in item.get("mutable_paths", item.get("paths", []))
            ),
            validators=tuple(
                str(command)
                for command in item.get("validators", list(DEFAULT_GATES))
            ),
            depends_on=tuple(str(dep) for dep in item.get("depends_on", [])),
            mutation_policy=str(item.get("mutation_policy", "proposal")),
            risk_level=str(item.get("risk_level", "medium")),
            goals=tuple(str(goal) for goal in item.get("goals", [])),
        )
        if not RESOURCE_ID_RE.fullmatch(resource.id):
            raise ValueError(f"invalid resource id: {resource.id}")
        if resource.id in resources:
            raise ValueError(f"duplicate resource id: {resource.id}")
        resources[resource.id] = resource
    return resources


def normalize_rel_path(path: str) -> str:
    normalized = Path(path).as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if Path(normalized).is_absolute() or normalized.startswith("../"):
        raise ValueError(f"path must be repo-relative: {path}")
    return normalized


def path_matches_prefix(path: str, prefix: str) -> bool:
    clean_path = normalize_rel_path(path)
    clean_prefix = normalize_rel_path(prefix).rstrip("/")
    return clean_path == clean_prefix or clean_path.startswith(
        f"{clean_prefix}/"
    )


def is_protected_path(path: str) -> bool:
    clean = normalize_rel_path(path)
    return any(
        clean == prefix.rstrip("/") or clean.startswith(prefix)
        for prefix in PROTECTED_PREFIXES
    )


def is_path_allowed(path: str, allowed_prefixes: tuple[str, ...]) -> bool:
    if is_protected_path(path):
        return False
    return any(
        path_matches_prefix(path, prefix) for prefix in allowed_prefixes
    )


def parse_status_paths(status_output: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in status_output.splitlines():
        if not line:
            continue
        raw = line[3:] if len(line) > 3 else line
        if " -> " in raw:
            old, new = raw.split(" -> ", 1)
            paths.extend([old.strip(), new.strip()])
        else:
            paths.append(raw.strip())
    return tuple(sorted(set(paths)))


def parse_numstat_lines(numstat_output: str) -> int:
    total = 0
    for line in numstat_output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        for value in parts[:2]:
            if value.isdigit():
                total += int(value)
    return total


def count_untracked_lines(worktree: Path, paths: tuple[str, ...]) -> int:
    total = 0
    for rel in paths:
        path = worktree / rel
        if not path.is_file():
            continue
        try:
            total += len(path.read_text(encoding="utf-8").splitlines())
        except UnicodeDecodeError:
            total += 1
    return total


def evaluate_diff_guard(
    *,
    changed_files: tuple[str, ...],
    changed_lines: int,
    allowed_prefixes: tuple[str, ...],
    max_changed_files: int,
    max_changed_lines: int,
) -> DiffGuardResult:
    violations: list[str] = []
    if len(changed_files) > max_changed_files:
        violations.append(
            f"changed file count {len(changed_files)} exceeds {max_changed_files}"
        )
    if changed_lines > max_changed_lines:
        violations.append(
            f"changed line count {changed_lines} exceeds {max_changed_lines}"
        )
    for path in changed_files:
        if not is_path_allowed(path, allowed_prefixes):
            violations.append(f"path is not allowed: {path}")
    return DiffGuardResult(
        ok=not violations,
        changed_files=changed_files,
        changed_lines=changed_lines,
        violations=tuple(violations),
    )


def build_run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def base_branch_name(base: str) -> str:
    if base.startswith("origin/"):
        return base.split("/", 1)[1]
    return base


def build_branch_name(target: str, run_id: str) -> str:
    date = datetime.now(UTC).strftime("%Y%m%d")
    suffix = run_id.rsplit("-", 1)[-1]
    return f"autopt/{target}-{date}-{suffix}"


def build_candidate_prompt(resource: HarnessResource, goal: str) -> str:
    paths = "\n".join(f"- {path}" for path in resource.mutable_paths)
    validators = "\n".join(
        f"- {validator}" for validator in resource.validators
    )
    return f"""You are running autonomous harness optimization for this repository.

Target resource: {resource.id}
Resource kind: {resource.kind}
Goal: {goal}

Make exactly one small stability improvement. Prefer deterministic validation,
schema guardrails, timeout reduction, retry safety, or documentation that makes
the existing harness more reliable. Do not broaden scope.

Editable paths:
{paths}

Required validation commands:
{validators}

Rules:
- Do not read or modify .env*, secrets/**, local auth files, or runtime state.
- Do not create commits, branches, pushes, or pull requests.
- Do not edit files outside the editable paths.
- Keep the diff small enough for a single pull request.
- If no safe improvement is available, leave the repository unchanged and say why.
"""


def build_pr_body(
    *,
    state: AutoptState,
    resource: HarnessResource,
    diff_guard: DiffGuardResult,
    gate_commands: tuple[str, ...],
) -> str:
    files = (
        "\n".join(f"- `{path}`" for path in diff_guard.changed_files)
        or "- n/a"
    )
    gates = "\n".join(f"- `{command}`: pass" for command in gate_commands)
    summary = (
        f"Autonomous harness optimization run `{state.run_id}` improved "
        f"`{resource.id}` for `{state.goal}`."
    )
    return f"""## Summary

{summary}

## Changed Files

{files}

## Validation

{gates}

## Diff Guard

- changed files: {len(diff_guard.changed_files)}
- changed lines: {diff_guard.changed_lines}
- violations: none

Raw prompts, raw model outputs, and local runtime logs are intentionally omitted.
"""


def write_state(log_root: Path, state: AutoptState) -> Path:
    path = log_root / datetime.now(UTC).strftime("%Y/%m/%d") / state.run_id
    path.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": state.run_id,
        "branch": state.branch,
        "worktree": str(state.worktree),
        "target": state.target,
        "goal": state.goal,
        "pr_url": state.pr_url,
        "events": state.events,
    }
    state_path = path / "state.json"
    state_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return state_path


def run_shell_command(
    runner: CommandRunner, command: str, cwd: Path
) -> CommandResult:
    return runner.run(["bash", "-lc", command], cwd)


def run_gate_commands(
    runner: CommandRunner,
    commands: tuple[str, ...],
    cwd: Path,
    state: AutoptState,
    phase: str,
) -> bool:
    for command in commands:
        result = run_shell_command(runner, command, cwd)
        state.record(
            "gate",
            phase=phase,
            command=command,
            returncode=result.returncode,
            stdout_tail=result.stdout[-2000:],
            stderr_tail=result.stderr[-2000:],
        )
        if result.returncode != 0:
            return False
    return True


def collect_diff_guard(
    runner: CommandRunner,
    worktree: Path,
    resource: HarnessResource,
    config: AutoptConfig,
) -> DiffGuardResult:
    status = runner.run(["git", "status", "--porcelain"], worktree, check=True)
    changed_files = parse_status_paths(status.stdout)
    numstat = runner.run(
        ["git", "diff", "--numstat", "HEAD", "--"], worktree, check=True
    )
    changed_lines = parse_numstat_lines(numstat.stdout)

    untracked = runner.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        worktree,
        check=True,
    )
    untracked_paths = tuple(
        path.strip() for path in untracked.stdout.splitlines() if path.strip()
    )
    changed_lines += count_untracked_lines(worktree, untracked_paths)

    return evaluate_diff_guard(
        changed_files=changed_files,
        changed_lines=changed_lines,
        allowed_prefixes=resource.mutable_paths,
        max_changed_files=config.max_changed_files,
        max_changed_lines=config.max_changed_lines,
    )


def run_candidate_generation(
    runner: CommandRunner,
    worktree: Path,
    resource: HarnessResource,
    config: AutoptConfig,
    state: AutoptState,
) -> bool:
    prompt = build_candidate_prompt(resource, config.goal)
    if config.dry_run:
        state.record("candidate_generation", dry_run=True)
        return True

    cmd = [
        "uv",
        "run",
        "python",
        ".claude/skills/codex-subagent/scripts/codex_exec.py",
        "--mode",
        "single",
        "--task-type",
        "code_gen",
        "--sandbox",
        "workspace-write",
        "--timeout",
        str(config.timeout_seconds),
        "--json",
        "--prompt",
        prompt,
    ]
    result = runner.run(cmd, worktree)
    state.record(
        "candidate_generation",
        returncode=result.returncode,
        stdout_tail=result.stdout[-2000:],
        stderr_tail=result.stderr[-2000:],
    )
    if result.returncode != 0:
        return False
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    return bool(payload.get("success", False))


def preflight(
    runner: CommandRunner,
    config: AutoptConfig,
    resources: dict[str, HarnessResource],
) -> HarnessResource:
    if config.candidate_count != 1:
        raise ValueError("v1 supports --candidate-count 1 only")
    if config.target not in resources:
        raise ValueError(f"unknown target resource: {config.target}")
    resource = resources[config.target]
    if resource.goals and config.goal not in resource.goals:
        raise ValueError(
            f"goal {config.goal!r} is not registered for {config.target}"
        )

    required = ["git", "uv", "codex"]
    if config.create_pr:
        required.append("gh")
    missing = [
        command for command in required if shutil.which(command) is None
    ]
    if missing:
        raise RuntimeError(
            "missing required command(s): " + ", ".join(missing)
        )

    runner.run(["git", "rev-parse", "--show-toplevel"], ROOT_DIR, check=True)
    runner.run(
        ["git", "rev-parse", "--verify", f"{config.base}^{{commit}}"],
        ROOT_DIR,
        check=True,
    )
    if config.create_pr:
        runner.run(["gh", "auth", "status"], ROOT_DIR, check=True)
    return resource


def create_worktree(
    runner: CommandRunner,
    config: AutoptConfig,
    state: AutoptState,
) -> None:
    state.worktree.parent.mkdir(parents=True, exist_ok=True)
    runner.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            state.branch,
            str(state.worktree),
            config.base,
        ],
        ROOT_DIR,
        check=True,
    )
    state.record(
        "worktree_created", path=str(state.worktree), branch=state.branch
    )


def create_pull_request(
    runner: CommandRunner,
    worktree: Path,
    state: AutoptState,
    resource: HarnessResource,
    diff_guard: DiffGuardResult,
    base: str,
) -> str:
    title = f"[harness-autopt] improve {resource.id} stability"
    body = build_pr_body(
        state=state,
        resource=resource,
        diff_guard=diff_guard,
        gate_commands=resource.validators,
    )
    runner.run(["git", "add", "-A"], worktree, check=True)
    runner.run(
        [
            "git",
            "commit",
            "-m",
            title,
            "-m",
            f"Run: {state.run_id}",
        ],
        worktree,
        check=True,
    )
    runner.run(
        ["git", "push", "-u", "origin", state.branch], worktree, check=True
    )
    result = runner.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            base_branch_name(base),
            "--head",
            state.branch,
        ],
        worktree,
        check=True,
    )
    return result.stdout.strip()


def cleanup_worktree(runner: CommandRunner, state: AutoptState) -> None:
    if state.worktree.exists():
        runner.run(
            ["git", "worktree", "remove", "--force", str(state.worktree)],
            ROOT_DIR,
        )


def run_autoptimization(
    config: AutoptConfig,
    *,
    runner: CommandRunner | None = None,
) -> int:
    runner = runner or CommandRunner()
    resources = load_resource_registry(config.registry_path)
    resource = preflight(runner, config, resources)
    run_id = build_run_id()
    branch = build_branch_name(config.target, run_id)
    worktree = config.worktree_root
    if not worktree.is_absolute():
        worktree = ROOT_DIR / worktree
    worktree = worktree / run_id
    state = AutoptState(run_id, branch, worktree, config.target, config.goal)

    try:
        create_worktree(runner, config, state)
        if not run_gate_commands(
            runner, resource.validators, worktree, state, "baseline"
        ):
            state.record("abort", reason="baseline gate failed")
            return 2
        if not run_candidate_generation(
            runner, worktree, resource, config, state
        ):
            state.record("abort", reason="candidate generation failed")
            return 2

        diff_guard = collect_diff_guard(runner, worktree, resource, config)
        state.record(
            "diff_guard",
            ok=diff_guard.ok,
            changed_files=list(diff_guard.changed_files),
            changed_lines=diff_guard.changed_lines,
            violations=list(diff_guard.violations),
        )
        if not diff_guard.changed_files:
            state.record("abort", reason="candidate produced no changes")
            return 2
        if not diff_guard.ok:
            state.record("abort", reason="diff guard failed")
            return 2

        if not run_gate_commands(
            runner, resource.validators, worktree, state, "candidate"
        ):
            state.record("abort", reason="candidate gate failed")
            return 2

        if config.create_pr and not config.dry_run:
            state.pr_url = create_pull_request(
                runner, worktree, state, resource, diff_guard, config.base
            )
            state.record("pull_request_created", url=state.pr_url)
        else:
            state.record("pull_request_skipped", dry_run=config.dry_run)
        return 0
    finally:
        state_path = write_state(config.log_root, state)
        print(f"harness autopt state: {state_path}")
        if not config.keep_worktree:
            cleanup_worktree(runner, state)


def print_resources(registry_path: Path) -> None:
    resources = load_resource_registry(registry_path)
    for resource in resources.values():
        print(f"{resource.id}\t{resource.kind}\t{resource.risk_level}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Autonomously optimize registered harness resources."
    )
    parser.add_argument("--target", default="codex-subagent")
    parser.add_argument("--goal", default="stability")
    parser.add_argument("--candidate-count", type=int, default=1)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument(
        "--worktree-root", type=Path, default=Path("worker/harness-autopt")
    )
    parser.add_argument(
        "--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH
    )
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    parser.add_argument("--max-changed-files", type=int, default=8)
    parser.add_argument("--max-changed-lines", type=int, default=800)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--create-pr", action="store_true")
    parser.add_argument("--keep-worktree", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-resources", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_resources:
        print_resources(args.registry_path)
        return 0
    config = AutoptConfig(
        target=args.target,
        goal=args.goal,
        candidate_count=args.candidate_count,
        base=args.base,
        worktree_root=args.worktree_root,
        create_pr=args.create_pr,
        registry_path=args.registry_path,
        log_root=args.log_root,
        max_changed_files=args.max_changed_files,
        max_changed_lines=args.max_changed_lines,
        timeout_seconds=args.timeout,
        keep_worktree=args.keep_worktree,
        dry_run=args.dry_run,
    )
    try:
        return run_autoptimization(config)
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
