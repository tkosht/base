#!/usr/bin/env python3
"""Helpers for Codex-controlled harness optimization.

Codex agents own classification, repair, and reflection. This module only
provides deterministic support functions: prompt assembly, registry parsing,
request serialization, sanitized state recording, diff guards, validation
helpers, and draft pull request helpers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import tomllib
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_REGISTRY_PATH = (
    ROOT_DIR / "docs" / "architecture" / "harness-resources.toml"
)
DEFAULT_LOG_ROOT = ROOT_DIR / ".codex" / "sessions" / "harness_autopt"
PROMPT_DIR = (
    ROOT_DIR / ".claude" / "skills" / "harness-autoptimizer" / "prompts"
)
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
RETENTION_DECISIONS = {
    "discard",
    "state-only",
    "code-simplification",
    "test",
    "validator",
    "canonical-rule",
    "skill-prompt",
    "decision-record",
}
HIGH_SIGNAL_TERMS = {
    "authority",
    "candidate_generation",
    "complexity",
    "conflict",
    "contradiction",
    "controller",
    "manual",
    "overcomplicated",
    "self-audit",
    "target/goal",
    "--target",
    "--goal",
}


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
    excluded_paths: tuple[str, ...] = ()
    max_changed_files: int | None = None
    max_changed_lines: int | None = None


@dataclass(frozen=True)
class DiffGuardResult:
    ok: bool
    changed_files: tuple[str, ...]
    changed_lines: int
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutoptSignal:
    command: str
    returncode: int
    duration_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass(frozen=True)
class AutoptClassification:
    resource_id: str
    goal: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class AutoptConstraints:
    editable_paths: tuple[str, ...]
    excluded_paths: tuple[str, ...]
    protected_prefixes: tuple[str, ...]
    max_changed_files: int
    max_changed_lines: int
    validators: tuple[str, ...]


@dataclass(frozen=True)
class AutoptRequest:
    trigger_source: str
    classification: AutoptClassification
    constraints: AutoptConstraints
    evidence: tuple[str, ...]
    signals: tuple[AutoptSignal, ...]
    success_criteria: tuple[str, ...]
    candidate_resource_ids: tuple[str, ...]
    pr_policy: str = "draft"


@dataclass(frozen=True)
class ExperienceCandidate:
    trigger_source: str
    observation: str
    evidence: tuple[str, ...]
    impact: str = "medium"
    recurrence: str = "unknown"
    generality: str = "unknown"
    verification: str = "unknown"
    context_cost: str = "unknown"


@dataclass(frozen=True)
class ExperienceAssessment:
    decision: str
    placement: str
    confidence: float
    reason: str


@dataclass
class AutoptState:
    run_id: str
    branch: str
    worktree: Path
    resource_id: str
    goal: str
    events: list[dict[str, Any]] = field(default_factory=list)
    pr_url: str | None = None

    def record(self, event: str, **payload: Any) -> None:
        self.events.append(
            {
                "event": event,
                "timestamp": datetime.now(UTC).isoformat(),
                **sanitize_state_payload(payload),
            }
        )


def sanitize_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop raw model/prompt/log payloads before writing helper state."""

    blocked_keys = {
        "prompt",
        "raw_prompt",
        "raw_output",
        "model_output",
        "stdout",
        "stderr",
        "stdout_tail",
        "stderr_tail",
    }
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if key in blocked_keys or key.endswith("_tail"):
            clean[f"{key}_omitted"] = True
            continue
        clean[key] = value
    return clean


def _experience_text(candidate: ExperienceCandidate) -> str:
    return " ".join((candidate.observation, *candidate.evidence)).casefold()


def assess_experience_candidate(
    candidate: ExperienceCandidate,
) -> ExperienceAssessment:
    """Classify whether a task experience should be retained."""

    text = _experience_text(candidate)
    if "one-off" in text or "一回限り" in text:
        return ExperienceAssessment(
            decision="discard",
            placement="none",
            confidence=0.76,
            reason=(
                "The evidence is task-specific and does not justify a durable "
                "harness change."
            ),
        )

    if any(
        marker in text
        for marker in (
            "candidate_generation",
            "python runner",
            "controller responsibility",
            "責務混入",
        )
    ):
        return ExperienceAssessment(
            decision="code-simplification",
            placement=".claude/skills/harness-autoptimizer/scripts/harness_autopt.py",
            confidence=0.92,
            reason=(
                "The experience shows implementation ownership leaking from "
                "the Codex controller into the helper."
            ),
        )

    if any(
        marker in text
        for marker in (
            "target/goal",
            "--target",
            "--goal",
            "target=project",
            "human had to set",
            "人間が",
            "manual orchestration",
        )
    ):
        return ExperienceAssessment(
            decision="canonical-rule",
            placement="docs/ai/repo-contract.md",
            confidence=0.88,
            reason=(
                "The experience shows a manual orchestration dependency that "
                "should be prohibited repo-wide."
            ),
        )

    if any(
        marker in text
        for marker in (
            "contradiction",
            "conflict",
            "authority",
            "adapter leakage",
            "矛盾",
            "正本",
        )
    ):
        return ExperienceAssessment(
            decision="canonical-rule",
            placement="docs/ai/experience-capture.md",
            confidence=0.84,
            reason=(
                "The experience concerns instruction authority and should be "
                "resolved in the canonical instruction surface."
            ),
        )

    if any(
        marker in text
        for marker in (
            "complexity",
            "overcomplicated",
            "too many branches",
            "複雑",
            "分岐",
        )
    ):
        return ExperienceAssessment(
            decision="code-simplification",
            placement="nearest implementation and tests",
            confidence=0.8,
            reason=(
                "The experience points to simpler implementation structure "
                "rather than a new durable rule."
            ),
        )

    if any(
        marker in text
        for marker in ("test", "validator", "gate", "regression")
    ):
        return ExperienceAssessment(
            decision="test",
            placement="nearest regression test or validator",
            confidence=0.78,
            reason="The experience is best retained as executable verification.",
        )

    if any(term in text for term in HIGH_SIGNAL_TERMS):
        return ExperienceAssessment(
            decision="state-only",
            placement="sanitized non-tracked state",
            confidence=0.62,
            reason=(
                "The signal is relevant but not specific enough to promote "
                "without more evidence."
            ),
        )

    return ExperienceAssessment(
        decision="state-only",
        placement="sanitized non-tracked state",
        confidence=0.55,
        reason=(
            "The experience may be useful later but does not yet justify a "
            "durable repo change."
        ),
    )


def experience_candidate_to_dict(
    candidate: ExperienceCandidate,
) -> dict[str, Any]:
    return asdict(candidate)


def experience_assessment_to_dict(
    assessment: ExperienceAssessment,
) -> dict[str, Any]:
    if assessment.decision not in RETENTION_DECISIONS:
        raise ValueError(f"unknown retention decision: {assessment.decision}")
    return asdict(assessment)


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
            excluded_paths=tuple(
                str(path) for path in item.get("excluded_paths", [])
            ),
            max_changed_files=optional_positive_int(
                item.get("max_changed_files"), "max_changed_files"
            ),
            max_changed_lines=optional_positive_int(
                item.get("max_changed_lines"), "max_changed_lines"
            ),
        )
        if not RESOURCE_ID_RE.fullmatch(resource.id):
            raise ValueError(f"invalid resource id: {resource.id}")
        if resource.id in resources:
            raise ValueError(f"duplicate resource id: {resource.id}")
        resources[resource.id] = resource
    return resources


def optional_positive_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


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


def is_path_excluded(path: str, excluded_prefixes: tuple[str, ...]) -> bool:
    return any(
        path_matches_prefix(path, prefix) for prefix in excluded_prefixes
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
    excluded_prefixes: tuple[str, ...] = (),
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
        if is_path_excluded(path, excluded_prefixes):
            violations.append(f"path is excluded: {path}")
        elif not is_path_allowed(path, allowed_prefixes):
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


def resource_catalog_item(resource: HarnessResource) -> dict[str, Any]:
    return {
        "id": resource.id,
        "kind": resource.kind,
        "risk_level": resource.risk_level,
        "mutation_policy": resource.mutation_policy,
        "goals": list(resource.goals),
        "paths": list(resource.paths),
        "mutable_paths": list(resource.mutable_paths),
        "excluded_paths": list(resource.excluded_paths),
        "validators": list(resource.validators),
        "max_changed_files": resource.max_changed_files,
        "max_changed_lines": resource.max_changed_lines,
    }


def build_resource_catalog(
    resources: dict[str, HarnessResource],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        resource_catalog_item(resources[resource_id])
        for resource_id in sorted(resources)
    )


def build_constraints(
    resource: HarnessResource,
    *,
    default_max_changed_files: int = 8,
    default_max_changed_lines: int = 800,
) -> AutoptConstraints:
    return AutoptConstraints(
        editable_paths=resource.mutable_paths,
        excluded_paths=resource.excluded_paths,
        protected_prefixes=PROTECTED_PREFIXES,
        max_changed_files=resource.max_changed_files
        or default_max_changed_files,
        max_changed_lines=resource.max_changed_lines
        or default_max_changed_lines,
        validators=resource.validators,
    )


def build_success_criteria(resource: HarnessResource) -> tuple[str, ...]:
    validators = ", ".join(resource.validators)
    return (
        "The Codex agent keeps the change inside editable_paths.",
        "The change does not touch excluded_paths or protected prefixes.",
        "The diff stays within max_changed_files and max_changed_lines.",
        f"Validators pass: {validators}.",
        "The pull request is draft and omits raw prompts, raw outputs, "
        "secrets, and runtime logs.",
    )


def build_autopt_request(
    *,
    resources: dict[str, HarnessResource],
    resource_id: str,
    goal: str,
    trigger_source: str,
    confidence: float,
    reason: str,
    evidence: tuple[str, ...],
    signals: tuple[AutoptSignal, ...] = (),
) -> AutoptRequest:
    if resource_id not in resources:
        raise ValueError(f"unknown target resource: {resource_id}")
    resource = resources[resource_id]
    if resource.goals and goal not in resource.goals:
        raise ValueError(f"goal {goal!r} is not registered for {resource_id}")
    return AutoptRequest(
        trigger_source=trigger_source,
        classification=AutoptClassification(
            resource_id=resource_id,
            goal=goal,
            confidence=confidence,
            reason=reason,
        ),
        constraints=build_constraints(resource),
        evidence=evidence,
        signals=signals,
        success_criteria=build_success_criteria(resource),
        candidate_resource_ids=tuple(sorted(resources)),
    )


def is_request_actionable(
    request: AutoptRequest, *, min_confidence: float = 0.7
) -> bool:
    return request.classification.confidence >= min_confidence


def autopt_request_to_dict(request: AutoptRequest) -> dict[str, Any]:
    return asdict(request)


def load_prompt_template(name: str) -> str:
    path = PROMPT_DIR / name
    return path.read_text(encoding="utf-8")


def build_controller_prompt(resources: dict[str, HarnessResource]) -> str:
    template = load_prompt_template("auto-controller.md")
    self_audit = load_prompt_template("self-audit.md")
    experience_to_rule = load_prompt_template("experience-to-rule.md")
    catalog = json.dumps(
        build_resource_catalog(resources),
        ensure_ascii=False,
        indent=2,
    )
    return (
        f"{template}\n\n"
        f"## Self-Audit Contract\n\n{self_audit}\n\n"
        f"## Experience-to-Rule Contract\n\n{experience_to_rule}\n\n"
        f"## Harness Resource Registry\n\n```json\n{catalog}\n```\n"
    )


def build_repair_prompt(request: AutoptRequest) -> str:
    template = load_prompt_template("repair-request.md")
    payload = json.dumps(
        autopt_request_to_dict(request),
        ensure_ascii=False,
        indent=2,
    )
    return f"{template}\n\n## AutoptRequest\n\n```json\n{payload}\n```\n"


def build_self_audit_prompt(
    candidate: ExperienceCandidate | None = None,
) -> str:
    template = load_prompt_template("self-audit.md")
    if candidate is None:
        return template
    payload = json.dumps(
        experience_candidate_to_dict(candidate),
        ensure_ascii=False,
        indent=2,
    )
    return f"{template}\n\n## ExperienceCandidate\n\n```json\n{payload}\n```\n"


def build_experience_to_rule_prompt(
    candidate: ExperienceCandidate | None = None,
    assessment: ExperienceAssessment | None = None,
) -> str:
    template = load_prompt_template("experience-to-rule.md")
    sections = [template]
    if candidate is not None:
        sections.append(
            "## ExperienceCandidate\n\n```json\n"
            + json.dumps(
                experience_candidate_to_dict(candidate),
                ensure_ascii=False,
                indent=2,
            )
            + "\n```"
        )
    if assessment is not None:
        sections.append(
            "## ExperienceAssessment\n\n```json\n"
            + json.dumps(
                experience_assessment_to_dict(assessment),
                ensure_ascii=False,
                indent=2,
            )
            + "\n```"
        )
    return "\n\n".join(sections) + "\n"


def write_autopt_request(
    log_root: Path, run_id: str, request: AutoptRequest
) -> Path:
    path = log_root / datetime.now(UTC).strftime("%Y/%m/%d") / run_id
    path.mkdir(parents=True, exist_ok=True)
    request_path = path / "request.json"
    request_path.write_text(
        json.dumps(
            autopt_request_to_dict(request),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return request_path


def build_pr_title(resource: HarnessResource, goal: str) -> str:
    return f"[harness-autopt] improve {resource.id} {goal}"


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
        f"Codex-controlled harness optimization run `{state.run_id}` improved "
        f"`{resource.id}` for `{state.goal}`."
    )
    return f"""## Summary

{summary}

## Resource

- target: `{resource.id}`
- kind: `{resource.kind}`
- goal: `{state.goal}`

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
        "resource_id": state.resource_id,
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
        started = time.monotonic()
        result = run_shell_command(runner, command, cwd)
        duration_seconds = round(time.monotonic() - started, 3)
        state.record(
            "gate",
            phase=phase,
            command=command,
            returncode=result.returncode,
            duration_seconds=duration_seconds,
        )
        if result.returncode != 0:
            return False
    return True


def collect_diff_guard(
    runner: CommandRunner,
    worktree: Path,
    resource: HarnessResource,
    *,
    default_max_changed_files: int = 8,
    default_max_changed_lines: int = 800,
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
        max_changed_files=resource.max_changed_files
        or default_max_changed_files,
        max_changed_lines=resource.max_changed_lines
        or default_max_changed_lines,
        excluded_prefixes=resource.excluded_paths,
    )


def is_pr_creation_allowed(
    resource: HarnessResource, allow_guarded_pr: bool
) -> bool:
    if resource.mutation_policy == "autonomous_pr":
        return True
    return resource.mutation_policy == "guarded_pr" and allow_guarded_pr


def create_pull_request(
    runner: CommandRunner,
    worktree: Path,
    state: AutoptState,
    resource: HarnessResource,
    diff_guard: DiffGuardResult,
    base: str,
    *,
    draft: bool = False,
) -> str:
    title = build_pr_title(resource, state.goal)
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
        build_pr_create_command(
            title=title,
            body=body,
            base=base_branch_name(base),
            head=state.branch,
            draft=draft,
        ),
        worktree,
        check=True,
    )
    return result.stdout.strip()


def build_pr_create_command(
    *,
    title: str,
    body: str,
    base: str,
    head: str,
    draft: bool,
) -> list[str]:
    command = [
        "gh",
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--base",
        base,
        "--head",
        head,
    ]
    if draft:
        command.append("--draft")
    return command


def print_resources(registry_path: Path) -> None:
    resources = load_resource_registry(registry_path)
    for resource in resources.values():
        print(f"{resource.id}\t{resource.kind}\t{resource.risk_level}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Codex-controller harness optimization artifacts."
    )
    parser.add_argument(
        "--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH
    )
    parser.add_argument("--print-controller-prompt", action="store_true")
    parser.add_argument("--print-self-audit-prompt", action="store_true")
    parser.add_argument(
        "--print-experience-to-rule-prompt", action="store_true"
    )
    parser.add_argument("--list-resources", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_resources:
        print_resources(args.registry_path)
        return 0
    if args.print_controller_prompt:
        resources = load_resource_registry(args.registry_path)
        print(build_controller_prompt(resources))
        return 0
    if args.print_self_audit_prompt:
        print(build_self_audit_prompt())
        return 0
    if args.print_experience_to_rule_prompt:
        print(build_experience_to_rule_prompt())
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
