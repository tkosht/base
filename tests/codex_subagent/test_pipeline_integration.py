import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))
SCRIPT = (
    ROOT
    / ".claude"
    / "skills"
    / "codex-subagent"
    / "scripts"
    / "codex_exec.py"
)

RUN_INTEGRATION = os.environ.get("CODEX_INTEGRATION") == "1"
HAS_CODEX = shutil.which("codex") is not None

pytestmark = pytest.mark.skipif(
    not RUN_INTEGRATION or not HAS_CODEX,
    reason="set CODEX_INTEGRATION=1 and ensure codex is on PATH",
)

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION
DYNAMIC_STAGE_SENTINEL = "DYNAMIC_STAGE_SPEC_OK"
DEFAULT_INTEGRATION_MAX_ATTEMPTS = 2


def _parse_integration_max_attempts(raw_value: str | None) -> int:
    if not raw_value:
        return DEFAULT_INTEGRATION_MAX_ATTEMPTS
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_INTEGRATION_MAX_ATTEMPTS
    return max(1, value)


INTEGRATION_MAX_ATTEMPTS = _parse_integration_max_attempts(
    os.environ.get("CODEX_INTEGRATION_MAX_ATTEMPTS")
)


def _stage_instruction(stage_id: str) -> str:
    return (
        "Return JSON only, no markdown. Required keys: "
        "schema_version, stage_id, status, output_is_partial, capsule_patch. "
        f'Use schema_version "{SCHEMA_VERSION}", stage_id from the prompt, '
        'status "ok", output_is_partial false, capsule_patch []. '
        "Do not add other keys."
    )


def _dynamic_stage_patch(sentinel: str) -> list[dict]:
    return [
        {
            "op": "add",
            "path": "/draft/dynamic_stage_note",
            "value": sentinel,
        }
    ]


def _stage_instruction_with_patch(sentinel: str) -> str:
    return (
        "Return JSON only, no markdown. Required keys: "
        "schema_version, stage_id, status, output_is_partial, capsule_patch. "
        f'Use schema_version "{SCHEMA_VERSION}", stage_id from the prompt, '
        'status "ok", output_is_partial false, '
        f"capsule_patch {json.dumps(_dynamic_stage_patch(sentinel))}. "
        "Do not add other keys."
    )


def _stage_instruction_with_next(sentinel: str) -> str:
    next_spec = {
        "id": "extra",
        "instructions": _stage_instruction_with_patch(sentinel),
    }
    return (
        "Return JSON only, no markdown. Required keys: "
        "schema_version, stage_id, status, output_is_partial, capsule_patch, "
        "next_stages. "
        f'Use schema_version "{SCHEMA_VERSION}", stage_id from the prompt, '
        'status "ok", output_is_partial false, capsule_patch []. '
        f"Include next_stages with one entry: {json.dumps(next_spec)}. "
        "Do not add other keys."
    )


def _assert_payload_fields(payload: dict) -> None:
    for key in (
        "pipeline_run_id",
        "success",
        "stage_results",
        "capsule",
        "capsule_hash",
        "capsule_store",
        "capsule_path",
    ):
        assert key in payload
    assert payload["pipeline_run_id"]
    assert payload["capsule_store"] == "embed"
    assert payload["capsule_path"] is None
    assert payload["capsule_hash"] == codex_exec.compute_capsule_hash(
        payload["capsule"]
    )


def _assert_stage_results(
    stage_results: list[dict],
    expected: list[str],
    allow_patch_stage_ids: set[str] | None = None,
) -> None:
    allow_patch_stage_ids = allow_patch_stage_ids or set()
    stage_ids = [item["stage_id"] for item in stage_results]
    assert stage_ids == expected
    for item in stage_results:
        assert item["schema_version"] == SCHEMA_VERSION
        assert item["status"] == "ok"
        assert item["output_is_partial"] is False
        if item["stage_id"] in allow_patch_stage_ids:
            assert item["capsule_patch"]
        else:
            assert item["capsule_patch"] == []


def _run_pipeline(
    tmp_path: Path,
    spec: dict,
    prompt: str,
    validate: Callable[[dict], None] | None = None,
) -> dict:
    spec_path = tmp_path / "pipeline_spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--mode",
        "pipeline",
        "--pipeline-spec",
        str(spec_path),
        "--sandbox",
        "read-only",
        "--capsule-store",
        "embed",
        "--timeout",
        "60",
        "--json",
        "--no-log",
        "--prompt",
        prompt,
    ]
    last_error: AssertionError | None = None
    for attempt in range(1, INTEGRATION_MAX_ATTEMPTS + 1):
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            last_error = AssertionError(
                "pipeline command failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        else:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                last_error = AssertionError(
                    "pipeline output is not valid JSON\n"
                    f"error: {exc}\n"
                    f"stdout:\n{result.stdout}\n"
                    f"stderr:\n{result.stderr}"
                )
            else:
                if validate is not None:
                    try:
                        validate(payload)
                    except AssertionError as exc:
                        last_error = AssertionError(
                            "pipeline payload validation failed\n"
                            f"error: {exc}\n"
                            f"payload:\n{json.dumps(payload, indent=2)}"
                        )
                    else:
                        return payload
                else:
                    return payload
        if attempt < INTEGRATION_MAX_ATTEMPTS:
            continue
    assert last_error is not None
    raise AssertionError(
        f"pipeline failed after {INTEGRATION_MAX_ATTEMPTS} attempts: "
        f"{last_error}"
    )


def test_pipeline_cli_smoke_success(tmp_path):
    prompt = "Follow Stage Instructions exactly."
    spec = {
        "stages": [
            {"id": "draft", "instructions": _stage_instruction("draft")},
            {"id": "critique", "instructions": _stage_instruction("critique")},
            {"id": "revise", "instructions": _stage_instruction("revise")},
        ],
        "allow_dynamic_stages": False,
    }

    def _validate(payload: dict) -> None:
        assert payload["success"] is True
        _assert_payload_fields(payload)
        _assert_stage_results(
            payload["stage_results"], ["draft", "critique", "revise"]
        )

    _run_pipeline(tmp_path, spec, prompt, validate=_validate)


def test_pipeline_cli_dynamic_stage(tmp_path):
    prompt = "Follow Stage Instructions exactly."
    spec = {
        "stages": [
            {
                "id": "draft",
                "instructions": _stage_instruction_with_next(
                    DYNAMIC_STAGE_SENTINEL
                ),
            },
            {"id": "revise", "instructions": _stage_instruction("revise")},
        ],
        "allow_dynamic_stages": True,
        "allowed_stage_ids": ["draft", "extra", "revise"],
    }

    def _validate(payload: dict) -> None:
        assert payload["success"] is True
        _assert_payload_fields(payload)
        _assert_stage_results(
            payload["stage_results"],
            ["draft", "extra", "revise"],
            allow_patch_stage_ids={"extra"},
        )
        extra = next(
            item
            for item in payload["stage_results"]
            if item["stage_id"] == "extra"
        )
        assert extra["capsule_patch"] == _dynamic_stage_patch(
            DYNAMIC_STAGE_SENTINEL
        )
        assert (
            payload["capsule"]["draft"]["dynamic_stage_note"]
            == DYNAMIC_STAGE_SENTINEL
        )

    _run_pipeline(tmp_path, spec, prompt, validate=_validate)
