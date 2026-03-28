import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION


def test_stage_result_ok_requires_not_partial():
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "ok",
        "output_is_partial": True,
        "capsule_patch": [],
    }
    with pytest.raises(ValueError, match="output_is_partial"):
        codex_exec.validate_stage_result(result, allow_dynamic=False)


def test_stage_result_requires_capsule_patch():
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "ok",
        "output_is_partial": False,
        "capsule_patch": None,
    }
    with pytest.raises(ValueError, match="capsule_patch"):
        codex_exec.validate_stage_result(result, allow_dynamic=False)


def test_stage_result_error_allows_empty_patch():
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "retryable_error",
        "output_is_partial": True,
        "capsule_patch": [],
    }
    codex_exec.validate_stage_result(result, allow_dynamic=False)


def test_stage_result_error_rejects_nonempty_patch():
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "fatal_error",
        "output_is_partial": True,
        "capsule_patch": [{"op": "add", "path": "/facts/-", "value": 1}],
    }
    with pytest.raises(ValueError, match="capsule_patch"):
        codex_exec.validate_stage_result(result, allow_dynamic=False)


def test_patch_path_prefix_allows_children():
    ops = [
        {
            "op": "add",
            "path": "/facts/-",
            "value": {"source": "x", "claim": "y"},
        },
        {"op": "replace", "path": "/draft/content", "value": "ok"},
    ]
    codex_exec.validate_patch_ops(ops)


def test_patch_path_prefix_rejects_outside():
    ops = [{"op": "add", "path": "/drafts/content", "value": "no"}]
    with pytest.raises(ValueError, match="path"):
        codex_exec.validate_patch_ops(ops)


@pytest.mark.parametrize(
    "path",
    [
        "/open_questions",
        "/open_questions/-",
        "/assumptions/0",
        "/critique/issues",
        "/revise/final",
    ],
)
def test_patch_path_prefix_allows_all_prefixes(path):
    ops = [{"op": "add", "path": path, "value": "ok"}]
    codex_exec.validate_patch_ops(ops)


def test_patch_ops_rejects_disallowed_op():
    ops = [{"op": "move", "path": "/facts/0", "from": "/facts/1"}]
    with pytest.raises(ValueError, match="op"):
        codex_exec.validate_patch_ops(ops)


def test_capsule_hash_excludes_pipeline_run_id():
    capsule_a = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "aaa",
        "facts": [{"source": "x", "claim": "y"}],
    }
    capsule_b = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_run_id": "bbb",
        "facts": [{"source": "x", "claim": "y"}],
    }
    assert codex_exec.compute_capsule_hash(
        capsule_a
    ) == codex_exec.compute_capsule_hash(capsule_b)


def test_capsule_store_auto():
    assert codex_exec.resolve_capsule_store("auto", 10_000, None) == "embed"
    assert codex_exec.resolve_capsule_store("auto", 30_000, None) == "file"


def _capsule_with_exact_size(target_size: int):
    capsule = {"draft": {"content": ""}, "critique": {}, "revise": {}}
    base_size = codex_exec.capsule_size_bytes(capsule)
    assert base_size <= target_size
    filler_len = target_size - base_size
    capsule["draft"]["content"] = "a" * filler_len
    assert codex_exec.capsule_size_bytes(capsule) == target_size
    return capsule


def test_capsule_store_auto_boundary():
    capsule = _capsule_with_exact_size(20_000)
    size_bytes = codex_exec.capsule_size_bytes(capsule)
    assert (
        codex_exec.resolve_capsule_store("auto", size_bytes, None) == "embed"
    )
    capsule["draft"]["content"] += "a"
    size_bytes = codex_exec.capsule_size_bytes(capsule)
    assert codex_exec.resolve_capsule_store("auto", size_bytes, None) == "file"


def test_capsule_path_constraints():
    with pytest.raises(ValueError, match="capsule_path"):
        codex_exec.resolve_capsule_store("embed", 1_000, "/tmp/x.json")


def test_resolve_capsule_delivery_auto_uses_path_only_for_file(tmp_path):
    capsule = {"draft": {"content": "x"}, "critique": {}, "revise": {}}
    custom = tmp_path / "capsule.json"
    store_mode, capsule_path, _size = codex_exec.resolve_capsule_delivery(
        "auto", capsule, str(custom), tmp_path, "run-1"
    )
    assert store_mode == "embed"
    assert capsule_path is None

    big_capsule = _capsule_with_exact_size(20_001)
    store_mode, capsule_path, _size = codex_exec.resolve_capsule_delivery(
        "auto", big_capsule, str(custom), tmp_path, "run-1"
    )
    assert store_mode == "file"
    assert capsule_path == custom


def test_resolve_pipeline_stages_default():
    assert codex_exec.resolve_pipeline_stage_ids(None, None) == [
        "draft",
        "critique",
        "revise",
    ]


def test_resolve_pipeline_stages_conflict():
    spec = {"stages": [{"id": "draft"}]}
    with pytest.raises(ValueError, match="pipeline_spec"):
        codex_exec.resolve_pipeline_stage_ids("draft", spec)


def test_resolve_pipeline_stages_from_spec():
    spec = {"stages": [{"id": "draft"}, {"id": "critique"}]}
    assert codex_exec.resolve_pipeline_stage_ids(None, spec) == [
        "draft",
        "critique",
    ]


def test_resolve_pipeline_stages_reject_unknown():
    with pytest.raises(ValueError, match="unknown stage"):
        codex_exec.resolve_pipeline_stage_ids("draft,unknown", None)


def test_find_stage_spec_prefers_pipeline_spec():
    pipeline_spec = {
        "stages": [{"id": "draft", "instructions": "from pipeline spec"}]
    }
    dynamic_specs = {"draft": {"id": "draft", "instructions": "dynamic"}}
    spec = codex_exec.find_stage_spec(pipeline_spec, "draft", dynamic_specs)
    assert spec["instructions"] == "from pipeline spec"


def test_find_stage_spec_uses_dynamic_when_missing():
    pipeline_spec = {"stages": [{"id": "draft"}]}
    dynamic_specs = {"extra": {"id": "extra", "instructions": "dyn"}}
    spec = codex_exec.find_stage_spec(pipeline_spec, "extra", dynamic_specs)
    assert spec["instructions"] == "dyn"
