import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402


def test_load_pipeline_spec_success(tmp_path):
    spec = {"stages": [{"id": "draft"}]}
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    assert codex_exec.load_pipeline_spec(path) == spec


def test_load_pipeline_spec_invalid(tmp_path):
    path = tmp_path / "spec.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="pipeline_spec"):
        codex_exec.load_pipeline_spec(path)


def test_load_pipeline_spec_missing(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="pipeline_spec"):
        codex_exec.load_pipeline_spec(path)


def test_resolve_capsule_path_default(tmp_path):
    log_dir = tmp_path / "logs"
    path = codex_exec.resolve_capsule_path("file", None, log_dir, "run-123")
    assert path == log_dir / "artifacts" / "run-123" / "capsule.json"


def test_resolve_capsule_path_custom(tmp_path):
    log_dir = tmp_path / "logs"
    custom = tmp_path / "capsule.json"
    path = codex_exec.resolve_capsule_path(
        "file", str(custom), log_dir, "run-123"
    )
    assert path == custom


def test_resolve_capsule_path_embed_rejects_custom(tmp_path):
    log_dir = tmp_path / "logs"
    with pytest.raises(ValueError, match="capsule_path"):
        codex_exec.resolve_capsule_path(
            "embed", "/tmp/capsule.json", log_dir, "run-123"
        )
