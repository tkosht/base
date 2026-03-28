import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION


def test_execute_pipeline_success():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        if stage_id == "draft":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "draft",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/draft/content",
                        "value": "draft v1",
                    }
                ],
            }
        if stage_id == "critique":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "critique",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/critique/issues",
                        "value": ["gap"],
                    }
                ],
            }
        if stage_id == "revise":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "revise",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/revise/final",
                        "value": "final",
                    }
                ],
            }
        raise AssertionError("unexpected stage")

    final_capsule, results, success = codex_exec.execute_pipeline(
        ["draft", "critique", "revise"],
        capsule,
        runner,
        allow_dynamic=False,
    )
    assert success is True
    assert len(results) == 3
    assert final_capsule["draft"]["content"] == "draft v1"
    assert final_capsule["critique"]["issues"] == ["gap"]
    assert final_capsule["revise"]["final"] == "final"


def test_execute_pipeline_stops_on_failure():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        if stage_id == "draft":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "draft",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/draft/content",
                        "value": "draft v1",
                    }
                ],
            }
        if stage_id == "critique":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "critique",
                "status": "retryable_error",
                "output_is_partial": True,
                "capsule_patch": [],
            }
        raise AssertionError("unexpected stage")

    final_capsule, results, success = codex_exec.execute_pipeline(
        ["draft", "critique", "revise"],
        capsule,
        runner,
        allow_dynamic=False,
    )
    assert success is False
    assert len(results) == 2
    assert final_capsule["draft"]["content"] == "draft v1"
    assert final_capsule["critique"] == {}


def test_execute_pipeline_rejects_next_stages_without_allow():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [],
            "next_stages": [{"id": "extra"}],
        }

    with pytest.raises(ValueError, match="next_stages"):
        codex_exec.execute_pipeline(
            ["draft"], capsule, runner, allow_dynamic=False
        )


def test_execute_pipeline_allows_dynamic_stages():
    capsule = {"draft": {}, "critique": {}, "revise": {}}
    calls = []

    def runner(stage_id, _capsule):
        calls.append(stage_id)
        if stage_id == "draft":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "draft",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/draft/content",
                        "value": "draft v1",
                    }
                ],
                "next_stages": [{"id": "extra"}],
            }
        if stage_id == "extra":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "extra",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [
                    {
                        "op": "add",
                        "path": "/revise/final",
                        "value": "final",
                    }
                ],
            }
        raise AssertionError("unexpected stage")

    final_capsule, results, success = codex_exec.execute_pipeline(
        ["draft"], capsule, runner, allow_dynamic=True
    )
    assert success is True
    assert calls == ["draft", "extra"]
    assert len(results) == 2
    assert final_capsule["draft"]["content"] == "draft v1"
    assert final_capsule["revise"]["final"] == "final"


def test_execute_pipeline_enforces_max_stages():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [],
        }

    with pytest.raises(ValueError, match="max_stages"):
        codex_exec.execute_pipeline(
            ["draft", "critique"],
            capsule,
            runner,
            allow_dynamic=False,
            max_stages=1,
        )


def test_execute_pipeline_dynamic_add_does_not_replace_queue():
    capsule = {"draft": {}, "critique": {}, "revise": {}}
    calls = []

    def runner(stage_id, _capsule):
        calls.append(stage_id)
        if stage_id == "draft":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "draft",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [],
                "next_stages": [{"id": "extra"}],
            }
        if stage_id == "extra":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "extra",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [],
            }
        if stage_id == "critique":
            return {
                "schema_version": SCHEMA_VERSION,
                "stage_id": "critique",
                "status": "ok",
                "output_is_partial": False,
                "capsule_patch": [],
            }
        raise AssertionError("unexpected stage")

    _final_capsule, _results, success = codex_exec.execute_pipeline(
        ["draft", "critique"],
        capsule,
        runner,
        allow_dynamic=True,
    )
    assert success is True
    assert calls == ["draft", "extra", "critique"]


def test_execute_pipeline_stops_on_patch_apply_failure():
    capsule = {"facts": [], "draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [
                {
                    "op": "remove",
                    "path": "/facts/0",
                }
            ],
        }

    final_capsule, results, success = codex_exec.execute_pipeline(
        ["draft"], capsule, runner, allow_dynamic=False
    )
    assert success is False
    assert len(results) == 1
    assert final_capsule == capsule


def test_execute_pipeline_rejects_disallowed_dynamic_stage():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [],
            "next_stages": [{"id": "extra"}],
        }

    with pytest.raises(ValueError, match="not allowed"):
        codex_exec.execute_pipeline(
            ["draft"],
            capsule,
            runner,
            allow_dynamic=True,
            allowed_stage_ids={"draft"},
        )
