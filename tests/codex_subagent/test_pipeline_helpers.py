import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402

SCHEMA_VERSION = codex_exec.SCHEMA_VERSION


def test_stage_result_from_exec_failure_timeout():
    result = codex_exec.CodexResult(
        agent_id="agent_0",
        output="",
        stderr="timeout",
        success=False,
        returncode=124,
        timed_out=True,
        timeout_seconds=30,
        output_is_partial=True,
    )
    stage_result = codex_exec.stage_result_from_exec_failure("draft", result)
    assert stage_result["status"] == "retryable_error"
    assert stage_result["output_is_partial"] is True
    assert stage_result["capsule_patch"] == []


def test_stage_result_from_exec_failure_non_timeout():
    result = codex_exec.CodexResult(
        agent_id="agent_0",
        output="",
        stderr="error",
        success=False,
        returncode=1,
        timed_out=False,
        output_is_partial=False,
    )
    stage_result = codex_exec.stage_result_from_exec_failure("draft", result)
    assert stage_result["status"] == "fatal_error"
    assert stage_result["output_is_partial"] is False
    assert stage_result["capsule_patch"] == []


def test_determine_pipeline_exit_code():
    assert (
        codex_exec.determine_pipeline_exit_code(True, False)
        == codex_exec.EXIT_SUCCESS
    )
    assert (
        codex_exec.determine_pipeline_exit_code(False, False)
        == codex_exec.EXIT_SUBAGENT_FAILED
    )
    assert (
        codex_exec.determine_pipeline_exit_code(False, True)
        == codex_exec.EXIT_WRAPPER_ERROR
    )


def test_build_stage_log_includes_capsule_fields():
    capsule = {"draft": {}, "critique": {}, "revise": {}}
    result = codex_exec.CodexResult(
        agent_id="agent_0",
        output="ok",
        stderr="",
        success=True,
        returncode=0,
    )
    stage_result = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "ok",
        "output_is_partial": False,
        "capsule_patch": [],
    }
    log = codex_exec.build_stage_log(
        stage_id="draft",
        pipeline_run_id="run-1",
        capsule_state=capsule,
        store_mode="embed",
        capsule_path=None,
        size_bytes=123,
        exec_result=result,
        stage_result=stage_result,
    )
    assert log["stage_id"] == "draft"
    assert log["pipeline_run_id"] == "run-1"
    assert log["capsule_hash"]
    assert log["capsule_path"] is None
    assert log["stage_result"]["stage_id"] == "draft"


def test_run_pipeline_with_runner_exit_code_on_stage_failure():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "retryable_error",
            "output_is_partial": True,
            "capsule_patch": [],
        }

    exit_code, _capsule, results, success, error_message = (
        codex_exec.run_pipeline_with_runner(
            stage_ids=["draft"],
            capsule=capsule,
            stage_runner=runner,
            allow_dynamic=False,
            max_stages=5,
        )
    )
    assert success is False
    assert results
    assert error_message == ""
    assert exit_code == codex_exec.EXIT_SUBAGENT_FAILED


def test_run_pipeline_with_runner_exit_code_on_wrapper_error():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "invalid",
            "output_is_partial": False,
            "capsule_patch": [],
        }

    exit_code, _capsule, results, success, error_message = (
        codex_exec.run_pipeline_with_runner(
            stage_ids=["draft"],
            capsule=capsule,
            stage_runner=runner,
            allow_dynamic=False,
            max_stages=5,
        )
    )
    assert success is False
    assert results == []
    assert error_message
    assert exit_code == codex_exec.EXIT_WRAPPER_ERROR


def test_run_pipeline_with_runner_exit_code_on_success():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        return {
            "schema_version": SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [],
        }

    exit_code, _capsule, results, success, error_message = (
        codex_exec.run_pipeline_with_runner(
            stage_ids=["draft"],
            capsule=capsule,
            stage_runner=runner,
            allow_dynamic=False,
            max_stages=5,
        )
    )
    assert success is True
    assert results
    assert error_message == ""
    assert exit_code == codex_exec.EXIT_SUCCESS


def test_run_pipeline_with_runner_exit_code_on_timeout_failure():
    capsule = {"draft": {}, "critique": {}, "revise": {}}

    def runner(stage_id, _capsule):
        failure = codex_exec.CodexResult(
            agent_id="agent_0",
            output="",
            stderr="timeout",
            success=False,
            returncode=124,
            timed_out=True,
            timeout_seconds=30,
            output_is_partial=True,
        )
        return codex_exec.stage_result_from_exec_failure(stage_id, failure)

    exit_code, _capsule, results, success, error_message = (
        codex_exec.run_pipeline_with_runner(
            stage_ids=["draft"],
            capsule=capsule,
            stage_runner=runner,
            allow_dynamic=False,
            max_stages=5,
        )
    )
    assert success is False
    assert results
    assert error_message == ""
    assert exit_code == codex_exec.EXIT_SUBAGENT_FAILED


def test_build_pipeline_output_payload_fields():
    capsule = {"draft": {}, "critique": {}, "revise": {}}
    payload = codex_exec.build_pipeline_output_payload(
        pipeline_run_id="run-1",
        success=True,
        stage_results=[{"stage_id": "draft"}],
        final_capsule=capsule,
        capsule_store="embed",
        capsule_path=None,
    )
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
    assert payload["capsule_hash"] == codex_exec.compute_capsule_hash(capsule)
