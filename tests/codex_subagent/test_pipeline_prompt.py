import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION


def test_build_stage_prompt_embed_includes_capsule_and_stage():
    capsule = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "run-1",
        "facts": [],
    }
    prompt = codex_exec.build_stage_prompt(
        stage_id="draft",
        base_prompt="Do the thing",
        capsule=capsule,
        capsule_store="embed",
        capsule_path=None,
        stage_spec=None,
        allow_dynamic=False,
    )
    assert "draft" in prompt
    assert "Do the thing" in prompt
    assert '"pipeline_run_id"' in prompt


def test_build_stage_prompt_file_includes_path():
    capsule = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "run-2",
        "facts": [],
    }
    path = Path("/tmp/capsule.json")
    prompt = codex_exec.build_stage_prompt(
        stage_id="draft",
        base_prompt="Do the thing",
        capsule=capsule,
        capsule_store="file",
        capsule_path=path,
        stage_spec=None,
        allow_dynamic=False,
    )
    assert str(path) in prompt
    assert '"pipeline_run_id"' not in prompt


def test_build_stage_prompt_allows_next_stages_when_dynamic():
    capsule = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "run-3",
        "facts": [],
    }
    prompt = codex_exec.build_stage_prompt(
        stage_id="draft",
        base_prompt="Do the thing",
        capsule=capsule,
        capsule_store="embed",
        capsule_path=None,
        stage_spec=None,
        allow_dynamic=True,
    )
    assert '"next_stages"' in prompt


def test_parse_stage_result_output_accepts_json():
    output = "\n".join(
        [
            "note",
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "stage_id": "draft",
                    "status": "ok",
                    "output_is_partial": False,
                    "capsule_patch": [],
                }
            ),
        ]
    )
    result = codex_exec.parse_stage_result_output(output, allow_dynamic=False)
    assert result["stage_id"] == "draft"


def test_parse_stage_result_output_rejects_invalid():
    output = json.dumps({"schema_version": SCHEMA_VERSION})
    with pytest.raises(ValueError, match="stage_result"):
        codex_exec.parse_stage_result_output(output, allow_dynamic=False)


def test_ensure_prompt_limit_rejects_oversize():
    prompt = "x" * 50
    with pytest.raises(ValueError, match="max_total_prompt_chars"):
        codex_exec.ensure_prompt_limit(prompt, 10)


def test_prepare_stage_prompt_enforces_max_total_prompt_chars():
    capsule = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "run-1",
        "facts": [],
    }
    with pytest.raises(ValueError, match="max_total_prompt_chars"):
        codex_exec.prepare_stage_prompt(
            stage_id="draft",
            base_prompt="x" * 50,
            capsule=capsule,
            capsule_store="embed",
            capsule_path=None,
            stage_spec=None,
            max_total_prompt_chars=10,
            allow_dynamic=False,
        )
