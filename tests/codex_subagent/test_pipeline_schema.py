import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION


def test_pipeline_spec_schema_valid(tmp_path):
    spec = {
        "stages": [{"id": "draft"}],
        "allow_dynamic_stages": True,
        "allowed_stage_ids": ["draft", "extra"],
        "max_total_prompt_chars": 1000,
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    loaded = codex_exec.load_pipeline_spec(path)
    assert loaded["stages"][0]["id"] == "draft"


def test_pipeline_spec_schema_rejects_unknown_key(tmp_path):
    spec = {"stages": [{"id": "draft"}], "unknown": 1}
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(ValueError, match="pipeline_spec"):
        codex_exec.load_pipeline_spec(path)


def test_stage_spec_schema_rejects_unknown_key():
    with pytest.raises(ValueError, match="stage_spec"):
        codex_exec.validate_json_schema(
            {"id": "draft", "action": "replace"}, "stage_spec"
        )


def test_stage_result_schema_rejects_wrong_type():
    payload = json.dumps(
        {
            "schema_version": 1,
            "stage_id": "draft",
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [],
        }
    )
    with pytest.raises(ValueError, match="stage_result"):
        codex_exec.parse_stage_result_output(payload, allow_dynamic=False)


def test_capsule_schema_rejects_missing_required():
    with pytest.raises(ValueError, match="capsule"):
        codex_exec.validate_json_schema(
            {"schema_version": SCHEMA_VERSION}, "capsule"
        )
