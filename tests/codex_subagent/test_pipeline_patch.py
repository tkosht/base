import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402


def test_apply_patch_add_append():
    capsule = {"facts": []}
    ops = [{"op": "add", "path": "/facts/-", "value": {"source": "x"}}]
    updated = codex_exec.apply_capsule_patch(capsule, ops)
    assert len(updated["facts"]) == 1
    assert updated["facts"][0]["source"] == "x"


def test_apply_patch_replace():
    capsule = {"draft": {"content": "old"}}
    ops = [{"op": "replace", "path": "/draft/content", "value": "new"}]
    updated = codex_exec.apply_capsule_patch(capsule, ops)
    assert updated["draft"]["content"] == "new"


def test_apply_patch_remove():
    capsule = {"assumptions": ["a", "b"]}
    ops = [{"op": "remove", "path": "/assumptions/0"}]
    updated = codex_exec.apply_capsule_patch(capsule, ops)
    assert updated["assumptions"] == ["b"]


def test_apply_patch_invalid_index():
    capsule = {"facts": []}
    ops = [{"op": "remove", "path": "/facts/0"}]
    with pytest.raises(ValueError, match="index"):
        codex_exec.apply_capsule_patch(capsule, ops)
