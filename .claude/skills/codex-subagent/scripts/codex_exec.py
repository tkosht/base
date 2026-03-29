#!/usr/bin/env python3
"""
codex_exec.py - Codex exec サブエージェント実行ラッパー

実行モード:
- SINGLE: 単一実行
- PARALLEL: 並列実行（結果を結合）
- COMPETITION: 複数実行 → 評価 → 最良選択

使用例:
    # 単一実行
    python codex_exec.py --mode single --prompt "Hello World"

    # 並列実行（3並列）
    python codex_exec.py --mode parallel --prompt "タスク" --count 3

    # コンペモード
    python codex_exec.py --mode competition --prompt "コード生成" --count 3
        --task-type code_gen
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import hashlib
import json
import os
import random
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None

# ============================================================================
# Logging Configuration
# ============================================================================

ROOT_DIR = Path(__file__).resolve().parents[4]
LOG_ROOT_DIR = ROOT_DIR / ".codex" / "sessions" / "codex_exec"
DEFAULT_HUMAN_LOG_DIR = LOG_ROOT_DIR / "human"
DEFAULT_AUTO_LOG_DIR = LOG_ROOT_DIR / "auto"
SCHEMA_DIR = ROOT_DIR / ".claude" / "skills" / "codex-subagent" / "schemas"
FAST_PROFILES = {"fast", "very-fast"}
FAST_PROFILE_GUARDRAILS = """\
[注意] --profile fast/very-fast で実行中（推論強度が低い設定）。
- 推測で埋めない。根拠（ファイルパス等）を示せない内容は「不明」とする。
- タスクは極小化し、1つの結論に集中する（必要なら「分割して再実行」を提案）。
- 出力は短く、指定の形式に厳密に従う。
"""


def detect_default_log_scope() -> str:
    # Heuristic: if any stdio stream is a TTY, treat as "human".
    # Otherwise (non-interactive / captured output), treat as "auto".
    if sys.stdin.isatty() or sys.stdout.isatty() or sys.stderr.isatty():
        return "human"
    return "auto"


def resolve_log_dir(
    log_dir: str | None = None,
    log_scope: str | None = None,
) -> Path:
    env_dir = os.environ.get("CODEX_SUBAGENT_LOG_DIR")
    base_dir = (
        Path(log_dir)
        if log_dir
        else (Path(env_dir) if env_dir else LOG_ROOT_DIR)
    )

    scope = log_scope or os.environ.get("CODEX_SUBAGENT_LOG_SCOPE")

    # If the user already provided a scoped directory (e.g. ".../human"),
    # interpret it as the base dir's scope unless an explicit scope override exists.
    if base_dir.name in {"human", "auto"} and not scope:
        scope = base_dir.name
        base_dir = base_dir.parent

    scope = scope or detect_default_log_scope()
    candidate = base_dir / scope

    if candidate == LOG_ROOT_DIR / "human":
        candidate = DEFAULT_HUMAN_LOG_DIR
    elif candidate == LOG_ROOT_DIR / "auto":
        candidate = DEFAULT_AUTO_LOG_DIR
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    return candidate


LOG_DIR = resolve_log_dir()
MAX_OUTPUT_SIZE = 10 * 1024  # 10KB
MAX_CAPTURE_BYTES = 5 * 1024 * 1024  # 5MB (stdout/stderr capture cap)
CAPSULE_STORE_AUTO_THRESHOLD = 20_000  # bytes
SCHEMA_VERSION = "1.1"
PIPELINE_SPEC_VERSION = "2.0"
LLM_EVAL_SAMPLE_RATE = 0.2  # 20% sampling for LLM evaluation
EXIT_SUCCESS = 0
EXIT_SUBAGENT_FAILED = 2
EXIT_WRAPPER_ERROR = 3
STAGE_STATUS_VALUES = {"ok", "retryable_error", "fatal_error"}
PATCH_ALLOWED_OPS = {"add", "replace", "remove"}
PATCH_ALLOWED_PREFIXES = (
    "/facts",
    "/draft",
    "/critique",
    "/revise",
    "/open_questions",
    "/assumptions",
)
CAPSULE_HASH_EXCLUDE_KEYS = {"pipeline_run_id"}
DEFAULT_PIPELINE_STAGES = ("draft", "critique", "revise")
DEFAULT_MAX_PARALLEL_STAGES = 2
DEFAULT_RETRY_BACKOFF_SECONDS = (2, 5, 10)
STAGE_ROLE_VALUES = (
    "planner",
    "executor",
    "reviewer",
    "verifier",
    "releaser",
    "reducer",
)
DEFAULT_STAGE_ROLE_BY_ID = {
    "draft": "planner",
    "critique": "reviewer",
    "review": "reviewer",
    "verify": "verifier",
    "release": "releaser",
}
ROLE_DEFAULT_INPUT_KEYS = {
    "planner": [
        "task",
        "facts",
        "open_questions",
        "assumptions",
    ],
    "executor": [
        "task",
        "draft",
        "facts",
        "open_questions",
        "assumptions",
    ],
    "reviewer": [
        "draft",
        "facts",
        "revise",
        "open_questions",
        "assumptions",
    ],
    "verifier": [
        "draft",
        "critique",
        "revise",
        "facts",
        "open_questions",
    ],
    "releaser": [
        "draft",
        "revise",
        "facts",
        "open_questions",
    ],
    "reducer": [
        "facts",
        "draft",
        "critique",
        "revise",
        "open_questions",
        "assumptions",
    ],
}
ROLE_DEFAULT_MAX_ATTEMPTS = {
    "planner": 1,
    "executor": 2,
    "reviewer": 1,
    "verifier": 1,
    "releaser": 1,
    "reducer": 1,
}
ROLE_DEFAULT_WRITE_ROOTS = {
    "planner": [],
    "executor": None,
    "reviewer": [],
    "verifier": [],
    "releaser": [],
    "reducer": [],
}
PIPELINE_STAGE_TEMPLATES = {
    "draft": {},
    "critique": {},
    "revise": {},
}
WORKTREE_LOCK = threading.Lock()


class ExecutionMode(StrEnum):
    SINGLE = "single"
    PARALLEL = "parallel"
    COMPETITION = "competition"
    PIPELINE = "pipeline"


class SandboxMode(StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    FULL_ACCESS = "danger-full-access"


class TaskType(StrEnum):
    CODE_GEN = "code_gen"
    CODE_REVIEW = "code_review"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"


class SelectionStrategy(StrEnum):
    BEST_SINGLE = "best_single"
    VOTING = "voting"
    HYBRID = "hybrid"
    CONSERVATIVE = "conservative"


class JudgeMode(StrEnum):
    HEURISTIC = "heuristic"
    HYBRID = "hybrid"


class MergeStrategy(StrEnum):
    CONCAT = "concat"
    DEDUP = "dedup"
    PRIORITY = "priority"
    CONSENSUS = "consensus"


@dataclass
class CodexResult:
    """codex exec の実行結果"""

    agent_id: str
    output: str
    stderr: str = ""
    tokens_used: int = 0
    execution_time: float = 0.0
    success: bool = True
    error_message: str = ""
    returncode: int | None = None
    timed_out: bool = False
    timeout_seconds: int | None = None
    output_is_partial: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationScore:
    """評価スコア"""

    correctness: float = 0.0  # 40%
    completeness: float = 0.0  # 25%
    quality: float = 0.0  # 20%
    efficiency: float = 0.0  # 15%

    @property
    def total(self) -> float:
        return (
            self.correctness * 0.40
            + self.completeness * 0.25
            + self.quality * 0.20
            + self.efficiency * 0.15
        )


@dataclass
class EvaluatedResult:
    """評価済み結果"""

    result: CodexResult
    score: EvaluationScore
    task_score: float = 0.0
    combined_score: float = 0.0


@dataclass
class CompetitionOutcome:
    """コンペ実行結果（候補全件 + 最良選択）"""

    best: EvaluatedResult
    results: list[CodexResult]
    selection: dict[str, Any] = field(default_factory=dict)


@dataclass
class MergeConfig:
    """マージ設定"""

    min_votes: int = 2
    min_ratio: float = 0.6
    priority_weight: float = 1.0
    confidence_weight: float = 1.0


@dataclass
class StageExecutionPolicy:
    stage_id: str
    role: str
    sandbox: SandboxMode
    workdir: str | None
    write_roots: list[str]
    input_keys: list[str]
    max_attempts: int
    depends_on: list[str]
    merge_strategy: str | None


@dataclass
class IsolatedWorkspace:
    path: Path
    cleanup_root: Path
    mode: str


@dataclass(frozen=True)
class RepoSnapshotEntry:
    kind: str
    mode: int
    mtime_ns: int
    content: bytes | None = None
    link_target: str | None = None


# ============================================================================
# Logging Data Structures
# ============================================================================


@dataclass
class ExecutionLog:
    """実行ログ（JSONL形式で保存）"""

    schema_version: str = SCHEMA_VERSION
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    execution: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    evaluation: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def get_git_info() -> dict[str, str]:
    """Git情報を取得"""
    info = {}
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["git_branch"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["git_commit"] = result.stdout.strip()
    except Exception:
        pass
    return info


def write_log(log: ExecutionLog) -> Path | None:
    """ログをJSONL形式で書き込み"""
    try:
        now = datetime.now(UTC)
        log_dir = LOG_DIR / now.strftime("%Y/%m/%d")
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"run-{now.strftime('%Y%m%dT%H%M%S')}-{log.run_id[:8]}.jsonl"
        )
        log_path = log_dir / filename

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(log), ensure_ascii=False) + "\n")

        return log_path
    except Exception as e:
        print(f"Warning: Failed to write log: {e}", file=sys.stderr)
        return None


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    """出力をトランケート"""
    if len(output) <= max_size:
        return output
    return (
        output[:max_size] + f"\n... (truncated, original {len(output)} chars)"
    )


def _normalize_capsule(capsule: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(capsule)
    for key in CAPSULE_HASH_EXCLUDE_KEYS:
        normalized.pop(key, None)
    return normalized


def capsule_size_bytes(capsule: dict[str, Any]) -> int:
    payload = json.dumps(
        capsule, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return len(payload.encode("utf-8"))


def compute_capsule_hash(capsule: dict[str, Any]) -> str:
    normalized = _normalize_capsule(capsule)
    payload = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_capsule_store(
    mode: str,
    size_bytes: int,
    capsule_path: str | None,
    threshold: int = CAPSULE_STORE_AUTO_THRESHOLD,
) -> str:
    if mode not in {"embed", "file", "auto"}:
        raise ValueError("capsule_store must be embed|file|auto")
    if mode == "embed":
        if capsule_path:
            raise ValueError("capsule_path is not allowed with embed")
        return "embed"
    if mode == "file":
        return "file"
    # auto
    return "embed" if size_bytes <= threshold else "file"


def load_json_schema(schema_name: str) -> tuple[dict[str, Any], Path]:
    schema_path = SCHEMA_DIR / f"{schema_name}.schema.json"
    if not schema_path.exists():
        raise ValueError(f"{schema_name} schema not found")
    try:
        payload = schema_path.read_text(encoding="utf-8")
        schema = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{schema_name} schema is invalid") from exc
    if not isinstance(schema, dict):
        raise ValueError(f"{schema_name} schema must be an object")
    return schema, schema_path


def validate_json_schema(payload: Any, schema_name: str) -> None:
    if jsonschema is None:
        raise ValueError("jsonschema is not available")
    schema, schema_path = load_json_schema(schema_name)
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(payload), key=str)
    if errors:
        message = errors[0].message
        raise ValueError(f"{schema_name} schema invalid: {message}")


def load_pipeline_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    if not spec_path.exists():
        raise ValueError("pipeline_spec not found")
    try:
        raw = spec_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("pipeline_spec is invalid") from exc
    if not isinstance(data, dict):
        raise ValueError("pipeline_spec must be an object")
    validate_json_schema(data, "pipeline_spec")
    return data


def default_stage_role(stage_spec: dict[str, Any]) -> str:
    if stage_spec.get("role") in STAGE_ROLE_VALUES:
        return str(stage_spec["role"])
    if stage_spec.get("merge_strategy"):
        return "reducer"
    return DEFAULT_STAGE_ROLE_BY_ID.get(str(stage_spec.get("id")), "executor")


def normalize_repo_relative_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        raise ValueError("path must be relative to repo root")
    parts = [part for part in path.parts if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError("path must not escape repo root")
    if not parts:
        return "."
    return Path(*parts).as_posix()


def path_matches_roots(path_value: str, roots: list[str]) -> bool:
    normalized = normalize_repo_relative_path(path_value)
    for root in roots:
        candidate = normalize_repo_relative_path(root)
        if candidate == ".":
            return True
        if normalized == candidate or normalized.startswith(candidate + "/"):
            return True
    return False


def normalize_stage_spec(
    stage_spec: dict[str, Any],
    previous_stage_id: str | None,
) -> dict[str, Any]:
    stage_id = str(stage_spec["id"])
    role = default_stage_role(stage_spec)
    sandbox_value = stage_spec.get("sandbox", SandboxMode.READ_ONLY.value)
    sandbox = SandboxMode(str(sandbox_value))
    raw_roots = stage_spec.get("write_roots")
    write_roots_explicit = raw_roots is not None
    if raw_roots is None:
        default_roots = ROLE_DEFAULT_WRITE_ROOTS[role]
        write_roots = ["."] if default_roots is None else list(default_roots)
    else:
        write_roots = [
            normalize_repo_relative_path(root) for root in raw_roots
        ]
    input_keys = list(
        stage_spec.get("input_keys") or ROLE_DEFAULT_INPUT_KEYS[role]
    )
    max_attempts = int(
        stage_spec.get("max_attempts") or ROLE_DEFAULT_MAX_ATTEMPTS[role]
    )
    if max_attempts < 1:
        raise ValueError("stage max_attempts must be >= 1")
    if "depends_on" in stage_spec:
        depends_on = [str(item) for item in stage_spec.get("depends_on", [])]
    elif previous_stage_id:
        depends_on = [previous_stage_id]
    else:
        depends_on = []
    merge_strategy = stage_spec.get("merge_strategy")
    if merge_strategy is None and role == "reducer":
        merge_strategy = MergeStrategy.DEDUP.value
    if merge_strategy is not None:
        merge_strategy = MergeStrategy(str(merge_strategy)).value
    return {
        "id": stage_id,
        "role": role,
        "sandbox": sandbox.value,
        "workdir": stage_spec.get("workdir"),
        "write_roots": write_roots,
        "write_roots_explicit": write_roots_explicit,
        "input_keys": input_keys,
        "max_attempts": max_attempts,
        "depends_on": depends_on,
        "merge_strategy": merge_strategy,
        "prompt": stage_spec.get("prompt"),
        "instructions": stage_spec.get("instructions"),
    }


def canonicalize_pipeline_spec(
    pipeline_spec: dict[str, Any] | None,
    stages_arg: str | None = None,
) -> dict[str, Any]:
    stage_ids = resolve_pipeline_stage_ids(stages_arg, pipeline_spec)
    if pipeline_spec is None:
        raw_spec = {
            "stages": [{"id": stage_id} for stage_id in stage_ids],
            "allow_dynamic_stages": False,
        }
        source_schema = "legacy"
    else:
        raw_spec = dict(pipeline_spec)
        source_schema = str(pipeline_spec.get("schema_version") or "legacy")

    raw_stages = raw_spec.get("stages", [])
    explicit_dependency = any(
        isinstance(stage, dict) and "depends_on" in stage
        for stage in raw_stages
    )
    stages: list[dict[str, Any]] = []
    previous_stage_id: str | None = None
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, dict):
            raise ValueError("pipeline_spec stage must be an object")
        normalized = normalize_stage_spec(raw_stage, previous_stage_id)
        stages.append(normalized)
        previous_stage_id = normalized["id"]

    canonical = {
        "schema_version": PIPELINE_SPEC_VERSION,
        "source_schema_version": source_schema,
        "allow_dynamic_stages": bool(
            raw_spec.get("allow_dynamic_stages", False)
        ),
        "allowed_stage_ids": list(raw_spec.get("allowed_stage_ids") or []),
        "max_total_prompt_chars": raw_spec.get("max_total_prompt_chars"),
        "stages": stages,
        "is_legacy": source_schema != PIPELINE_SPEC_VERSION,
        "uses_graph": explicit_dependency
        or any(stage.get("role") == "reducer" for stage in stages),
    }
    if not canonical["allowed_stage_ids"]:
        canonical["allowed_stage_ids"] = [stage["id"] for stage in stages]
    validate_canonical_pipeline_spec(canonical)
    return canonical


def validate_canonical_pipeline_spec(canonical_spec: dict[str, Any]) -> None:
    stage_ids = [stage["id"] for stage in canonical_spec["stages"]]
    if len(stage_ids) != len(set(stage_ids)):
        raise ValueError("pipeline_spec stage ids must be unique")
    known_stage_ids = set(stage_ids)
    if canonical_spec.get("allow_dynamic_stages") and canonical_spec.get(
        "uses_graph"
    ):
        raise ValueError(
            "depends_on and dynamic next_stages cannot be combined"
        )
    for stage in canonical_spec["stages"]:
        for dependency in stage.get("depends_on", []):
            if dependency not in known_stage_ids:
                raise ValueError("pipeline_spec dependency is unknown")
            if dependency == stage["id"]:
                raise ValueError("pipeline_spec self dependency is invalid")
        if (
            canonical_spec.get("uses_graph")
            and stage.get("write_roots")
            and not stage.get("write_roots_explicit", False)
        ):
            raise ValueError(
                "graph writer stages must declare write_roots explicitly"
            )
    try:
        build_stage_layers(canonical_spec["stages"])
    except ValueError as exc:
        raise ValueError(f"pipeline_spec is invalid: {exc}") from exc


def build_stage_layers(stages: list[dict[str, Any]]) -> list[list[str]]:
    stage_map = {stage["id"]: stage for stage in stages}
    remaining = {
        stage_id: set(stage["depends_on"])
        for stage_id, stage in stage_map.items()
    }
    completed: set[str] = set()
    layers: list[list[str]] = []
    while remaining:
        ready = sorted(
            stage_id
            for stage_id, deps in remaining.items()
            if deps.issubset(completed)
        )
        if not ready:
            raise ValueError("pipeline graph has a cycle")
        layers.append(ready)
        completed.update(ready)
        for stage_id in ready:
            remaining.pop(stage_id, None)
    return layers


def build_stage_policy(stage_spec: dict[str, Any]) -> StageExecutionPolicy:
    return StageExecutionPolicy(
        stage_id=stage_spec["id"],
        role=stage_spec["role"],
        sandbox=SandboxMode(stage_spec["sandbox"]),
        workdir=stage_spec.get("workdir"),
        write_roots=list(stage_spec.get("write_roots") or []),
        input_keys=list(stage_spec.get("input_keys") or []),
        max_attempts=int(stage_spec.get("max_attempts") or 1),
        depends_on=list(stage_spec.get("depends_on") or []),
        merge_strategy=stage_spec.get("merge_strategy"),
    )


def compute_retry_backoff_seconds(attempt_index: int) -> int:
    backoffs = DEFAULT_RETRY_BACKOFF_SECONDS
    if attempt_index < 1:
        return backoffs[0]
    return backoffs[min(attempt_index - 1, len(backoffs) - 1)]


def list_repo_state_paths(root: str | Path = ROOT_DIR) -> list[str]:
    root_path = Path(root)
    try:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=root_path,
            capture_output=True,
            check=True,
        )
    except Exception:
        paths: list[str] = []
        for path in sorted(root_path.rglob("*")):
            if ".git" in path.parts or not (
                path.is_file() or path.is_symlink()
            ):
                continue
            paths.append(path.relative_to(root_path).as_posix())
        return paths
    raw = result.stdout.decode("utf-8", errors="replace")
    return [entry for entry in raw.split("\0") if entry]


def read_repo_snapshot_entry(path: str | Path) -> RepoSnapshotEntry | None:
    entry_path = Path(path)
    if not entry_path.exists() and not entry_path.is_symlink():
        return None
    stat_result = entry_path.lstat()
    mode = stat.S_IMODE(stat_result.st_mode)
    mtime_ns = stat_result.st_mtime_ns
    if entry_path.is_symlink():
        return RepoSnapshotEntry(
            kind="symlink",
            mode=mode,
            mtime_ns=mtime_ns,
            link_target=os.readlink(entry_path),
        )
    if entry_path.is_file():
        return RepoSnapshotEntry(
            kind="file",
            mode=mode,
            mtime_ns=mtime_ns,
            content=entry_path.read_bytes(),
        )
    return None


def capture_repo_snapshot(
    root: str | Path = ROOT_DIR,
) -> dict[str, RepoSnapshotEntry]:
    root_path = Path(root)
    snapshot: dict[str, RepoSnapshotEntry] = {}
    for rel_path in list_repo_state_paths(root_path):
        entry = read_repo_snapshot_entry(root_path / rel_path)
        if entry is not None:
            snapshot[rel_path] = entry
    return snapshot


def diff_repo_snapshot(
    before_snapshot: dict[str, RepoSnapshotEntry],
    after_snapshot: dict[str, RepoSnapshotEntry],
) -> list[str]:
    changed: list[str] = []
    for rel_path in sorted(set(before_snapshot) | set(after_snapshot)):
        if before_snapshot.get(rel_path) != after_snapshot.get(rel_path):
            changed.append(rel_path)
    return changed


def restore_repo_paths(
    before_snapshot: dict[str, RepoSnapshotEntry],
    after_snapshot: dict[str, RepoSnapshotEntry],
    target_paths: list[str],
    root: str | Path = ROOT_DIR,
) -> None:
    del after_snapshot
    root_path = Path(root)
    for rel_path in target_paths:
        before_bytes = before_snapshot.get(rel_path)
        abs_path = root_path / rel_path
        if before_bytes is None:
            remove_repo_path(abs_path, root_path)
            continue
        write_repo_snapshot_entry(abs_path, before_bytes)


def remove_repo_path(path: str | Path, root: str | Path) -> None:
    abs_path = Path(path)
    root_path = Path(root)
    if not abs_path.exists() and not abs_path.is_symlink():
        return
    if abs_path.is_symlink() or abs_path.is_file():
        abs_path.unlink()
    elif abs_path.is_dir():
        shutil.rmtree(abs_path)
    parent = abs_path.parent
    while parent != root_path and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def write_repo_snapshot_entry(
    destination: str | Path,
    entry: RepoSnapshotEntry,
) -> None:
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() or dest_path.is_symlink():
        remove_repo_path(dest_path, dest_path.parent)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    if entry.kind == "symlink":
        if entry.link_target is None:
            raise ValueError("symlink snapshot entry requires link_target")
        os.symlink(entry.link_target, dest_path)
        try:
            os.utime(
                dest_path,
                ns=(entry.mtime_ns, entry.mtime_ns),
                follow_symlinks=False,
            )
        except (NotImplementedError, OSError):
            pass
        return
    if entry.kind != "file":
        raise ValueError("unsupported snapshot entry kind")
    if entry.content is None:
        raise ValueError("file snapshot entry requires content")
    dest_path.write_bytes(entry.content)
    os.chmod(dest_path, entry.mode)
    os.utime(dest_path, ns=(entry.mtime_ns, entry.mtime_ns))


def enforce_stage_write_policy(
    policy: StageExecutionPolicy,
    before_snapshot: dict[str, RepoSnapshotEntry],
    *,
    workspace_root: str | Path = ROOT_DIR,
    after_snapshot: dict[str, RepoSnapshotEntry] | None = None,
    restore_unauthorized: bool = True,
) -> dict[str, Any]:
    root_path = Path(workspace_root)
    effective_after_snapshot = (
        after_snapshot
        if after_snapshot is not None
        else capture_repo_snapshot(root_path)
    )
    changed_files = diff_repo_snapshot(
        before_snapshot, effective_after_snapshot
    )
    unauthorized_files = [
        path
        for path in changed_files
        if not path_matches_roots(path, policy.write_roots)
    ]
    if unauthorized_files and restore_unauthorized:
        restore_repo_paths(
            before_snapshot,
            effective_after_snapshot,
            unauthorized_files,
            root=root_path,
        )
    return {
        "changed_files": changed_files,
        "unauthorized_files": unauthorized_files,
        "authorized": not unauthorized_files,
    }


def build_repo_change_set(
    after_snapshot: dict[str, RepoSnapshotEntry],
    changed_files: list[str],
) -> dict[str, RepoSnapshotEntry | None]:
    return {path: after_snapshot.get(path) for path in changed_files}


def apply_repo_changes(
    changes: dict[str, RepoSnapshotEntry | None],
    root: str | Path = ROOT_DIR,
) -> None:
    root_path = Path(root)
    for rel_path in sorted(changes):
        payload = changes[rel_path]
        abs_path = root_path / rel_path
        if payload is None:
            remove_repo_path(abs_path, root_path)
            continue
        write_repo_snapshot_entry(abs_path, payload)


def copy_path_preserving_metadata(
    source_path: str | Path,
    destination_path: str | Path,
) -> None:
    source = Path(source_path)
    destination = Path(destination_path)
    entry = read_repo_snapshot_entry(source)
    if entry is None:
        raise ValueError("source path does not exist for promotion")
    write_repo_snapshot_entry(destination, entry)


def sync_repo_state(
    source_root: str | Path,
    target_root: str | Path,
) -> None:
    source_path = Path(source_root)
    target_path = Path(target_root)
    source_paths = set(list_repo_state_paths(source_path))
    target_paths = set(list_repo_state_paths(target_path))
    for rel_path in sorted(target_paths - source_paths):
        dest_path = target_path / rel_path
        remove_repo_path(dest_path, target_path)
    for rel_path in sorted(source_paths):
        source_file = source_path / rel_path
        target_file = target_path / rel_path
        if not (source_file.is_file() or source_file.is_symlink()):
            if target_file.exists():
                remove_repo_path(target_file, target_path)
            continue
        copy_path_preserving_metadata(source_file, target_file)


def create_isolated_workspace(
    source_root: str | Path,
    stage_label: str,
) -> IsolatedWorkspace:
    source_path = Path(source_root)
    cleanup_root = Path(
        tempfile.mkdtemp(
            prefix=f"codex-stage-{re.sub(r'[^A-Za-z0-9._-]+', '-', stage_label)}-"
        )
    )
    workspace_path = cleanup_root / "workspace"
    worktree_created = False
    try:
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=source_path,
                capture_output=True,
                check=True,
            )
        except Exception:
            workspace_path.mkdir(parents=True, exist_ok=True)
            sync_repo_state(source_path, workspace_path)
            return IsolatedWorkspace(
                path=workspace_path,
                cleanup_root=cleanup_root,
                mode="copy",
            )

        with WORKTREE_LOCK:
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "--detach",
                    str(workspace_path),
                    "HEAD",
                ],
                cwd=source_path,
                capture_output=True,
                check=True,
            )
            worktree_created = True
        sync_repo_state(source_path, workspace_path)
        return IsolatedWorkspace(
            path=workspace_path,
            cleanup_root=cleanup_root,
            mode="worktree",
        )
    except Exception:
        if worktree_created:
            with WORKTREE_LOCK:
                subprocess.run(
                    [
                        "git",
                        "worktree",
                        "remove",
                        "--force",
                        str(workspace_path),
                    ],
                    cwd=source_path,
                    capture_output=True,
                    check=False,
                )
        shutil.rmtree(cleanup_root, ignore_errors=True)
        raise


def cleanup_isolated_workspace(workspace: IsolatedWorkspace) -> None:
    if workspace.mode == "worktree":
        with WORKTREE_LOCK:
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "remove",
                    "--force",
                    str(workspace.path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                check=False,
            )
    shutil.rmtree(workspace.cleanup_root, ignore_errors=True)


def resolve_workspace_workdir(
    workdir: str | None,
    workspace_root: str | Path,
) -> str:
    workspace_path = Path(workspace_root)
    if workdir is None:
        return str(workspace_path)
    candidate = Path(workdir)
    if not candidate.is_absolute():
        relative = normalize_repo_relative_path(candidate.as_posix())
        return str(workspace_path / relative)
    try:
        relative = candidate.relative_to(ROOT_DIR)
    except ValueError:
        raise ValueError("workdir must stay within repo root") from None
    normalized = normalize_repo_relative_path(relative.as_posix())
    return str(workspace_path / normalized)


def detect_conflicting_stage_changes(
    stage_outcomes: list[dict[str, Any]],
) -> list[str]:
    changed_by_path: dict[str, str] = {}
    conflicts: set[str] = set()
    for outcome in stage_outcomes:
        for rel_path in outcome.get("promotable_files", []):
            previous_stage = changed_by_path.get(rel_path)
            if previous_stage and previous_stage != outcome["policy"].stage_id:
                conflicts.add(rel_path)
            else:
                changed_by_path[rel_path] = outcome["policy"].stage_id
    return sorted(conflicts)


def cleanup_stage_workspace(outcome: dict[str, Any]) -> None:
    workspace = outcome.get("workspace")
    if workspace is None or outcome.get("workspace_cleaned"):
        return
    cleanup_isolated_workspace(workspace)
    outcome["workspace_cleaned"] = True


def promote_stage_workspace(
    outcome: dict[str, Any],
    root: str | Path = ROOT_DIR,
) -> None:
    workspace = outcome.get("workspace")
    if workspace is None:
        return
    snapshot = capture_repo_snapshot(workspace.path)
    changes = build_repo_change_set(
        snapshot,
        list(outcome.get("promotable_files") or []),
    )
    apply_repo_changes(changes, root=root)
    cleanup_stage_workspace(outcome)


def select_capsule_inputs(
    capsule: dict[str, Any],
    input_keys: list[str],
) -> dict[str, Any]:
    selected = {
        "schema_version": capsule.get("schema_version"),
        "pipeline_run_id": capsule.get("pipeline_run_id"),
    }
    for key in input_keys:
        if key in capsule:
            selected[key] = json.loads(json.dumps(capsule[key]))
    return selected


def get_pipeline_artifact_dir(
    log_dir: str | Path,
    pipeline_run_id: str,
) -> Path:
    return Path(log_dir) / "artifacts" / pipeline_run_id


def get_pipeline_state_path(
    log_dir: str | Path,
    pipeline_run_id: str,
) -> Path:
    return get_pipeline_artifact_dir(log_dir, pipeline_run_id) / "state.json"


def write_pipeline_state(path: str | Path, payload: dict[str, Any]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_pipeline_state(path: str | Path) -> dict[str, Any]:
    state_path = Path(path)
    if state_path.is_dir():
        state_path = state_path / "state.json"
    if not state_path.exists():
        raise ValueError("resume state not found")
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("resume state is invalid") from exc


def resolve_resume_state_path(
    resume_run: str,
    effective_log_dir: str | Path | None = None,
) -> Path:
    candidate = Path(resume_run)
    if candidate.exists():
        return candidate if candidate.is_file() else candidate / "state.json"

    search_roots: list[Path] = []
    if effective_log_dir is not None:
        search_roots.append(Path(effective_log_dir))
    search_roots.extend([DEFAULT_HUMAN_LOG_DIR, DEFAULT_AUTO_LOG_DIR])
    for root in search_roots:
        state_path = root / "artifacts" / resume_run / "state.json"
        if state_path.exists():
            return state_path
    raise ValueError("resume state not found")


def resolve_capsule_path(
    store_mode: str,
    capsule_path: str | None,
    log_dir: str | Path,
    pipeline_run_id: str,
) -> Path | None:
    if store_mode not in {"embed", "file"}:
        raise ValueError("capsule_store must be embed|file")
    if store_mode == "embed":
        if capsule_path:
            raise ValueError("capsule_path is not allowed with embed")
        return None
    if capsule_path:
        return Path(capsule_path)
    return Path(log_dir) / "artifacts" / pipeline_run_id / "capsule.json"


def serialize_capsule(capsule: dict[str, Any]) -> str:
    return json.dumps(
        capsule,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        indent=2,
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    idx = 0
    while True:
        start = text.find("{", idx)
        if start == -1:
            break
        try:
            obj, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            idx = start + 1
            continue
        if isinstance(obj, dict):
            return obj
        idx = start + 1
    raise ValueError("stage_result json not found")


def parse_stage_result_output(
    output: str,
    allow_dynamic: bool,
) -> dict[str, Any]:
    if not output:
        raise ValueError("stage_result output is empty")
    payload = _extract_json_object(output)
    if not isinstance(payload, dict):
        raise ValueError("stage_result must be an object")
    validate_json_schema(payload, "stage_result")
    validate_stage_result(payload, allow_dynamic=allow_dynamic)
    return payload


def build_stage_prompt(
    stage_id: str,
    base_prompt: str,
    capsule: dict[str, Any],
    capsule_store: str,
    capsule_path: str | Path | None,
    stage_spec: dict[str, Any] | None,
    allow_dynamic: bool,
    stage_policy: StageExecutionPolicy | None = None,
) -> str:
    if capsule_store not in {"embed", "file"}:
        raise ValueError("capsule_store must be embed|file")
    if capsule_store == "file" and not capsule_path:
        raise ValueError("capsule_path is required for file store")

    stage_hint = ""
    if stage_spec:
        hint = stage_spec.get("prompt") or stage_spec.get("instructions")
        if isinstance(hint, str) and hint:
            stage_hint = f"\nStage Instructions:\n{hint}\n"

    policy_lines: list[str] = []
    if stage_policy:
        policy_lines.append(f"- Role: {stage_policy.role}")
        policy_lines.append(f"- Sandbox: {stage_policy.sandbox.value}")
        if stage_policy.workdir:
            policy_lines.append(f"- Workdir: {stage_policy.workdir}")
        policy_lines.append(
            "- Allowed repo write roots: "
            + (
                ", ".join(stage_policy.write_roots)
                if stage_policy.write_roots
                else "(none)"
            )
        )
        policy_lines.append(
            "- Capsule input keys: "
            + (
                ", ".join(stage_policy.input_keys)
                if stage_policy.input_keys
                else "(none)"
            )
        )
    policy_block = ""
    if policy_lines:
        policy_block = "Stage Policy:\n" + "\n".join(policy_lines) + "\n\n"

    if capsule_store == "embed":
        capsule_block = f"CAPSULE_JSON:\n{serialize_capsule(capsule)}"
    else:
        capsule_block = f"CAPSULE_PATH: {capsule_path}"

    allowed_paths = ", ".join(PATCH_ALLOWED_PREFIXES)
    template_lines = [
        "{",
        f'  "schema_version": "{SCHEMA_VERSION}",',
        f'  "stage_id": "{stage_id}",',
        '  "status": "ok|retryable_error|fatal_error",',
        '  "output_is_partial": false,',
        '  "capsule_patch": [],',
    ]
    if allow_dynamic:
        template_lines.append('  "next_stages": []')
    else:
        template_lines[-1] = template_lines[-1].rstrip(",")
    template_lines.append("}")
    template = "\n".join(template_lines)

    dynamic_note = ""
    if allow_dynamic:
        dynamic_note = (
            "- You may include next_stages only when you need to add stages.\n"
        )

    return (
        f"You are executing pipeline stage: {stage_id}.\n"
        f"Task:\n{base_prompt}\n\n"
        f"{stage_hint}"
        f"{policy_block}"
        f"{capsule_block}\n\n"
        "Return JSON ONLY with this shape:\n"
        f"{template}\n\n"
        "Rules:\n"
        "- JSON Patch ops: add, replace, remove.\n"
        f"- Allowed patch paths: {allowed_paths} (prefix allowed).\n"
        "- If status != ok or output_is_partial is true, capsule_patch must be [].\n"
        f"{dynamic_note}"
    )


def prepare_stage_prompt(
    stage_id: str,
    base_prompt: str,
    capsule: dict[str, Any],
    capsule_store: str,
    capsule_path: str | Path | None,
    stage_spec: dict[str, Any] | None,
    max_total_prompt_chars: int | None,
    allow_dynamic: bool,
    stage_policy: StageExecutionPolicy | None = None,
) -> str:
    prompt = build_stage_prompt(
        stage_id=stage_id,
        base_prompt=base_prompt,
        capsule=capsule,
        capsule_store=capsule_store,
        capsule_path=capsule_path,
        stage_spec=stage_spec,
        stage_policy=stage_policy,
        allow_dynamic=allow_dynamic,
    )
    ensure_prompt_limit(prompt, max_total_prompt_chars)
    return prompt


def stage_result_from_exec_failure(
    stage_id: str,
    result: CodexResult,
) -> dict[str, Any]:
    if result.success:
        raise ValueError("exec result must be failure")
    status = "retryable_error" if result.timed_out else "fatal_error"
    output_is_partial = bool(result.output_is_partial or result.timed_out)
    return {
        "schema_version": SCHEMA_VERSION,
        "stage_id": stage_id,
        "status": status,
        "output_is_partial": output_is_partial,
        "capsule_patch": [],
        "summary": "codex exec failed",
    }


def build_stage_log(
    stage_id: str,
    pipeline_run_id: str,
    capsule_state: dict[str, Any],
    store_mode: str,
    capsule_path: str | Path | None,
    size_bytes: int,
    exec_result: CodexResult,
    stage_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "pipeline_run_id": pipeline_run_id,
        "capsule_store": store_mode,
        "capsule_path": str(capsule_path) if capsule_path else None,
        "capsule_size_bytes": size_bytes,
        "capsule_hash": compute_capsule_hash(capsule_state),
        "exec": {
            "agent_id": exec_result.agent_id,
            "model": exec_result.metadata.get("model"),
            "output": truncate_output(exec_result.output),
            "stderr": truncate_output(exec_result.stderr),
            "tokens_used": exec_result.tokens_used,
            "execution_time": exec_result.execution_time,
            "success": exec_result.success,
            "returncode": exec_result.returncode,
            "timed_out": exec_result.timed_out,
            "timeout_seconds": exec_result.timeout_seconds,
            "output_is_partial": exec_result.output_is_partial,
            "error_message": exec_result.error_message,
        },
        "stage_result": stage_result,
    }


def determine_pipeline_exit_code(
    success: bool,
    wrapper_error: bool,
) -> int:
    if wrapper_error:
        return EXIT_WRAPPER_ERROR
    return EXIT_SUCCESS if success else EXIT_SUBAGENT_FAILED


def ensure_prompt_limit(
    prompt: str, max_total_prompt_chars: int | None
) -> None:
    if max_total_prompt_chars is None:
        return
    if max_total_prompt_chars <= 0:
        raise ValueError("max_total_prompt_chars must be positive")
    if len(prompt) > max_total_prompt_chars:
        raise ValueError("prompt exceeds max_total_prompt_chars")


def build_pipeline_output_payload(
    pipeline_run_id: str,
    success: bool,
    stage_results: list[dict[str, Any]],
    final_capsule: dict[str, Any],
    capsule_store: str,
    capsule_path: str | Path | None,
    evaluation: dict[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    return {
        "pipeline_run_id": pipeline_run_id,
        "model": model,
        "success": success,
        "stage_results": stage_results,
        "capsule": final_capsule,
        "capsule_hash": compute_capsule_hash(final_capsule),
        "capsule_store": capsule_store,
        "capsule_path": str(capsule_path) if capsule_path else None,
        "evaluation": evaluation,
    }


def build_initial_capsule(
    prompt: str,
    pipeline_run_id: str,
    sandbox: SandboxMode,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": pipeline_run_id,
        "task": {
            "goal": prompt,
            "constraints": [str(sandbox)],
            "inputs": [],
        },
        "facts": [],
        "open_questions": [],
        "assumptions": [],
        "draft": {},
        "critique": {},
        "revise": {},
    }


def validate_capsule_payload(capsule: dict[str, Any]) -> None:
    validate_json_schema(capsule, "capsule")


def evaluate_retry_policy_from_logs(
    stage_specs: list[dict[str, Any]],
    stage_logs: list[dict[str, Any]],
) -> bool:
    logs_by_stage: dict[str, list[dict[str, Any]]] = {}
    max_attempts_by_stage = {
        stage["id"]: int(stage.get("max_attempts") or 1)
        for stage in stage_specs
    }
    for log in stage_logs:
        stage_id = log.get("stage_id")
        if not isinstance(stage_id, str) or not stage_id:
            return False
        logs_by_stage.setdefault(stage_id, []).append(log)

    for stage_id, logs in logs_by_stage.items():
        attempts: list[int] = []
        for log in logs:
            attempt_value = log.get("attempt")
            if not isinstance(attempt_value, int) or attempt_value < 1:
                return False
            attempts.append(attempt_value)
        if attempts != list(range(1, len(attempts) + 1)):
            return False
        max_attempts = max_attempts_by_stage.get(stage_id)
        if max_attempts is None or len(attempts) > max_attempts:
            return False
        for index, log in enumerate(logs[:-1]):
            stage_result = log.get("stage_result") or {}
            status = stage_result.get("status")
            retry_scheduled = bool(log.get("retry_scheduled"))
            if retry_scheduled and status != "retryable_error":
                return False
            if status == "retryable_error" and not retry_scheduled:
                return False
            if retry_scheduled and attempts[index + 1] != attempts[index] + 1:
                return False
        last_log = logs[-1]
        if last_log.get("retry_scheduled"):
            return False
        last_status = (last_log.get("stage_result") or {}).get("status")
        if last_status == "retryable_error" and len(attempts) != max_attempts:
            return False
    return True


def build_pipeline_evaluation(
    stage_specs: list[dict[str, Any]],
    stage_results: list[dict[str, Any]],
    stage_logs: list[dict[str, Any]],
    final_capsule: dict[str, Any],
    unauthorized_write_detected: bool,
    used_graph: bool,
    allow_dynamic: bool = False,
) -> dict[str, Any]:
    stage_contract_valid = True
    for result in stage_results:
        try:
            validate_stage_result(result, allow_dynamic=allow_dynamic)
        except ValueError:
            stage_contract_valid = False
            break
    try:
        validate_capsule_payload(final_capsule)
        capsule_schema_valid = True
    except ValueError:
        capsule_schema_valid = False
    completed_stage_ids = {result.get("stage_id") for result in stage_results}
    expected_stage_ids = {stage["id"] for stage in stage_specs}
    declared_success_stages_complete = expected_stage_ids.issubset(
        completed_stage_ids
    )
    handoff_order_valid = True
    if used_graph:
        completed_in_order = [
            result.get("stage_id") for result in stage_results
        ]
        completed_index = {
            stage_id: index
            for index, stage_id in enumerate(completed_in_order)
        }
        for stage in stage_specs:
            stage_index = completed_index.get(stage["id"])
            if stage_index is None:
                handoff_order_valid = False
                break
            for dependency in stage.get("depends_on", []):
                dep_index = completed_index.get(dependency)
                if dep_index is None or dep_index > stage_index:
                    handoff_order_valid = False
                    break
            if not handoff_order_valid:
                break
    evaluation = {
        "capsule_schema_valid": capsule_schema_valid,
        "stage_contract_valid": stage_contract_valid,
        "unauthorized_writes_detected": unauthorized_write_detected,
        "retry_policy_followed": evaluate_retry_policy_from_logs(
            stage_specs, stage_logs
        ),
        "handoff_order_valid": handoff_order_valid,
        "declared_success_stages_complete": declared_success_stages_complete,
    }
    evaluation["passed"] = all(
        [
            evaluation["capsule_schema_valid"],
            evaluation["stage_contract_valid"],
            not evaluation["unauthorized_writes_detected"],
            evaluation["retry_policy_followed"],
            evaluation["handoff_order_valid"],
            evaluation["declared_success_stages_complete"],
        ]
    )
    return evaluation


def write_capsule_file(path: str | Path, capsule: dict[str, Any]) -> None:
    capsule_path = Path(path)
    capsule_path.parent.mkdir(parents=True, exist_ok=True)
    capsule_path.write_text(serialize_capsule(capsule), encoding="utf-8")


def resolve_capsule_delivery(
    store_mode_arg: str,
    capsule: dict[str, Any],
    capsule_path_arg: str | None,
    log_dir: str | Path,
    pipeline_run_id: str,
) -> tuple[str, Path | None, int]:
    size_bytes = capsule_size_bytes(capsule)
    store_mode = resolve_capsule_store(
        store_mode_arg, size_bytes, capsule_path_arg
    )
    if store_mode == "file":
        capsule_path = resolve_capsule_path(
            "file", capsule_path_arg, log_dir, pipeline_run_id
        )
    else:
        capsule_path = None
        if store_mode_arg == "embed":
            resolve_capsule_path(
                "embed", capsule_path_arg, log_dir, pipeline_run_id
            )
    return store_mode, capsule_path, size_bytes


def find_stage_spec(
    pipeline_spec: dict[str, Any] | None,
    stage_id: str,
    dynamic_stage_specs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if pipeline_spec:
        stages = pipeline_spec.get("stages", [])
        if isinstance(stages, list):
            for spec in stages:
                if isinstance(spec, dict) and spec.get("id") == stage_id:
                    return spec
    if dynamic_stage_specs and stage_id in dynamic_stage_specs:
        return dynamic_stage_specs[stage_id]
    return None


def _is_allowed_patch_path(path: str) -> bool:
    if not path.startswith("/"):
        return False
    for prefix in PATCH_ALLOWED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def validate_patch_ops(ops: list[dict[str, Any]]) -> None:
    if not isinstance(ops, list):
        raise ValueError("capsule_patch must be an array")
    for op in ops:
        if not isinstance(op, dict):
            raise ValueError("capsule_patch elements must be objects")
        op_name = op.get("op")
        path = op.get("path")
        if op_name not in PATCH_ALLOWED_OPS:
            raise ValueError("capsule_patch op is not allowed")
        if not isinstance(path, str) or not _is_allowed_patch_path(path):
            raise ValueError("capsule_patch path is not allowed")
        if op_name == "remove" and path in PATCH_ALLOWED_PREFIXES:
            raise ValueError(
                "capsule_patch must not remove top-level capsule keys"
            )


def validate_stage_result(
    result: dict[str, Any],
    allow_dynamic: bool,
) -> None:
    required = {"schema_version", "stage_id", "status", "output_is_partial"}
    missing = required - set(result.keys())
    if missing:
        raise ValueError("stage_result missing required fields")
    if result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("stage_result schema_version is invalid")
    status = result.get("status")
    output_is_partial = result.get("output_is_partial")
    capsule_patch = result.get("capsule_patch")
    if status not in STAGE_STATUS_VALUES:
        raise ValueError("stage_result status is invalid")
    if not isinstance(output_is_partial, bool):
        raise ValueError("stage_result output_is_partial must be boolean")
    if capsule_patch is None:
        raise ValueError("capsule_patch is required")
    if not isinstance(capsule_patch, list):
        raise ValueError("capsule_patch must be an array")
    if output_is_partial:
        if status == "ok":
            raise ValueError("output_is_partial requires error status")
        if capsule_patch:
            raise ValueError("capsule_patch must be empty on partial output")
    if status != "ok":
        if capsule_patch:
            raise ValueError("capsule_patch must be empty on error status")
    if status == "ok" and output_is_partial:
        raise ValueError("status ok requires output_is_partial=false")
    if status == "ok":
        validate_patch_ops(capsule_patch)
    if "next_stages" in result and not allow_dynamic:
        raise ValueError("next_stages is not allowed without dynamic stages")
    if allow_dynamic and result.get("next_stages"):
        next_stages = result["next_stages"]
        if not isinstance(next_stages, list):
            raise ValueError("next_stages must be a list")
        if len(next_stages) > 1:
            raise ValueError("next_stages allows at most one stage per result")


def resolve_pipeline_stage_ids(
    stages_arg: str | None,
    pipeline_spec: dict[str, Any] | None,
    default_ids: tuple[str, ...] = DEFAULT_PIPELINE_STAGES,
) -> list[str]:
    if pipeline_spec and stages_arg:
        raise ValueError("pipeline_spec and pipeline_stages are exclusive")
    if pipeline_spec is not None:
        stages = pipeline_spec.get("stages")
        if not isinstance(stages, list) or not stages:
            raise ValueError("pipeline_spec stages must be a non-empty list")
        stage_ids = []
        for stage in stages:
            if not isinstance(stage, dict) or "id" not in stage:
                raise ValueError("pipeline_spec stage id is required")
            stage_id = stage["id"]
            if not isinstance(stage_id, str) or not stage_id:
                raise ValueError("pipeline_spec stage id is invalid")
            stage_ids.append(stage_id)
        return stage_ids
    if stages_arg:
        stage_ids = [s.strip() for s in stages_arg.split(",") if s.strip()]
        if not stage_ids:
            raise ValueError("pipeline_stages is empty")
        for stage_id in stage_ids:
            if stage_id not in PIPELINE_STAGE_TEMPLATES:
                raise ValueError("unknown stage id in pipeline_stages")
        return stage_ids
    return list(default_ids)


def _decode_pointer_segment(segment: str) -> str:
    return segment.replace("~1", "/").replace("~0", "~")


def _parse_json_pointer(path: str) -> list[str]:
    if path == "":
        return []
    if not path.startswith("/"):
        raise ValueError("json pointer must start with '/'")
    parts = path.split("/")[1:]
    return [_decode_pointer_segment(p) for p in parts]


def _resolve_parent(container: Any, pointer: list[str]) -> tuple[Any, str]:
    if not pointer:
        raise ValueError("json pointer cannot be empty")
    current = container
    for segment in pointer[:-1]:
        if isinstance(current, list):
            if segment == "-":
                raise ValueError("json pointer '-' is not valid in middle")
            try:
                index = int(segment)
            except ValueError as exc:
                raise ValueError("json pointer index is invalid") from exc
            if index < 0 or index >= len(current):
                raise ValueError("json pointer index out of range")
            current = current[index]
            continue
        if isinstance(current, dict):
            if segment not in current:
                raise ValueError("json pointer path not found")
            current = current[segment]
            continue
        raise ValueError("json pointer path not found")
    return current, pointer[-1]


def apply_capsule_patch(
    capsule: dict[str, Any],
    ops: list[dict[str, Any]],
) -> dict[str, Any]:
    validate_patch_ops(ops)
    updated = json.loads(json.dumps(capsule))
    for op in ops:
        op_name = op["op"]
        path = op["path"]
        value = op.get("value")
        pointer = _parse_json_pointer(path)
        parent, key = _resolve_parent(updated, pointer)
        if op_name == "add":
            if isinstance(parent, list):
                if key == "-":
                    parent.append(value)
                else:
                    try:
                        index = int(key)
                    except ValueError as exc:
                        raise ValueError(
                            "json patch index is invalid"
                        ) from exc
                    if index < 0 or index > len(parent):
                        raise ValueError("json patch index out of range")
                    parent.insert(index, value)
            elif isinstance(parent, dict):
                parent[key] = value
            else:
                raise ValueError("json patch target is invalid")
        elif op_name == "replace":
            if isinstance(parent, list):
                try:
                    index = int(key)
                except ValueError as exc:
                    raise ValueError("json patch index is invalid") from exc
                if index < 0 or index >= len(parent):
                    raise ValueError("json patch index out of range")
                parent[index] = value
            elif isinstance(parent, dict):
                if key not in parent:
                    raise ValueError("json patch path not found")
                parent[key] = value
            else:
                raise ValueError("json patch target is invalid")
        elif op_name == "remove":
            if isinstance(parent, list):
                try:
                    index = int(key)
                except ValueError as exc:
                    raise ValueError("json patch index is invalid") from exc
                if index < 0 or index >= len(parent):
                    raise ValueError("json patch index out of range")
                del parent[index]
            elif isinstance(parent, dict):
                if key not in parent:
                    raise ValueError("json patch path not found")
                del parent[key]
            else:
                raise ValueError("json patch target is invalid")
        else:
            raise ValueError("json patch op is not allowed")
    return updated


def apply_stage_result(
    capsule: dict[str, Any],
    stage_result: dict[str, Any],
    allow_dynamic: bool,
    capsule_validator: Callable[[dict[str, Any]], None] | None = None,
) -> tuple[dict[str, Any], bool]:
    validate_stage_result(stage_result, allow_dynamic=allow_dynamic)
    if stage_result.get("status") != "ok":
        return capsule, False
    if stage_result.get("output_is_partial"):
        return capsule, False
    try:
        updated = apply_capsule_patch(
            capsule, stage_result.get("capsule_patch", [])
        )
    except ValueError:
        return capsule, False
    if capsule_validator is not None:
        try:
            capsule_validator(updated)
        except ValueError:
            return capsule, False
    return updated, True


def execute_pipeline(
    stage_ids: list[str],
    capsule: dict[str, Any],
    stage_runner,
    allow_dynamic: bool,
    max_stages: int = 10,
    capsule_validator: Callable[[dict[str, Any]], None] | None = None,
    on_stage_complete: (
        Callable[[str, dict[str, Any], dict[str, Any], bool], None] | None
    ) = None,
    allowed_stage_ids: set[str] | None = None,
    dynamic_stage_specs: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
    if not stage_ids:
        raise ValueError("pipeline stages is empty")
    queue = list(stage_ids)
    results: list[dict[str, Any]] = []
    index = 0
    while index < len(queue):
        if len(queue) > max_stages:
            raise ValueError("pipeline stages exceed max_stages")
        stage_id = queue[index]
        stage_result = stage_runner(stage_id, capsule)
        if "stage_id" not in stage_result:
            stage_result["stage_id"] = stage_id
        validate_stage_result(stage_result, allow_dynamic=allow_dynamic)
        results.append(stage_result)
        capsule, applied = apply_stage_result(
            capsule,
            stage_result,
            allow_dynamic=allow_dynamic,
            capsule_validator=capsule_validator,
        )
        if on_stage_complete:
            on_stage_complete(stage_id, capsule, stage_result, applied)
        if not applied:
            return capsule, results, False
        if allow_dynamic and stage_result.get("next_stages"):
            next_specs = stage_result["next_stages"]
            if not isinstance(next_specs, list):
                raise ValueError("next_stages must be a list")
            inserted = []
            for spec in next_specs:
                validate_json_schema(spec, "stage_spec")
                stage_id_value = spec.get("id")
                if not isinstance(stage_id_value, str) or not stage_id_value:
                    raise ValueError("next_stages stage id is invalid")
                if (
                    allowed_stage_ids is not None
                    and stage_id_value not in allowed_stage_ids
                ):
                    raise ValueError("next_stages stage id is not allowed")
                if dynamic_stage_specs is not None:
                    dynamic_stage_specs.setdefault(
                        stage_id_value,
                        normalize_stage_spec(dict(spec), None),
                    )
                inserted.append(stage_id_value)
            for offset, stage_id_value in enumerate(inserted, start=1):
                queue.insert(index + offset, stage_id_value)
        index += 1
    return capsule, results, True


def run_pipeline_with_runner(
    stage_ids: list[str],
    capsule: dict[str, Any],
    stage_runner,
    allow_dynamic: bool,
    max_stages: int,
    capsule_validator: Callable[[dict[str, Any]], None] | None = None,
    on_stage_complete: (
        Callable[[str, dict[str, Any], dict[str, Any], bool], None] | None
    ) = None,
    allowed_stage_ids: set[str] | None = None,
    dynamic_stage_specs: dict[str, dict[str, Any]] | None = None,
) -> tuple[int, dict[str, Any], list[dict[str, Any]], bool, str]:
    wrapper_error = False
    error_message = ""
    try:
        final_capsule, stage_results, success = execute_pipeline(
            stage_ids=stage_ids,
            capsule=capsule,
            stage_runner=stage_runner,
            allow_dynamic=allow_dynamic,
            max_stages=max_stages,
            capsule_validator=capsule_validator,
            on_stage_complete=on_stage_complete,
            allowed_stage_ids=allowed_stage_ids,
            dynamic_stage_specs=dynamic_stage_specs,
        )
    except ValueError as exc:
        final_capsule = capsule
        stage_results = []
        success = False
        wrapper_error = True
        error_message = str(exc)

    exit_code = determine_pipeline_exit_code(success, wrapper_error)
    return exit_code, final_capsule, stage_results, success, error_message


def _decode_text(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return data


def _terminate_process_group_sync(
    proc: subprocess.Popen[str],
    grace_seconds: float = 1.5,
) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


async def _terminate_process_group_async(
    process: asyncio.subprocess.Process,
    grace_seconds: float = 1.5,
) -> None:
    if process.returncode is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        await asyncio.wait_for(process.wait(), timeout=grace_seconds)
        return
    except TimeoutError:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    await process.wait()


async def _collect_stream(
    stream: asyncio.StreamReader | None,
    max_bytes: int = MAX_CAPTURE_BYTES,
) -> tuple[bytes, bool]:
    if stream is None:
        return b"", False
    buf = bytearray()
    truncated = False
    try:
        while True:
            chunk = await stream.read(4096)
            if not chunk:
                break
            if len(buf) < max_bytes:
                remaining = max_bytes - len(buf)
                buf.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
            else:
                truncated = True
    except asyncio.CancelledError:
        # Return what we have (partial) on cancellation.
        pass
    return bytes(buf), truncated


# ============================================================================
# LLM-as-Judge (using codex exec)
# ============================================================================


async def evaluate_with_llm(
    output: str,
    prompt: str,
    task_type: TaskType,
    timeout: int = 60,
    profile: str | None = None,
    model: str | None = None,
) -> dict[str, Any] | None:
    """codex exec を使った LLM 評価"""
    eval_prompt = f"""You are an expert code evaluator. Evaluate the following output.

Task Type: {task_type.value}
Original Prompt: {prompt[:500]}

Output to Evaluate:
{truncate_output(output, 2000)}

Rate this output on a 1-5 scale for each criterion:
- CORRECTNESS: Does it meet requirements? No errors?
- COMPLETENESS: Are all requested items present?
- QUALITY: Is it readable, maintainable?
- EFFICIENCY: Is execution fast, tokens minimal?

Respond in JSON format ONLY (no explanation):
{{
  "correctness": N,
  "completeness": N,
  "quality": N,
  "efficiency": N,
  "rationale": "brief assessment",
  "strengths": ["..."],
  "weaknesses": ["..."]
}}"""

    try:
        result = await run_codex_exec_async(
            prompt=eval_prompt,
            sandbox=SandboxMode.READ_ONLY,
            timeout=timeout,
            agent_id="llm_judge",
            profile=profile,
            model=model,
        )

        if result.success and result.output:
            # JSON を抽出
            json_match = re.search(r"\{[^{}]*\}", result.output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        print(f"Warning: LLM evaluation failed: {e}", file=sys.stderr)

    return None


async def compare_with_llm_judge(
    prompt: str,
    task_type: TaskType,
    left: CodexResult,
    right: CodexResult,
    timeout: int = 90,
    profile: str | None = None,
    model: str | None = None,
) -> dict[str, Any] | None:
    judge_prompt = f"""You are a strict pairwise evaluator for agent outputs.

Task Type: {task_type.value}
Original Prompt: {prompt[:500]}

Candidate A:
{truncate_output(left.output, 2000)}

Candidate B:
{truncate_output(right.output, 2000)}

Return JSON only:
{{
  "winner": "A|B|tie",
  "rationale": "brief reason",
  "criteria": ["correctness", "completeness", "quality"]
}}"""
    try:
        result = await run_codex_exec_async(
            prompt=judge_prompt,
            sandbox=SandboxMode.READ_ONLY,
            timeout=timeout,
            agent_id="pairwise_judge",
            profile=profile,
            model=model,
        )
        if result.success and result.output:
            match = re.search(r"\{.*\}", result.output, re.DOTALL)
            if match:
                payload = json.loads(match.group())
                if payload.get("winner") in {"A", "B", "tie"}:
                    return payload
    except Exception as exc:
        print(f"Warning: pairwise judge failed: {exc}", file=sys.stderr)
    return None


def should_run_llm_eval(
    mode: ExecutionMode,
    heuristic_score: float,
    force_llm_eval: bool = False,
) -> bool:
    """LLM評価を実行すべきか判定"""
    if force_llm_eval:
        return True

    # Competition モードは常に実行
    if mode == ExecutionMode.COMPETITION:
        return True

    # エッジケース（スコアが極端）
    if heuristic_score < 2.5 or heuristic_score > 4.5:
        return True

    # サンプリング（20%）
    return random.random() < LLM_EVAL_SAMPLE_RATE


# ============================================================================
# Core Execution Functions
# ============================================================================


def run_codex_exec(
    prompt: str,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 360,
    agent_id: str = "agent_0",
    workdir: str | None = None,
    profile: str | None = None,
    model: str | None = None,
) -> CodexResult:
    """単一の codex exec を実行"""
    start_time = time.time()

    cmd = ["codex", "exec", "--sandbox", sandbox.value]
    if profile:
        cmd.extend(["--profile", profile])
    if model:
        cmd.extend(["--model", model])
    if workdir:
        cmd.extend(["--cd", workdir])
    cmd.append(prompt)

    proc: subprocess.Popen[str] | None = None
    try:
        proc: subprocess.Popen[str] = subprocess.Popen(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        timed_out = False
        output_is_partial = False
        stdout_text = ""
        stderr_text = ""

        try:
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            timed_out = True
            output_is_partial = True
            stdout_text = _decode_text(getattr(e, "stdout", None) or e.output)
            stderr_text = _decode_text(getattr(e, "stderr", None))
            _terminate_process_group_sync(proc)
            try:
                stdout_rest, stderr_rest = proc.communicate(timeout=1)
                stdout_text += stdout_rest
                stderr_text += stderr_rest
            except Exception:
                pass

        execution_time = timeout if timed_out else (time.time() - start_time)

        # トークン数を出力から抽出（概算）
        tokens_used = len(stdout_text.split()) * 2  # 概算

        returncode = proc.returncode
        success = (returncode == 0) and not timed_out
        if timed_out:
            error_message = f"Timeout after {timeout}s"
        elif returncode is None:
            error_message = "Process did not exit"
        elif returncode != 0:
            error_message = stderr_text
        else:
            error_message = ""

        return CodexResult(
            agent_id=agent_id,
            output=stdout_text,
            stderr=stderr_text,
            tokens_used=tokens_used,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            returncode=returncode,
            timed_out=timed_out,
            timeout_seconds=timeout if timed_out else None,
            output_is_partial=output_is_partial,
            metadata={"model": model},
        )
    except Exception as e:
        if proc is not None:
            _terminate_process_group_sync(proc)
        return CodexResult(
            agent_id=agent_id,
            output="",
            stderr="",
            success=False,
            error_message=str(e),
            returncode=None,
            timed_out=False,
            timeout_seconds=None,
            output_is_partial=False,
            metadata={"model": model},
        )


async def run_codex_exec_async(
    prompt: str,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 360,
    agent_id: str = "agent_0",
    workdir: str | None = None,
    profile: str | None = None,
    model: str | None = None,
) -> CodexResult:
    """非同期で codex exec を実行"""
    start_time = time.time()

    cmd = ["codex", "exec", "--sandbox", sandbox.value]
    if profile:
        cmd.extend(["--profile", profile])
    if model:
        cmd.extend(["--model", model])
    if workdir:
        cmd.extend(["--cd", workdir])
    cmd.append(prompt)

    process: asyncio.subprocess.Process | None = None
    stdout_task: asyncio.Task[tuple[bytes, bool]] | None = None
    stderr_task: asyncio.Task[tuple[bytes, bool]] | None = None
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        stdout_task = asyncio.create_task(_collect_stream(process.stdout))
        stderr_task = asyncio.create_task(_collect_stream(process.stderr))

        timed_out = False
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except TimeoutError:
            timed_out = True
            await _terminate_process_group_async(process)

        stdout, stdout_truncated = await stdout_task
        stderr, stderr_truncated = await stderr_task
        output_is_partial = timed_out or stdout_truncated or stderr_truncated

        execution_time = timeout if timed_out else (time.time() - start_time)

        output = _decode_text(stdout)
        stderr_text = _decode_text(stderr)
        tokens_used = len(output.split()) * 2

        returncode = process.returncode
        success = (returncode == 0) and not timed_out
        if timed_out:
            error_message = f"Timeout after {timeout}s"
        elif returncode is None:
            error_message = "Process did not exit"
        elif returncode != 0:
            error_message = stderr_text
        else:
            error_message = ""

        return CodexResult(
            agent_id=agent_id,
            output=output,
            stderr=stderr_text,
            tokens_used=tokens_used,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            returncode=returncode,
            timed_out=timed_out,
            timeout_seconds=timeout if timed_out else None,
            output_is_partial=output_is_partial,
            metadata={"model": model},
        )
    except Exception as e:
        if process is not None:
            await _terminate_process_group_async(process)
        if stdout_task is not None:
            stdout_task.cancel()
        if stderr_task is not None:
            stderr_task.cancel()
        return CodexResult(
            agent_id=agent_id,
            output="",
            stderr="",
            success=False,
            error_message=str(e),
            returncode=None,
            timed_out=False,
            timeout_seconds=None,
            output_is_partial=False,
            metadata={"model": model},
        )


async def execute_parallel(
    prompts: list[str],
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 360,
    workdir: str | None = None,
    profile: str | None = None,
    model: str | None = None,
) -> list[CodexResult]:
    """複数のプロンプトを並列実行"""
    tasks = [
        run_codex_exec_async(
            prompt=p,
            sandbox=sandbox,
            timeout=timeout,
            agent_id=f"agent_{i}",
            workdir=workdir,
            profile=profile,
            model=model,
        )
        for i, p in enumerate(prompts)
    ]
    return await asyncio.gather(*tasks)


async def execute_competition(
    prompt: str,
    count: int = 3,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 360,
    task_type: TaskType = TaskType.CODE_GEN,
    strategy: SelectionStrategy = SelectionStrategy.BEST_SINGLE,
    judge_mode: JudgeMode = JudgeMode.HYBRID,
    workdir: str | None = None,
    profile: str | None = None,
    model: str | None = None,
) -> CompetitionOutcome:
    """コンペモード: 複数実行 → 評価 → 最良選択"""
    # 同一プロンプトで複数回実行
    prompts = [prompt] * count
    results = await execute_parallel(
        prompts,
        sandbox,
        timeout,
        workdir,
        profile=profile,
        model=model,
    )

    # 成功した結果のみ評価
    successful = [r for r in results if r.success]
    if not successful:
        # 全て失敗した場合、最初の結果を返す
        best_result = (
            results[0]
            if results
            else CodexResult(
                agent_id="none",
                output="",
                success=False,
                error_message="No results",
            )
        )
        return CompetitionOutcome(
            best=EvaluatedResult(result=best_result, score=EvaluationScore()),
            results=results,
        )

    # 各結果を評価
    evaluated = [evaluate_result(r, task_type) for r in successful]

    # 選択戦略に基づいて最良を選択
    best = select_best(evaluated, strategy)
    selection: dict[str, Any] = {
        "judge_mode": judge_mode.value,
        "heuristic_winner": best.result.agent_id,
        "selected_by": "heuristic",
    }
    if judge_mode == JudgeMode.HYBRID and len(evaluated) >= 2:
        ranked = sorted(
            evaluated, key=lambda item: item.combined_score, reverse=True
        )
        left = ranked[0]
        right = ranked[1]
        pairwise = await compare_with_llm_judge(
            prompt=prompt,
            task_type=task_type,
            left=left.result,
            right=right.result,
            timeout=min(timeout, 90),
            profile=profile,
            model=model,
        )
        if pairwise:
            selection["pairwise_judge"] = pairwise
            selection["pairwise_candidates"] = [
                left.result.agent_id,
                right.result.agent_id,
            ]
            winner = pairwise.get("winner")
            if winner == "A":
                best = left
                selection["selected_by"] = "pairwise_judge"
            elif winner == "B":
                best = right
                selection["selected_by"] = "pairwise_judge"
            else:
                selection["selected_by"] = "heuristic_tiebreak"
    selection["winner"] = best.result.agent_id
    return CompetitionOutcome(best=best, results=results, selection=selection)


def evaluate_result(
    result: CodexResult, task_type: TaskType
) -> EvaluatedResult:
    """結果を評価してスコアを付与"""
    output = result.output
    score = EvaluationScore()

    # 基本的なヒューリスティック評価
    # CORRECTNESS: 出力があり、エラーがない
    if result.success and output:
        score.correctness = 4.0
        if len(output) > 100:
            score.correctness = 4.5
    elif result.success:
        score.correctness = 3.0
    else:
        score.correctness = 1.0

    # COMPLETENESS: 出力の長さと構造
    if output:
        # コードブロックの存在
        has_code = "```" in output
        # 見出しの存在
        has_headers = re.search(r"^#+\s", output, re.MULTILINE) is not None

        score.completeness = 3.0
        if has_code:
            score.completeness += 0.5
        if has_headers:
            score.completeness += 0.5
        if len(output) > 500:
            score.completeness += 0.5

    # QUALITY: 構造化と可読性
    if output:
        score.quality = 3.5
        # リストの存在
        if re.search(r"^[-*]\s", output, re.MULTILINE):
            score.quality += 0.3
        # 番号付きリスト
        if re.search(r"^\d+\.\s", output, re.MULTILINE):
            score.quality += 0.2

    # EFFICIENCY: 実行時間とトークン効率
    if result.execution_time < 30:
        score.efficiency = 4.5
    elif result.execution_time < 60:
        score.efficiency = 4.0
    elif result.execution_time < 120:
        score.efficiency = 3.0
    else:
        score.efficiency = 2.0

    # タスク別追加評価
    task_score = evaluate_task_specific(result, task_type)

    # 総合スコア（汎用60% + タスク別40%）
    combined = score.total * 0.6 + task_score * 0.4

    return EvaluatedResult(
        result=result,
        score=score,
        task_score=task_score,
        combined_score=combined,
    )


def evaluate_task_specific(result: CodexResult, task_type: TaskType) -> float:
    """タスク別の評価"""
    output = result.output

    if task_type == TaskType.CODE_GEN:
        score = 3.0
        # 関数/クラス定義の存在
        if re.search(r"(def |class |function |const |let )", output):
            score += 0.5
        # テストの言及
        if re.search(r"(test|spec|assert)", output, re.IGNORECASE):
            score += 0.5
        # エラーハンドリング
        if re.search(r"(try|except|catch|error)", output, re.IGNORECASE):
            score += 0.3
        return min(score, 5.0)

    elif task_type == TaskType.CODE_REVIEW:
        score = 3.0
        # 問題指摘
        if re.search(r"(bug|issue|problem|concern)", output, re.IGNORECASE):
            score += 0.5
        # 改善提案
        if re.search(
            r"(suggest|recommend|consider|should)", output, re.IGNORECASE
        ):
            score += 0.5
        # 行番号参照
        if re.search(r"line\s*\d+", output, re.IGNORECASE):
            score += 0.3
        return min(score, 5.0)

    elif task_type == TaskType.ANALYSIS:
        score = 3.0
        # 根拠の明示
        if re.search(r"(because|since|due to|reason)", output, re.IGNORECASE):
            score += 0.5
        # 構造化された分析
        if re.search(r"(overview|summary|conclusion)", output, re.IGNORECASE):
            score += 0.5
        return min(score, 5.0)

    elif task_type == TaskType.DOCUMENTATION:
        score = 3.0
        # セクション構造
        if output.count("#") >= 3:
            score += 0.5
        # 使用例
        if re.search(r"(example|usage|sample)", output, re.IGNORECASE):
            score += 0.5
        # コードブロック
        if "```" in output:
            score += 0.3
        return min(score, 5.0)

    return 3.0


def select_best(
    evaluated: list[EvaluatedResult],
    strategy: SelectionStrategy,
) -> EvaluatedResult:
    """選択戦略に基づいて最良の結果を選択"""
    if not evaluated:
        raise ValueError("No evaluated results")

    if strategy == SelectionStrategy.BEST_SINGLE:
        # 総合スコア最大
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.VOTING:
        # 平均スコアが高いもの（同一出力が複数あれば加点）
        output_counts: dict[str, int] = Counter(
            e.result.output for e in evaluated
        )
        for e in evaluated:
            vote_bonus = (output_counts[e.result.output] - 1) * 0.1
            e.combined_score += vote_bonus
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.HYBRID:
        # CORRECTNESS >= 4.0 かつ総合上位
        qualified = [e for e in evaluated if e.score.correctness >= 4.0]
        if qualified:
            return max(qualified, key=lambda e: e.combined_score)
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.CONSERVATIVE:
        # 実行時間が短く、合格ラインを満たすもの
        qualified = [e for e in evaluated if e.combined_score >= 3.5]
        if qualified:
            return min(qualified, key=lambda e: e.result.execution_time)
        return min(evaluated, key=lambda e: e.result.execution_time)

    return evaluated[0]


def _normalize(text: str) -> str:
    """テキストの正規化"""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s-]", "", text)
    return text


def merge_outputs(
    results: list[CodexResult],
    strategy: MergeStrategy,
    config: MergeConfig | None = None,
) -> str:
    """複数の出力をマージ"""
    if config is None:
        config = MergeConfig()

    outputs = [r.output for r in results if r.success and r.output]

    if not outputs:
        return ""

    if strategy == MergeStrategy.CONCAT:
        # 全て結合（セパレータ付き）
        return "\n\n---\n\n".join(outputs)

    elif strategy == MergeStrategy.DEDUP:
        # 重複除去
        seen = set()
        unique = []
        for o in outputs:
            normalized = _normalize(o)
            if normalized not in seen:
                seen.add(normalized)
                unique.append(o)
        return "\n\n---\n\n".join(unique)

    elif strategy == MergeStrategy.PRIORITY:
        # 最初の成功結果を優先
        return outputs[0]

    elif strategy == MergeStrategy.CONSENSUS:
        # 最も多い出力を採用
        normalized_outputs = [_normalize(o) for o in outputs]
        counts = Counter(normalized_outputs)
        top_normalized, top_count = counts.most_common(1)[0]

        if top_count >= config.min_votes:
            ratio = top_count / len(outputs)
            if ratio >= config.min_ratio:
                # 合意された出力の元のテキストを返す
                for o in outputs:
                    if _normalize(o) == top_normalized:
                        return o

        # フォールバック: 最初の出力
        return outputs[0]

    return outputs[0] if outputs else ""


def format_output(
    result: EvaluatedResult,
    verbose: bool = False,
) -> str:
    """結果を整形して出力"""
    lines = []

    if verbose:
        lines.append(f"Agent ID: {result.result.agent_id}")
        lines.append(f"Execution Time: {result.result.execution_time:.2f}s")
        lines.append(f"Tokens: {result.result.tokens_used}")
        lines.append(f"Score: {result.combined_score:.2f}")
        lines.append(f"  - Correctness: {result.score.correctness:.1f}")
        lines.append(f"  - Completeness: {result.score.completeness:.1f}")
        lines.append(f"  - Quality: {result.score.quality:.1f}")
        lines.append(f"  - Efficiency: {result.score.efficiency:.1f}")
        lines.append(f"  - Task Score: {result.task_score:.1f}")
        lines.append("")
        lines.append("--- Output ---")

    lines.append(result.result.output)

    return "\n".join(lines)


def build_stage_prompt_capsule_path(
    pipeline_run_id: str,
    stage_id: str,
    attempt: int,
    log_dir: str | Path,
) -> Path:
    artifact_dir = get_pipeline_artifact_dir(log_dir, pipeline_run_id)
    return artifact_dir / "stage-inputs" / f"{stage_id}-attempt-{attempt}.json"


def build_pipeline_state_payload(
    pipeline_run_id: str,
    log_dir: str | Path,
    prompt: str,
    canonical_spec: dict[str, Any],
    raw_pipeline_spec: dict[str, Any] | None,
    capsule: dict[str, Any],
    stage_results: list[dict[str, Any]],
    stage_logs: list[dict[str, Any]],
    attempts_by_stage: dict[str, int],
    completed_stage_ids: list[str],
    unauthorized_write_detected: bool,
    args: argparse.Namespace,
    success: bool | None = None,
    error_message: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": PIPELINE_SPEC_VERSION,
        "pipeline_run_id": pipeline_run_id,
        "log_dir": str(log_dir),
        "prompt": prompt,
        "pipeline_spec_raw": raw_pipeline_spec,
        "canonical_spec": canonical_spec,
        "capsule": capsule,
        "stage_results": stage_results,
        "stage_logs": stage_logs,
        "attempts_by_stage": attempts_by_stage,
        "completed_stage_ids": completed_stage_ids,
        "unauthorized_write_detected": unauthorized_write_detected,
        "success": success,
        "error_message": error_message,
        "args": {
            "sandbox": args.sandbox,
            "timeout": args.timeout,
            "profile": args.profile,
            "model": args.model,
            "workdir": args.workdir,
            "capsule_store": args.capsule_store,
            "capsule_path": args.capsule_path,
            "max_stages": args.max_stages,
            "max_parallel_stages": args.max_parallel_stages,
            "judge_mode": args.judge_mode,
        },
    }


def execute_stage_with_retry(
    *,
    stage_spec: dict[str, Any],
    capsule_state: dict[str, Any],
    base_prompt: str,
    pipeline_run_id: str,
    log_dir: str | Path,
    timeout: int,
    profile: str | None,
    model: str | None,
    default_workdir: str | None,
    capsule_store_arg: str,
    capsule_path_arg: str | None,
    max_total_prompt_chars: int | None,
    allow_dynamic: bool,
    previous_attempts: int,
    source_root: str | Path = ROOT_DIR,
) -> dict[str, Any]:
    policy = build_stage_policy(stage_spec)
    attempt_logs: list[dict[str, Any]] = []
    attempt_count = previous_attempts
    while attempt_count < policy.max_attempts:
        attempt_count += 1
        keep_workspace = False
        workspace = create_isolated_workspace(
            source_root,
            f"{pipeline_run_id}-{policy.stage_id}-attempt-{attempt_count}",
        )
        try:
            prompt_capsule = select_capsule_inputs(
                capsule_state, policy.input_keys
            )
            prompt_capsule_path_arg = capsule_path_arg
            if (
                capsule_store_arg in {"auto", "file"}
                and prompt_capsule_path_arg is None
            ):
                prompt_capsule_path_arg = str(
                    build_stage_prompt_capsule_path(
                        pipeline_run_id,
                        policy.stage_id,
                        attempt_count,
                        log_dir,
                    )
                )
            store_mode, prompt_capsule_path, size_bytes = (
                resolve_capsule_delivery(
                    capsule_store_arg,
                    prompt_capsule,
                    prompt_capsule_path_arg,
                    log_dir,
                    pipeline_run_id,
                )
            )
            if store_mode == "file" and prompt_capsule_path:
                write_capsule_file(prompt_capsule_path, prompt_capsule)
            stage_prompt = prepare_stage_prompt(
                stage_id=policy.stage_id,
                base_prompt=base_prompt,
                capsule=prompt_capsule,
                capsule_store=store_mode,
                capsule_path=prompt_capsule_path,
                stage_spec=stage_spec,
                stage_policy=policy,
                max_total_prompt_chars=max_total_prompt_chars,
                allow_dynamic=allow_dynamic,
            )
            before_snapshot = capture_repo_snapshot(workspace.path)
            effective_workdir = resolve_workspace_workdir(
                policy.workdir or default_workdir,
                workspace.path,
            )
            result = run_codex_exec(
                prompt=stage_prompt,
                sandbox=policy.sandbox,
                timeout=timeout,
                workdir=effective_workdir,
                profile=profile,
                model=model,
            )
            if not result.success:
                stage_result = stage_result_from_exec_failure(
                    policy.stage_id, result
                )
            else:
                try:
                    stage_result = parse_stage_result_output(
                        result.output,
                        allow_dynamic=allow_dynamic,
                    )
                except ValueError as exc:
                    stage_result = {
                        "schema_version": SCHEMA_VERSION,
                        "stage_id": policy.stage_id,
                        "status": "fatal_error",
                        "output_is_partial": True,
                        "capsule_patch": [],
                        "summary": f"stage_result parse failed: {exc}",
                    }
            after_snapshot = capture_repo_snapshot(workspace.path)
            write_policy = enforce_stage_write_policy(
                policy,
                before_snapshot,
                workspace_root=workspace.path,
                after_snapshot=after_snapshot,
                restore_unauthorized=False,
            )
            if write_policy["unauthorized_files"]:
                stage_result = {
                    "schema_version": SCHEMA_VERSION,
                    "stage_id": policy.stage_id,
                    "status": "fatal_error",
                    "output_is_partial": False,
                    "capsule_patch": [],
                    "summary": "unauthorized writes detected",
                }
            promotable_changes: dict[str, bytes | None] = {}
            if write_policy["authorized"]:
                promotable_changes = build_repo_change_set(
                    after_snapshot,
                    write_policy["changed_files"],
                )
            stage_log = build_stage_log(
                stage_id=policy.stage_id,
                pipeline_run_id=pipeline_run_id,
                capsule_state=capsule_state,
                store_mode=store_mode,
                capsule_path=prompt_capsule_path,
                size_bytes=size_bytes,
                exec_result=result,
                stage_result=stage_result,
            )
            stage_log["attempt"] = attempt_count
            stage_log["role"] = policy.role
            stage_log["sandbox"] = policy.sandbox.value
            stage_log["workdir"] = policy.workdir or default_workdir
            stage_log["effective_workdir"] = effective_workdir
            stage_log["workspace_mode"] = workspace.mode
            stage_log["write_roots"] = policy.write_roots
            stage_log["input_keys"] = policy.input_keys
            stage_log["depends_on"] = policy.depends_on
            stage_log["merge_strategy"] = policy.merge_strategy
            stage_log["changed_files"] = write_policy["changed_files"]
            stage_log["unauthorized_files"] = write_policy[
                "unauthorized_files"
            ]
            stage_log["authorized"] = write_policy["authorized"]
            attempt_logs.append(stage_log)
            if (
                stage_result.get("status") != "retryable_error"
                or attempt_count >= policy.max_attempts
            ):
                keep_workspace = True
                return {
                    "stage_result": stage_result,
                    "attempt_logs": attempt_logs,
                    "attempt_count": attempt_count,
                    "policy": policy,
                    "unauthorized_write": bool(
                        write_policy["unauthorized_files"]
                    ),
                    "workspace": workspace,
                    "workspace_cleaned": False,
                    "promotable_files": sorted(promotable_changes),
                }
            backoff_seconds = compute_retry_backoff_seconds(attempt_count)
            stage_log["retry_scheduled"] = True
            stage_log["retry_backoff_seconds"] = backoff_seconds
        finally:
            if not keep_workspace:
                cleanup_isolated_workspace(workspace)
        time.sleep(backoff_seconds)
    raise AssertionError("retry loop exited unexpectedly")


def run_pipeline_mode(
    args: argparse.Namespace,
    task_type: TaskType,
    enable_logging: bool,
) -> int:
    del task_type  # pipeline currently uses deterministic grading
    raw_pipeline_spec = (
        load_pipeline_spec(args.pipeline_spec) if args.pipeline_spec else None
    )
    if args.resume_run:
        state_path = resolve_resume_state_path(
            args.resume_run,
            effective_log_dir=LOG_DIR,
        )
        resume_state = load_pipeline_state(state_path)
        pipeline_run_id = str(resume_state["pipeline_run_id"])
        pipeline_log_dir = Path(
            resume_state.get("log_dir") or state_path.parents[2]
        )
        prompt = str(resume_state.get("prompt") or args.prompt)
        if raw_pipeline_spec is None:
            raw_pipeline_spec = resume_state.get("pipeline_spec_raw")
        canonical_spec = resume_state.get("canonical_spec")
        if not isinstance(canonical_spec, dict):
            canonical_spec = canonicalize_pipeline_spec(
                raw_pipeline_spec,
                args.pipeline_stages,
            )
        capsule = dict(resume_state.get("capsule") or {})
        stage_logs = list(resume_state.get("stage_logs") or [])
        attempts_by_stage = {
            str(key): int(value)
            for key, value in (
                resume_state.get("attempts_by_stage") or {}
            ).items()
        }
        completed_stage_ids = set(
            resume_state.get("completed_stage_ids") or []
        )
        pipeline_stage_results = [
            result
            for result in (resume_state.get("stage_results") or [])
            if result.get("stage_id") in completed_stage_ids
        ]
        unauthorized_write_detected = bool(
            resume_state.get("unauthorized_write_detected", False)
        )
    else:
        pipeline_log_dir = Path(LOG_DIR)
        canonical_spec = canonicalize_pipeline_spec(
            raw_pipeline_spec,
            args.pipeline_stages,
        )
        if raw_pipeline_spec is None and args.allow_dynamic_stages:
            canonical_spec["allow_dynamic_stages"] = True
            validate_canonical_pipeline_spec(canonical_spec)
        pipeline_run_id = str(uuid.uuid4())
        prompt = args.prompt
        capsule = build_initial_capsule(
            prompt,
            pipeline_run_id,
            SandboxMode(args.sandbox),
        )
        stage_logs = []
        attempts_by_stage: dict[str, int] = {}
        completed_stage_ids: set[str] = set()
        pipeline_stage_results: list[dict[str, Any]] = []
        unauthorized_write_detected = False

    state_path = get_pipeline_state_path(pipeline_log_dir, pipeline_run_id)
    write_pipeline_state(
        state_path,
        build_pipeline_state_payload(
            pipeline_run_id=pipeline_run_id,
            log_dir=pipeline_log_dir,
            prompt=prompt,
            canonical_spec=canonical_spec,
            raw_pipeline_spec=raw_pipeline_spec,
            capsule=capsule,
            stage_results=pipeline_stage_results,
            stage_logs=stage_logs,
            attempts_by_stage=attempts_by_stage,
            completed_stage_ids=sorted(completed_stage_ids),
            unauthorized_write_detected=unauthorized_write_detected,
            args=args,
        ),
    )

    stage_specs = list(canonical_spec["stages"])
    stage_spec_map = {stage["id"]: stage for stage in stage_specs}
    allow_dynamic = bool(canonical_spec.get("allow_dynamic_stages", False))
    max_total_prompt_chars = canonical_spec.get("max_total_prompt_chars")
    allowed_stage_ids = set(canonical_spec.get("allowed_stage_ids") or [])

    def persist_state(
        *,
        success: bool | None = None,
        error_message: str = "",
    ) -> None:
        write_pipeline_state(
            state_path,
            build_pipeline_state_payload(
                pipeline_run_id=pipeline_run_id,
                log_dir=pipeline_log_dir,
                prompt=prompt,
                canonical_spec=canonical_spec,
                raw_pipeline_spec=raw_pipeline_spec,
                capsule=capsule,
                stage_results=pipeline_stage_results,
                stage_logs=stage_logs,
                attempts_by_stage=attempts_by_stage,
                completed_stage_ids=sorted(completed_stage_ids),
                unauthorized_write_detected=unauthorized_write_detected,
                args=args,
                success=success,
                error_message=error_message,
            ),
        )

    def apply_stage_results_atomically(
        base_capsule: dict[str, Any],
        results_to_apply: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], bool]:
        candidate = json.loads(json.dumps(base_capsule))
        for stage_result in results_to_apply:
            candidate, applied = apply_stage_result(
                candidate,
                stage_result,
                allow_dynamic=allow_dynamic,
                capsule_validator=validate_capsule_payload,
            )
            if not applied:
                return base_capsule, False
        return candidate, True

    def record_stage_outcome(outcome: dict[str, Any]) -> None:
        nonlocal unauthorized_write_detected
        policy: StageExecutionPolicy = outcome["policy"]
        attempts_by_stage[policy.stage_id] = outcome["attempt_count"]
        stage_logs.extend(outcome["attempt_logs"])
        if outcome["unauthorized_write"]:
            unauthorized_write_detected = True
        persist_state()

    def run_stage_once(
        stage_spec: dict[str, Any], current_capsule: dict[str, Any]
    ) -> dict[str, Any]:
        previous_attempts = (
            attempts_by_stage.get(stage_spec["id"], 0)
            if stage_spec["id"] in completed_stage_ids
            else 0
        )
        return execute_stage_with_retry(
            stage_spec=stage_spec,
            capsule_state=current_capsule,
            base_prompt=prompt,
            pipeline_run_id=pipeline_run_id,
            log_dir=pipeline_log_dir,
            timeout=args.timeout,
            profile=args.profile,
            model=args.model,
            default_workdir=args.workdir,
            capsule_store_arg=args.capsule_store,
            capsule_path_arg=args.capsule_path,
            max_total_prompt_chars=max_total_prompt_chars,
            allow_dynamic=allow_dynamic,
            previous_attempts=previous_attempts,
            source_root=ROOT_DIR,
        )

    def register_dynamic_stages(
        queue: list[str],
        index: int,
        stage_result: dict[str, Any],
        dynamic_stage_specs: dict[str, dict[str, Any]],
    ) -> None:
        if not allow_dynamic or not stage_result.get("next_stages"):
            return
        next_specs = stage_result["next_stages"]
        if not isinstance(next_specs, list):
            raise ValueError("next_stages must be a list")
        inserted: list[str] = []
        for spec in next_specs:
            validate_json_schema(spec, "stage_spec")
            stage_id_value = spec.get("id")
            if not isinstance(stage_id_value, str) or not stage_id_value:
                raise ValueError("next_stages stage id is invalid")
            if (
                allowed_stage_ids is not None
                and stage_id_value not in allowed_stage_ids
            ):
                raise ValueError("next_stages stage id is not allowed")
            dynamic_stage_specs.setdefault(
                stage_id_value,
                normalize_stage_spec(dict(spec), None),
            )
            inserted.append(stage_id_value)
        for offset, stage_id_value in enumerate(inserted, start=1):
            queue.insert(index + offset, stage_id_value)

    wrapper_error = False
    success = False
    error_message = ""
    if canonical_spec.get("uses_graph"):
        ordered_outcomes: list[dict[str, Any]] = []
        try:
            layers = build_stage_layers(stage_specs)
            for layer in layers:
                pending_stage_ids = [
                    stage_id
                    for stage_id in layer
                    if stage_id not in completed_stage_ids
                ]
                if not pending_stage_ids:
                    continue
                layer_snapshot = json.loads(json.dumps(capsule))
                layer_outcomes: dict[str, dict[str, Any]] = {}
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max(1, args.max_parallel_stages)
                ) as executor:
                    future_map = {
                        executor.submit(
                            run_stage_once,
                            stage_spec_map[stage_id],
                            layer_snapshot,
                        ): stage_id
                        for stage_id in pending_stage_ids
                    }
                    for future in concurrent.futures.as_completed(future_map):
                        stage_id = future_map[future]
                        layer_outcomes[stage_id] = future.result()
                ordered_outcomes = [
                    layer_outcomes[stage_id] for stage_id in pending_stage_ids
                ]
                ordered_stage_results = [
                    outcome["stage_result"] for outcome in ordered_outcomes
                ]
                pipeline_stage_results.extend(ordered_stage_results)
                for outcome in ordered_outcomes:
                    record_stage_outcome(outcome)
                candidate_capsule, applied = apply_stage_results_atomically(
                    layer_snapshot,
                    ordered_stage_results,
                )
                if not applied:
                    for outcome in ordered_outcomes:
                        cleanup_stage_workspace(outcome)
                    error_message = "pipeline execution failed"
                    break
                conflicting_files = detect_conflicting_stage_changes(
                    ordered_outcomes
                )
                if conflicting_files:
                    error_message = (
                        "parallel stage file conflicts detected: "
                        + ", ".join(conflicting_files)
                    )
                    for outcome in ordered_outcomes:
                        cleanup_stage_workspace(outcome)
                    break
                for outcome in ordered_outcomes:
                    promote_stage_workspace(outcome, root=ROOT_DIR)
                capsule = candidate_capsule
                completed_stage_ids.update(pending_stage_ids)
                persist_state()
                ordered_outcomes = []
            success = len(completed_stage_ids) == len(stage_specs)
            if success:
                error_message = ""
            elif not error_message:
                error_message = "pipeline execution failed"
        except ValueError as exc:
            for outcome in ordered_outcomes:
                cleanup_stage_workspace(outcome)
            wrapper_error = True
            error_message = str(exc)
    else:
        dynamic_stage_specs: dict[str, dict[str, Any]] = {}
        queue = [
            stage["id"]
            for stage in stage_specs
            if stage["id"] not in completed_stage_ids
        ]
        index = 0
        outcome: dict[str, Any] | None = None
        try:
            while index < len(queue):
                if len(queue) > args.max_stages:
                    raise ValueError("pipeline stages exceed max_stages")
                stage_id = queue[index]
                stage_spec = find_stage_spec(
                    canonical_spec,
                    stage_id,
                    dynamic_stage_specs,
                )
                if not isinstance(stage_spec, dict):
                    raise ValueError("stage spec not found")
                outcome = run_stage_once(stage_spec, capsule)
                stage_result = outcome["stage_result"]
                pipeline_stage_results.append(stage_result)
                record_stage_outcome(outcome)
                candidate_capsule, applied = apply_stage_result(
                    capsule,
                    stage_result,
                    allow_dynamic=allow_dynamic,
                    capsule_validator=validate_capsule_payload,
                )
                if not applied:
                    error_message = "pipeline execution failed"
                    cleanup_stage_workspace(outcome)
                    break
                promote_stage_workspace(outcome, root=ROOT_DIR)
                capsule = candidate_capsule
                completed_stage_ids.add(stage_id)
                register_dynamic_stages(
                    queue,
                    index,
                    stage_result,
                    dynamic_stage_specs,
                )
                persist_state()
                outcome = None
                index += 1
            success = index == len(queue)
            if success:
                error_message = ""
            elif not error_message:
                error_message = "pipeline execution failed"
        except ValueError as exc:
            if outcome is not None:
                cleanup_stage_workspace(outcome)
            wrapper_error = True
            error_message = str(exc)

    persist_state(success=success, error_message=error_message)
    exit_code = determine_pipeline_exit_code(success, wrapper_error)
    if not success:
        final_store_mode, final_capsule_path, _ = resolve_capsule_delivery(
            args.capsule_store,
            capsule,
            args.capsule_path,
            pipeline_log_dir,
            pipeline_run_id,
        )
        if final_store_mode == "file" and final_capsule_path:
            write_capsule_file(final_capsule_path, capsule)
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": ExecutionMode.PIPELINE.value,
                    "prompt": truncate_output(prompt, 1000),
                    "sandbox": args.sandbox,
                    "task_type": TaskType.CODE_GEN.value,
                    "pipeline_run_id": pipeline_run_id,
                    "pipeline_stages": [stage["id"] for stage in stage_specs],
                    "allow_dynamic_stages": allow_dynamic,
                    "capsule_store": args.capsule_store,
                    "capsule_path": args.capsule_path,
                    "max_stages": args.max_stages,
                    "max_parallel_stages": args.max_parallel_stages,
                    "timeout_seconds": args.timeout,
                    "profile": args.profile,
                    "model": args.model,
                },
                results=stage_logs,
                evaluation={"heuristic": None, "human": None, "llm": None},
                metadata=get_git_info(),
            )
            write_log(log)
        if args.json:
            evaluation = build_pipeline_evaluation(
                stage_specs=stage_specs,
                stage_results=pipeline_stage_results,
                stage_logs=stage_logs,
                final_capsule=capsule,
                unauthorized_write_detected=unauthorized_write_detected,
                used_graph=canonical_spec.get("uses_graph", False),
                allow_dynamic=allow_dynamic,
            )
            payload = build_pipeline_output_payload(
                pipeline_run_id=pipeline_run_id,
                success=False,
                stage_results=pipeline_stage_results,
                final_capsule=capsule,
                capsule_store=final_store_mode,
                capsule_path=final_capsule_path,
                evaluation=evaluation,
                model=args.model,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("[error] pipeline execution failed", file=sys.stderr)
            print(serialize_capsule(capsule))
        return exit_code

    final_store_mode, final_capsule_path, _ = resolve_capsule_delivery(
        args.capsule_store,
        capsule,
        args.capsule_path,
        pipeline_log_dir,
        pipeline_run_id,
    )
    if final_store_mode == "file" and final_capsule_path:
        write_capsule_file(final_capsule_path, capsule)

    evaluation = build_pipeline_evaluation(
        stage_specs=stage_specs,
        stage_results=pipeline_stage_results,
        stage_logs=stage_logs,
        final_capsule=capsule,
        unauthorized_write_detected=unauthorized_write_detected,
        used_graph=canonical_spec.get("uses_graph", False),
        allow_dynamic=allow_dynamic,
    )
    persist_state(success=success, error_message=error_message)

    if enable_logging:
        log = ExecutionLog(
            execution={
                "mode": ExecutionMode.PIPELINE.value,
                "prompt": truncate_output(prompt, 1000),
                "sandbox": args.sandbox,
                "task_type": TaskType.CODE_GEN.value,
                "pipeline_run_id": pipeline_run_id,
                "pipeline_stages": [stage["id"] for stage in stage_specs],
                "allow_dynamic_stages": allow_dynamic,
                "capsule_store": args.capsule_store,
                "capsule_path": args.capsule_path,
                "max_stages": args.max_stages,
                "max_parallel_stages": args.max_parallel_stages,
                "timeout_seconds": args.timeout,
                "profile": args.profile,
                "model": args.model,
            },
            results=stage_logs,
            evaluation={"heuristic": evaluation, "human": None, "llm": None},
            metadata=get_git_info(),
        )
        log_path = write_log(log)
        if args.verbose and log_path:
            print(f"Log saved: {log_path}", file=sys.stderr)

    if args.json:
        payload = build_pipeline_output_payload(
            pipeline_run_id=pipeline_run_id,
            success=success,
            stage_results=pipeline_stage_results,
            final_capsule=capsule,
            capsule_store=final_store_mode,
            capsule_path=final_capsule_path,
            evaluation=evaluation,
            model=args.model,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if not success:
            print("[error] pipeline execution failed", file=sys.stderr)
        print(serialize_capsule(capsule))
    return EXIT_SUCCESS if success else EXIT_SUBAGENT_FAILED


def main() -> int:
    parser = argparse.ArgumentParser(
        description="codex exec サブエージェント実行ラッパー"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=[m.value for m in ExecutionMode],
        default=ExecutionMode.SINGLE.value,
        help="実行モード",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="実行するプロンプト",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="並列/コンペモードでの実行回数",
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        choices=[s.value for s in SandboxMode],
        default=SandboxMode.READ_ONLY.value,
        help="サンドボックスモード",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=360,
        help="タイムアウト（秒）",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="codex exec の --profile を指定",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="codex exec の --model を指定",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        choices=[t.value for t in TaskType],
        default=TaskType.CODE_GEN.value,
        help="タスク種別（コンペモード用）",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=[s.value for s in SelectionStrategy],
        default=SelectionStrategy.BEST_SINGLE.value,
        help="選択戦略（コンペモード用）",
    )
    parser.add_argument(
        "--merge",
        type=str,
        choices=[m.value for m in MergeStrategy],
        default=MergeStrategy.CONCAT.value,
        help="マージ戦略（並列モード用）",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        default=None,
        help="作業ディレクトリ",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細出力",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        default=True,
        help="ログを記録（デフォルト: 有効）",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="ログを無効化",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="ログ保存ルート（既定: .codex/sessions/codex_exec）",
    )
    parser.add_argument(
        "--log-scope",
        type=str,
        choices=["human", "auto"],
        default=None,
        help="ログ分類（既定: TTY 判定 / env: CODEX_SUBAGENT_LOG_SCOPE）",
    )
    parser.add_argument(
        "--llm-eval",
        action="store_true",
        help="LLM評価を強制実行",
    )
    parser.add_argument(
        "--judge-mode",
        type=str,
        choices=[mode.value for mode in JudgeMode],
        default=JudgeMode.HYBRID.value,
        help="competition の最終選定方式",
    )
    parser.add_argument(
        "--pipeline-stages",
        type=str,
        default=None,
        help="pipeline stage ID をカンマ区切りで指定",
    )
    parser.add_argument(
        "--pipeline-spec",
        type=str,
        default=None,
        help="pipeline spec JSON のパス",
    )
    parser.add_argument(
        "--allow-dynamic-stages",
        action="store_true",
        help="next_stages による動的追加を許可",
    )
    parser.add_argument(
        "--capsule-store",
        type=str,
        choices=["embed", "file", "auto"],
        default="auto",
        help="capsule の受け渡し方式",
    )
    parser.add_argument(
        "--capsule-path",
        type=str,
        default=None,
        help="capsule の保存パス（file 時のみ有効）",
    )
    parser.add_argument(
        "--max-stages",
        type=int,
        default=10,
        help="pipeline の最大 stage 数",
    )
    parser.add_argument(
        "--max-parallel-stages",
        type=int,
        default=DEFAULT_MAX_PARALLEL_STAGES,
        help="pipeline graph の最大並列 stage 数",
    )
    parser.add_argument(
        "--resume-run",
        type=str,
        default=None,
        help="pipeline の checkpoint state から再開する",
    )

    args = parser.parse_args()

    if args.max_parallel_stages <= 0:
        print("[error] max_parallel_stages must be positive", file=sys.stderr)
        return EXIT_WRAPPER_ERROR

    # --no-log が指定されていたらログを無効化
    enable_logging = args.log and not args.no_log

    global LOG_DIR
    LOG_DIR = resolve_log_dir(args.log_dir, args.log_scope)

    # Guardrails: fast/very-fast は「タスク極小化」前提でのみ使う。
    if args.profile in FAST_PROFILES:
        # 見落とし防止のため stderr に明示する（処理は継続）
        print(FAST_PROFILE_GUARDRAILS, file=sys.stderr)

        # 例: "1) ... 2) ..." や "A) ... B) ..." のような複数タスクを検出
        multipart = len(re.findall(r"(?m)^\s*\d+\)", args.prompt)) >= 2
        multipart = multipart or (
            len(re.findall(r"(?m)^\s*[A-Z]\)", args.prompt)) >= 2
        )
        if multipart:
            print(
                "[警告] --profile fast/very-fast で複数タスクが指定されています。"
                " 可能ならプロンプトを分割して再実行してください。",
                file=sys.stderr,
            )

        # fast 時はプロンプト先頭に安全策を付与して実行（推測抑制・極小化誘導）
        args.prompt = f"{FAST_PROFILE_GUARDRAILS}\n{args.prompt}"

    mode = ExecutionMode(args.mode)
    sandbox = SandboxMode(args.sandbox)
    task_type = TaskType(args.task_type)
    strategy = SelectionStrategy(args.strategy)
    judge_mode = JudgeMode(args.judge_mode)
    merge_strat = MergeStrategy(args.merge)
    exit_code = EXIT_SUCCESS

    if mode == ExecutionMode.SINGLE:
        result = run_codex_exec(
            prompt=args.prompt,
            sandbox=sandbox,
            timeout=args.timeout,
            workdir=args.workdir,
            profile=args.profile,
            model=args.model,
        )

        # ヒューリスティック評価
        evaluated = evaluate_result(result, task_type)
        heuristic_eval = {
            "correctness": evaluated.score.correctness,
            "completeness": evaluated.score.completeness,
            "quality": evaluated.score.quality,
            "efficiency": evaluated.score.efficiency,
            "combined_score": evaluated.combined_score,
        }

        # LLM 評価（条件付き）
        llm_eval = None
        if (
            result.success
            and result.output
            and should_run_llm_eval(
                mode, evaluated.combined_score, args.llm_eval
            )
        ):
            llm_eval = asyncio.run(
                evaluate_with_llm(
                    result.output,
                    args.prompt,
                    task_type,
                    timeout=60,
                    profile=args.profile,
                    model=args.model,
                )
            )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": 1,
                    "timeout_seconds": args.timeout,
                    "profile": args.profile,
                    "model": args.model,
                },
                results=[
                    {
                        "agent_id": result.agent_id,
                        "model": result.metadata.get("model"),
                        "output": truncate_output(result.output),
                        "stderr": truncate_output(result.stderr),
                        "tokens_used": result.tokens_used,
                        "execution_time": result.execution_time,
                        "success": result.success,
                        "returncode": result.returncode,
                        "timed_out": result.timed_out,
                        "timeout_seconds": result.timeout_seconds,
                        "output_is_partial": result.output_is_partial,
                        "error_message": result.error_message,
                    }
                ],
                evaluation={
                    "heuristic": heuristic_eval,
                    "human": None,
                    "llm": llm_eval,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "agent_id": result.agent_id,
                        "output": result.output,
                        "stderr": result.stderr,
                        "tokens_used": result.tokens_used,
                        "execution_time": result.execution_time,
                        "success": result.success,
                        "returncode": result.returncode,
                        "timed_out": result.timed_out,
                        "timeout_seconds": result.timeout_seconds,
                        "output_is_partial": result.output_is_partial,
                        "error_message": result.error_message,
                        "model": result.metadata.get("model"),
                        "evaluation": {
                            "heuristic": heuristic_eval,
                            "llm": llm_eval,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if args.verbose:
                print(f"Execution Time: {result.execution_time:.2f}s")
                print(f"Success: {result.success}")
                print(f"Score: {evaluated.combined_score:.2f}")
                print("--- Output ---")
            if not result.success and result.error_message:
                print(f"[error] {result.error_message}", file=sys.stderr)
            print(result.output)
        exit_code = EXIT_SUCCESS if result.success else EXIT_SUBAGENT_FAILED

    elif mode == ExecutionMode.PARALLEL:
        prompts = [args.prompt] * args.count
        results = asyncio.run(
            execute_parallel(
                prompts=prompts,
                sandbox=sandbox,
                timeout=args.timeout,
                workdir=args.workdir,
                profile=args.profile,
                model=args.model,
            )
        )
        merged = merge_outputs(results, merge_strat)

        # 各結果の評価
        evaluated_results = [
            evaluate_result(r, task_type) for r in results if r.success
        ]
        avg_score = (
            sum(e.combined_score for e in evaluated_results)
            / len(evaluated_results)
            if evaluated_results
            else 0
        )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": args.count,
                    "merge_strategy": merge_strat.value,
                    "timeout_seconds": args.timeout,
                    "profile": args.profile,
                    "model": args.model,
                },
                results=[
                    {
                        "agent_id": r.agent_id,
                        "model": r.metadata.get("model"),
                        "output": truncate_output(r.output),
                        "stderr": truncate_output(r.stderr),
                        "tokens_used": r.tokens_used,
                        "execution_time": r.execution_time,
                        "success": r.success,
                        "returncode": r.returncode,
                        "timed_out": r.timed_out,
                        "timeout_seconds": r.timeout_seconds,
                        "output_is_partial": r.output_is_partial,
                        "error_message": r.error_message,
                    }
                    for r in results
                ],
                evaluation={
                    "heuristic": {"average_score": avg_score},
                    "human": None,
                    "llm": None,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "results": [
                            {
                                "agent_id": r.agent_id,
                                "model": r.metadata.get("model"),
                                "output": r.output,
                                "stderr": r.stderr,
                                "success": r.success,
                                "execution_time": r.execution_time,
                                "returncode": r.returncode,
                                "timed_out": r.timed_out,
                                "timeout_seconds": r.timeout_seconds,
                                "output_is_partial": r.output_is_partial,
                                "error_message": r.error_message,
                            }
                            for r in results
                        ],
                        "merged_output": merged,
                        "evaluation": {"average_score": avg_score},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if args.verbose:
                for r in results:
                    print(
                        f"[{r.agent_id}] Time: {r.execution_time:.2f}s, "
                        f"Success: {r.success}"
                    )
                print(f"Average Score: {avg_score:.2f}")
                print("--- Merged Output ---")
            failures = [
                r for r in results if not r.success and r.error_message
            ]
            for r in failures:
                print(
                    f"[error] [{r.agent_id}] {r.error_message}",
                    file=sys.stderr,
                )
            print(merged)
        all_success = bool(results) and all(r.success for r in results)
        exit_code = EXIT_SUCCESS if all_success else EXIT_SUBAGENT_FAILED

    elif mode == ExecutionMode.COMPETITION:
        outcome = asyncio.run(
            execute_competition(
                prompt=args.prompt,
                count=args.count,
                sandbox=sandbox,
                timeout=args.timeout,
                task_type=task_type,
                strategy=strategy,
                judge_mode=judge_mode,
                workdir=args.workdir,
                profile=args.profile,
                model=args.model,
            )
        )
        best = outcome.best
        candidates = outcome.results

        heuristic_eval = {
            "correctness": best.score.correctness,
            "completeness": best.score.completeness,
            "quality": best.score.quality,
            "efficiency": best.score.efficiency,
            "task_score": best.task_score,
            "combined_score": best.combined_score,
        }

        # LLM 評価（Competition モードは常に実行）
        llm_eval = None
        if (
            best.result.success
            and best.result.output
            and should_run_llm_eval(mode, best.combined_score, args.llm_eval)
        ):
            llm_eval = asyncio.run(
                evaluate_with_llm(
                    best.result.output,
                    args.prompt,
                    task_type,
                    timeout=60,
                    profile=args.profile,
                    model=args.model,
                )
            )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": args.count,
                    "strategy": strategy.value,
                    "judge_mode": judge_mode.value,
                    "timeout_seconds": args.timeout,
                    "profile": args.profile,
                    "model": args.model,
                },
                results=[
                    (
                        {
                            "agent_id": r.agent_id,
                            "model": r.metadata.get("model"),
                            "output": truncate_output(r.output),
                            "stderr": truncate_output(r.stderr),
                            "tokens_used": r.tokens_used,
                            "execution_time": r.execution_time,
                            "success": r.success,
                            "returncode": r.returncode,
                            "timed_out": r.timed_out,
                            "timeout_seconds": r.timeout_seconds,
                            "output_is_partial": r.output_is_partial,
                            "error_message": r.error_message,
                            "selected": r.agent_id == best.result.agent_id,
                        }
                    )
                    for r in candidates
                ],
                evaluation={
                    "heuristic": heuristic_eval,
                    "human": None,
                    "llm": llm_eval,
                    "selection": outcome.selection,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "agent_id": best.result.agent_id,
                        "model": best.result.metadata.get("model"),
                        "output": best.result.output,
                        "stderr": best.result.stderr,
                        "combined_score": best.combined_score,
                        "scores": {
                            "correctness": best.score.correctness,
                            "completeness": best.score.completeness,
                            "quality": best.score.quality,
                            "efficiency": best.score.efficiency,
                            "task_score": best.task_score,
                        },
                        "execution_time": best.result.execution_time,
                        "success": best.result.success,
                        "returncode": best.result.returncode,
                        "timed_out": best.result.timed_out,
                        "timeout_seconds": best.result.timeout_seconds,
                        "output_is_partial": best.result.output_is_partial,
                        "error_message": best.result.error_message,
                        "llm_evaluation": llm_eval,
                        "selection": outcome.selection,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if not best.result.success and best.result.error_message:
                print(f"[error] {best.result.error_message}", file=sys.stderr)
            print(format_output(best, verbose=args.verbose))
        exit_code = (
            EXIT_SUCCESS if best.result.success else EXIT_SUBAGENT_FAILED
        )

    elif mode == ExecutionMode.PIPELINE:
        try:
            exit_code = run_pipeline_mode(
                args=args,
                task_type=task_type,
                enable_logging=enable_logging,
            )
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return EXIT_WRAPPER_ERROR

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(EXIT_WRAPPER_ERROR)
