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
import hashlib
import json
import os
import random
import re
import signal
import subprocess
import sys
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
PIPELINE_STAGE_TEMPLATES = {
    "draft": {},
    "critique": {},
    "revise": {},
}


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


@dataclass
class MergeConfig:
    """マージ設定"""

    min_votes: int = 2
    min_ratio: float = 0.6
    priority_weight: float = 1.0
    confidence_weight: float = 1.0


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
) -> str:
    prompt = build_stage_prompt(
        stage_id=stage_id,
        base_prompt=base_prompt,
        capsule=capsule,
        capsule_store=capsule_store,
        capsule_path=capsule_path,
        stage_spec=stage_spec,
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
    return updated, True


def execute_pipeline(
    stage_ids: list[str],
    capsule: dict[str, Any],
    stage_runner,
    allow_dynamic: bool,
    max_stages: int = 10,
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
            capsule, stage_result, allow_dynamic=allow_dynamic
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
                    dynamic_stage_specs.setdefault(stage_id_value, dict(spec))
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
    return CompetitionOutcome(best=best, results=results)


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

    args = parser.parse_args()

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
        pipeline_run_id = str(uuid.uuid4())
        try:
            pipeline_spec = (
                load_pipeline_spec(args.pipeline_spec)
                if args.pipeline_spec
                else None
            )
            stage_ids = resolve_pipeline_stage_ids(
                args.pipeline_stages, pipeline_spec
            )
            if pipeline_spec is None:
                allow_dynamic = args.allow_dynamic_stages
            else:
                allow_dynamic = bool(
                    pipeline_spec.get("allow_dynamic_stages", False)
                )
            allowed_stage_ids = (
                pipeline_spec.get("allowed_stage_ids")
                if pipeline_spec
                else None
            )
            if allowed_stage_ids is not None:
                allowed_stage_ids_set = set(allowed_stage_ids)
            else:
                allowed_stage_ids_set = None
            max_total_prompt_chars = (
                pipeline_spec.get("max_total_prompt_chars")
                if pipeline_spec
                else None
            )
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return EXIT_WRAPPER_ERROR

        capsule = build_initial_capsule(args.prompt, pipeline_run_id, sandbox)
        stage_logs: list[dict[str, Any]] = []
        dynamic_stage_specs: dict[str, dict[str, Any]] = {}

        def stage_runner(
            stage_id: str,
            capsule_state: dict[str, Any],
        ) -> dict[str, Any]:
            validate_json_schema(capsule_state, "capsule")
            store_mode, capsule_path, size_bytes = resolve_capsule_delivery(
                args.capsule_store,
                capsule_state,
                args.capsule_path,
                LOG_DIR,
                pipeline_run_id,
            )
            if store_mode == "file" and capsule_path:
                write_capsule_file(capsule_path, capsule_state)

            stage_spec = find_stage_spec(
                pipeline_spec, stage_id, dynamic_stage_specs
            )
            stage_prompt = prepare_stage_prompt(
                stage_id=stage_id,
                base_prompt=args.prompt,
                capsule=capsule_state,
                capsule_store=store_mode,
                capsule_path=capsule_path,
                stage_spec=stage_spec,
                max_total_prompt_chars=max_total_prompt_chars,
                allow_dynamic=allow_dynamic,
            )
            result = run_codex_exec(
                prompt=stage_prompt,
                sandbox=sandbox,
                timeout=args.timeout,
                workdir=args.workdir,
                profile=args.profile,
                model=args.model,
            )

            if not result.success:
                stage_result = stage_result_from_exec_failure(stage_id, result)
                stage_log = build_stage_log(
                    stage_id=stage_id,
                    pipeline_run_id=pipeline_run_id,
                    capsule_state=capsule_state,
                    store_mode=store_mode,
                    capsule_path=capsule_path,
                    size_bytes=size_bytes,
                    exec_result=result,
                    stage_result=stage_result,
                )
                stage_logs.append(stage_log)
                return stage_result

            try:
                stage_result = parse_stage_result_output(
                    result.output, allow_dynamic=allow_dynamic
                )
            except ValueError as exc:
                stage_result = {
                    "schema_version": SCHEMA_VERSION,
                    "stage_id": stage_id,
                    "status": "fatal_error",
                    "output_is_partial": True,
                    "capsule_patch": [],
                    "summary": f"stage_result parse failed: {exc}",
                }
            stage_log = build_stage_log(
                stage_id=stage_id,
                pipeline_run_id=pipeline_run_id,
                capsule_state=capsule_state,
                store_mode=store_mode,
                capsule_path=capsule_path,
                size_bytes=size_bytes,
                exec_result=result,
                stage_result=stage_result,
            )
            stage_logs.append(stage_log)
            return stage_result

        def on_stage_complete(
            stage_id: str,
            capsule_state: dict[str, Any],
            stage_result: dict[str, Any],
            applied: bool,
        ) -> None:
            if not stage_logs:
                return
            store_mode, capsule_path, size_bytes = resolve_capsule_delivery(
                args.capsule_store,
                capsule_state,
                args.capsule_path,
                LOG_DIR,
                pipeline_run_id,
            )
            if store_mode == "file" and capsule_path and applied:
                write_capsule_file(capsule_path, capsule_state)

            stage_logs[-1]["capsule_hash_after"] = compute_capsule_hash(
                capsule_state
            )
            stage_logs[-1]["capsule_size_bytes_after"] = size_bytes
            stage_logs[-1]["capsule_store_after"] = store_mode
            stage_logs[-1]["capsule_path_after"] = (
                str(capsule_path) if capsule_path else None
            )
            stage_logs[-1]["applied"] = applied

        (
            exit_code,
            final_capsule,
            stage_results,
            success,
            error_message,
        ) = run_pipeline_with_runner(
            stage_ids=stage_ids,
            capsule=capsule,
            stage_runner=stage_runner,
            allow_dynamic=allow_dynamic,
            max_stages=args.max_stages,
            on_stage_complete=on_stage_complete,
            allowed_stage_ids=allowed_stage_ids_set,
            dynamic_stage_specs=dynamic_stage_specs,
        )
        if exit_code == EXIT_WRAPPER_ERROR and error_message:
            print(f"[error] {error_message}", file=sys.stderr)

        final_store_mode, final_capsule_path, _ = resolve_capsule_delivery(
            args.capsule_store,
            final_capsule,
            args.capsule_path,
            LOG_DIR,
            pipeline_run_id,
        )
        if final_store_mode == "file" and final_capsule_path:
            write_capsule_file(final_capsule_path, final_capsule)

        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "pipeline_run_id": pipeline_run_id,
                    "pipeline_stages": stage_ids,
                    "allow_dynamic_stages": allow_dynamic,
                    "capsule_store": args.capsule_store,
                    "capsule_path": args.capsule_path,
                    "max_stages": args.max_stages,
                    "timeout_seconds": args.timeout,
                    "profile": args.profile,
                    "model": args.model,
                },
                results=stage_logs,
                evaluation={
                    "heuristic": None,
                    "human": None,
                    "llm": None,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            payload = build_pipeline_output_payload(
                pipeline_run_id=pipeline_run_id,
                success=success,
                stage_results=stage_results,
                final_capsule=final_capsule,
                capsule_store=final_store_mode,
                capsule_path=final_capsule_path,
                model=args.model,
            )
            print(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if not success:
                print(
                    "[error] pipeline execution failed",
                    file=sys.stderr,
                )
            print(serialize_capsule(final_capsule))

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(EXIT_WRAPPER_ERROR)
