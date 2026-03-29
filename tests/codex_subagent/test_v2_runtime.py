import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "codex-subagent" / "scripts"
sys.path.append(str(SCRIPTS))

import codex_exec  # noqa: E402


def _make_args(tmp_path: Path, pipeline_spec: Path | None = None, **overrides):
    args = argparse.Namespace(
        prompt="test prompt",
        sandbox="read-only",
        timeout=30,
        profile=None,
        model=None,
        workdir=None,
        capsule_store="embed",
        capsule_path=None,
        max_stages=10,
        max_parallel_stages=2,
        judge_mode="hybrid",
        pipeline_spec=str(pipeline_spec) if pipeline_spec else None,
        pipeline_stages=None,
        allow_dynamic_stages=False,
        resume_run=None,
        json=True,
        verbose=False,
        log_dir=str(tmp_path),
        log_scope=None,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def _stage_result_output(stage_id: str, patch: list[dict]):
    return json.dumps(
        {
            "schema_version": codex_exec.SCHEMA_VERSION,
            "stage_id": stage_id,
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": patch,
        }
    )


def _extract_stage_id(prompt: str) -> str:
    match = re.search(
        r"You are executing pipeline stage: ([A-Za-z0-9_-]+)", prompt
    )
    assert match is not None
    return match.group(1)


def test_apply_stage_result_rejects_invalid_capsule_after_patch():
    capsule = codex_exec.build_initial_capsule(
        "goal",
        "run-1",
        codex_exec.SandboxMode.READ_ONLY,
    )
    stage_result = {
        "schema_version": codex_exec.SCHEMA_VERSION,
        "stage_id": "draft",
        "status": "ok",
        "output_is_partial": False,
        "capsule_patch": [{"op": "remove", "path": "/draft/content"}],
    }
    updated, applied = codex_exec.apply_stage_result(
        capsule,
        stage_result,
        allow_dynamic=False,
        capsule_validator=codex_exec.validate_capsule_payload,
    )
    assert applied is False
    assert updated == capsule


def test_validate_patch_ops_rejects_top_level_remove():
    with pytest.raises(ValueError, match="top-level"):
        codex_exec.validate_patch_ops([{"op": "remove", "path": "/draft"}])


def test_canonicalize_pipeline_spec_sets_v2_defaults():
    spec = {
        "stages": [
            {"id": "draft"},
            {"id": "execute"},
            {"id": "review"},
        ]
    }
    canonical = codex_exec.canonicalize_pipeline_spec(spec)
    assert canonical["schema_version"] == codex_exec.PIPELINE_SPEC_VERSION
    assert canonical["stages"][0]["role"] == "planner"
    assert canonical["stages"][1]["role"] == "executor"
    assert canonical["stages"][1]["max_attempts"] == 2
    assert canonical["stages"][1]["write_roots"] == ["."]
    assert canonical["stages"][2]["role"] == "reviewer"
    assert canonical["stages"][2]["depends_on"] == ["execute"]


def test_enforce_stage_write_policy_restores_unauthorized(monkeypatch):
    before = {
        "allowed/file.txt": codex_exec.RepoSnapshotEntry(
            kind="file",
            mode=0o644,
            mtime_ns=1,
            content=b"before",
        ),
        "other.txt": codex_exec.RepoSnapshotEntry(
            kind="file",
            mode=0o644,
            mtime_ns=1,
            content=b"before-other",
        ),
    }
    after = {
        "allowed/file.txt": codex_exec.RepoSnapshotEntry(
            kind="file",
            mode=0o644,
            mtime_ns=2,
            content=b"after",
        ),
        "other.txt": codex_exec.RepoSnapshotEntry(
            kind="file",
            mode=0o644,
            mtime_ns=2,
            content=b"after-other",
        ),
    }
    restored: list[str] = []
    monkeypatch.setattr(
        codex_exec,
        "capture_repo_snapshot",
        lambda *_args, **_kwargs: after,
    )
    monkeypatch.setattr(
        codex_exec,
        "restore_repo_paths",
        lambda before_snapshot, after_snapshot, target_paths, **kwargs: (
            restored.extend(target_paths)
        ),
    )
    policy = codex_exec.StageExecutionPolicy(
        stage_id="review",
        role="reviewer",
        sandbox=codex_exec.SandboxMode.READ_ONLY,
        workdir=None,
        write_roots=["allowed"],
        input_keys=["draft"],
        max_attempts=1,
        depends_on=[],
        merge_strategy=None,
    )
    result = codex_exec.enforce_stage_write_policy(policy, before)
    assert result["changed_files"] == ["allowed/file.txt", "other.txt"]
    assert result["unauthorized_files"] == ["other.txt"]
    assert restored == ["other.txt"]


def test_execute_stage_with_retry_retries_retryable_error(
    monkeypatch, tmp_path
):
    calls = {"count": 0}

    def fake_run_codex_exec(**kwargs):
        del kwargs
        calls["count"] += 1
        if calls["count"] == 1:
            return codex_exec.CodexResult(
                agent_id="agent_0",
                output="",
                stderr="timeout",
                success=False,
                returncode=124,
                timed_out=True,
                timeout_seconds=30,
                output_is_partial=True,
            )
        return codex_exec.CodexResult(
            agent_id="agent_0",
            output=_stage_result_output(
                "execute",
                [{"op": "add", "path": "/facts/-", "value": {"status": "ok"}}],
            ),
            success=True,
            returncode=0,
        )

    monkeypatch.setattr(codex_exec, "run_codex_exec", fake_run_codex_exec)
    monkeypatch.setattr(
        codex_exec,
        "create_isolated_workspace",
        lambda source_root, stage_label: codex_exec.IsolatedWorkspace(
            path=tmp_path,
            cleanup_root=tmp_path,
            mode="copy",
        ),
    )
    monkeypatch.setattr(
        codex_exec, "cleanup_isolated_workspace", lambda workspace: None
    )
    monkeypatch.setattr(
        codex_exec,
        "enforce_stage_write_policy",
        lambda policy, before_snapshot, **kwargs: {
            "changed_files": [],
            "unauthorized_files": [],
            "authorized": True,
        },
    )
    monkeypatch.setattr(codex_exec.time, "sleep", lambda _: None)

    outcome = codex_exec.execute_stage_with_retry(
        stage_spec=codex_exec.normalize_stage_spec({"id": "execute"}, "draft"),
        capsule_state=codex_exec.build_initial_capsule(
            "goal",
            "run-1",
            codex_exec.SandboxMode.READ_ONLY,
        ),
        base_prompt="goal",
        pipeline_run_id="run-1",
        log_dir=tmp_path,
        timeout=30,
        profile=None,
        model=None,
        default_workdir=None,
        capsule_store_arg="embed",
        capsule_path_arg=None,
        max_total_prompt_chars=None,
        allow_dynamic=False,
        previous_attempts=0,
    )

    assert outcome["attempt_count"] == 2
    assert outcome["stage_result"]["status"] == "ok"
    assert outcome["attempt_logs"][0]["retry_scheduled"] is True
    codex_exec.cleanup_stage_workspace(outcome)


def test_resolve_workspace_workdir_remaps_repo_absolute_path(
    monkeypatch, tmp_path
):
    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    workspace_root = tmp_path / "ws"
    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)

    resolved = codex_exec.resolve_workspace_workdir(
        str(primary_root / "subdir"),
        workspace_root,
    )

    assert resolved == str(workspace_root / "subdir")


def test_resolve_workspace_workdir_rejects_external_absolute_path(
    monkeypatch, tmp_path
):
    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)

    with pytest.raises(ValueError, match="repo root"):
        codex_exec.resolve_workspace_workdir(str(outside), tmp_path / "ws")


def test_apply_repo_changes_preserves_executable_mode(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    tool = src / "tool.sh"
    tool.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    os.chmod(tool, 0o755)

    snapshot = codex_exec.capture_repo_snapshot(src)
    changes = codex_exec.build_repo_change_set(snapshot, ["tool.sh"])
    codex_exec.apply_repo_changes(changes, root=dst)

    mode = stat.S_IMODE((dst / "tool.sh").stat().st_mode)
    assert mode == 0o755


def test_apply_repo_changes_preserves_symlink(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    (src / "target.txt").write_text("target", encoding="utf-8")
    (src / "link.txt").symlink_to("target.txt")

    snapshot = codex_exec.capture_repo_snapshot(src)
    changes = codex_exec.build_repo_change_set(snapshot, ["link.txt"])
    codex_exec.apply_repo_changes(changes, root=dst)

    assert (dst / "link.txt").is_symlink()
    assert os.readlink(dst / "link.txt") == "target.txt"


def test_run_pipeline_mode_resume_from_failed_stage(
    monkeypatch, tmp_path, capsys
):
    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [{"id": "draft"}, {"id": "verify"}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    stage_calls = {"draft": 0, "verify": 0}

    def fake_run_codex_exec(**kwargs):
        stage_id = _extract_stage_id(kwargs["prompt"])
        stage_calls[stage_id] += 1
        if stage_id == "draft":
            return codex_exec.CodexResult(
                agent_id="draft",
                output=_stage_result_output(
                    "draft",
                    [{"op": "add", "path": "/draft/content", "value": "ok"}],
                ),
                success=True,
                returncode=0,
            )
        if stage_calls["verify"] == 1:
            return codex_exec.CodexResult(
                agent_id="verify",
                output="",
                stderr="timeout",
                success=False,
                returncode=124,
                timed_out=True,
                timeout_seconds=30,
                output_is_partial=True,
            )
        return codex_exec.CodexResult(
            agent_id="verify",
            output=_stage_result_output(
                "verify",
                [
                    {
                        "op": "add",
                        "path": "/facts/-",
                        "value": {"verified": True},
                    }
                ],
            ),
            success=True,
            returncode=0,
        )

    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)
    monkeypatch.setattr(codex_exec, "LOG_DIR", tmp_path)
    monkeypatch.setattr(codex_exec, "run_codex_exec", fake_run_codex_exec)
    monkeypatch.setattr(
        codex_exec,
        "enforce_stage_write_policy",
        lambda policy, before_snapshot, **kwargs: {
            "changed_files": [],
            "unauthorized_files": [],
            "authorized": True,
        },
    )

    args = _make_args(tmp_path, spec_path)
    first_exit = codex_exec.run_pipeline_mode(
        args=args,
        task_type=codex_exec.TaskType.ANALYSIS,
        enable_logging=False,
    )
    first_payload = json.loads(capsys.readouterr().out)
    assert first_exit == codex_exec.EXIT_SUBAGENT_FAILED
    assert first_payload["success"] is False
    assert stage_calls == {"draft": 1, "verify": 1}

    state_paths = list((tmp_path / "artifacts").glob("*/state.json"))
    assert len(state_paths) == 1

    resume_args = _make_args(
        tmp_path,
        spec_path,
        resume_run=str(state_paths[0]),
    )
    second_exit = codex_exec.run_pipeline_mode(
        args=resume_args,
        task_type=codex_exec.TaskType.ANALYSIS,
        enable_logging=False,
    )
    second_payload = json.loads(capsys.readouterr().out)
    assert second_exit == codex_exec.EXIT_SUCCESS
    assert second_payload["success"] is True
    assert stage_calls == {"draft": 1, "verify": 2}


def test_build_stage_layers_handles_branch_join():
    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [
            {"id": "draft"},
            {
                "id": "exec_a",
                "depends_on": ["draft"],
                "write_roots": ["pkg_a"],
            },
            {
                "id": "exec_b",
                "depends_on": ["draft"],
                "write_roots": ["pkg_b"],
            },
            {
                "id": "reduce",
                "role": "reducer",
                "depends_on": ["exec_a", "exec_b"],
            },
        ],
    }
    canonical = codex_exec.canonicalize_pipeline_spec(spec)
    assert codex_exec.build_stage_layers(canonical["stages"]) == [
        ["draft"],
        ["exec_a", "exec_b"],
        ["reduce"],
    ]


def test_canonicalize_graph_writer_requires_explicit_write_roots():
    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [
            {"id": "draft"},
            {"id": "exec_a", "depends_on": ["draft"]},
        ],
    }
    with pytest.raises(ValueError, match="write_roots"):
        codex_exec.canonicalize_pipeline_spec(spec)


def test_resolve_resume_state_path_uses_custom_log_root(tmp_path):
    custom_log_dir = tmp_path / "logs" / "human"
    state_path = custom_log_dir / "artifacts" / "run-123" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text("{}", encoding="utf-8")

    resolved = codex_exec.resolve_resume_state_path(
        "run-123",
        effective_log_dir=custom_log_dir,
    )

    assert resolved == state_path


def test_run_pipeline_mode_does_not_promote_failed_stage_workspace_changes(
    monkeypatch, tmp_path, capsys
):
    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    allowed_dir = primary_root / "allowed"
    allowed_dir.mkdir()
    target_file = allowed_dir / "result.txt"
    target_file.write_text("before", encoding="utf-8")

    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [
            {"id": "execute", "write_roots": ["allowed"]},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    def fake_run_codex_exec(**kwargs):
        workdir = Path(kwargs["workdir"])
        (workdir / "allowed").mkdir(exist_ok=True)
        (workdir / "allowed" / "result.txt").write_text(
            "after",
            encoding="utf-8",
        )
        return codex_exec.CodexResult(
            agent_id="execute",
            output=_stage_result_output(
                "execute",
                [{"op": "remove", "path": "/draft/content"}],
            ),
            success=True,
            returncode=0,
        )

    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)
    monkeypatch.setattr(codex_exec, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(codex_exec, "run_codex_exec", fake_run_codex_exec)

    args = _make_args(tmp_path, spec_path)
    exit_code = codex_exec.run_pipeline_mode(
        args=args,
        task_type=codex_exec.TaskType.ANALYSIS,
        enable_logging=False,
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == codex_exec.EXIT_SUBAGENT_FAILED
    assert payload["success"] is False
    assert target_file.read_text(encoding="utf-8") == "before"

    state_paths = list((tmp_path / "logs" / "artifacts").glob("*/state.json"))
    assert len(state_paths) == 1
    state_payload = json.loads(state_paths[0].read_text(encoding="utf-8"))
    assert state_payload["completed_stage_ids"] == []


def test_run_pipeline_mode_graph_promotes_non_conflicting_parallel_writers(
    monkeypatch, tmp_path, capsys
):
    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [
            {"id": "draft"},
            {
                "id": "exec_a",
                "depends_on": ["draft"],
                "write_roots": ["pkg_a"],
            },
            {
                "id": "exec_b",
                "depends_on": ["draft"],
                "write_roots": ["pkg_b"],
            },
        ],
    }
    spec_path = tmp_path / "graph.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    def fake_run_codex_exec(**kwargs):
        stage_id = _extract_stage_id(kwargs["prompt"])
        workdir = Path(kwargs["workdir"])
        if stage_id == "draft":
            return codex_exec.CodexResult(
                agent_id="draft",
                output=_stage_result_output(
                    "draft",
                    [{"op": "add", "path": "/draft/content", "value": "ok"}],
                ),
                success=True,
                returncode=0,
            )
        target_dir = workdir / ("pkg_a" if stage_id == "exec_a" else "pkg_b")
        target_dir.mkdir(exist_ok=True)
        (target_dir / "result.txt").write_text(stage_id, encoding="utf-8")
        return codex_exec.CodexResult(
            agent_id=stage_id,
            output=_stage_result_output(
                stage_id,
                [
                    {
                        "op": "add",
                        "path": "/facts/-",
                        "value": {"stage": stage_id},
                    }
                ],
            ),
            success=True,
            returncode=0,
        )

    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)
    monkeypatch.setattr(codex_exec, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(codex_exec, "run_codex_exec", fake_run_codex_exec)

    args = _make_args(tmp_path, spec_path)
    exit_code = codex_exec.run_pipeline_mode(
        args=args,
        task_type=codex_exec.TaskType.ANALYSIS,
        enable_logging=False,
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == codex_exec.EXIT_SUCCESS
    assert payload["success"] is True
    assert (primary_root / "pkg_a" / "result.txt").read_text(
        encoding="utf-8"
    ) == "exec_a"
    assert (primary_root / "pkg_b" / "result.txt").read_text(
        encoding="utf-8"
    ) == "exec_b"


def test_run_pipeline_mode_graph_rejects_conflicting_parallel_writers(
    monkeypatch, tmp_path, capsys
):
    primary_root = tmp_path / "repo"
    primary_root.mkdir()
    shared_dir = primary_root / "shared"
    shared_dir.mkdir()
    target_file = shared_dir / "result.txt"
    target_file.write_text("before", encoding="utf-8")

    spec = {
        "schema_version": codex_exec.PIPELINE_SPEC_VERSION,
        "stages": [
            {"id": "draft"},
            {
                "id": "exec_a",
                "depends_on": ["draft"],
                "write_roots": ["shared"],
            },
            {
                "id": "exec_b",
                "depends_on": ["draft"],
                "write_roots": ["shared"],
            },
        ],
    }
    spec_path = tmp_path / "graph-conflict.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    def fake_run_codex_exec(**kwargs):
        stage_id = _extract_stage_id(kwargs["prompt"])
        workdir = Path(kwargs["workdir"])
        if stage_id == "draft":
            return codex_exec.CodexResult(
                agent_id="draft",
                output=_stage_result_output(
                    "draft",
                    [{"op": "add", "path": "/draft/content", "value": "ok"}],
                ),
                success=True,
                returncode=0,
            )
        shared = workdir / "shared"
        shared.mkdir(exist_ok=True)
        (shared / "result.txt").write_text(stage_id, encoding="utf-8")
        return codex_exec.CodexResult(
            agent_id=stage_id,
            output=_stage_result_output(
                stage_id,
                [
                    {
                        "op": "add",
                        "path": "/facts/-",
                        "value": {"stage": stage_id},
                    }
                ],
            ),
            success=True,
            returncode=0,
        )

    monkeypatch.setattr(codex_exec, "ROOT_DIR", primary_root)
    monkeypatch.setattr(codex_exec, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(codex_exec, "run_codex_exec", fake_run_codex_exec)

    args = _make_args(tmp_path, spec_path)
    exit_code = codex_exec.run_pipeline_mode(
        args=args,
        task_type=codex_exec.TaskType.ANALYSIS,
        enable_logging=False,
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == codex_exec.EXIT_SUBAGENT_FAILED
    assert payload["success"] is False
    assert target_file.read_text(encoding="utf-8") == "before"


def test_build_pipeline_evaluation_marks_retry_policy_followed():
    stage_specs = [
        codex_exec.normalize_stage_spec(
            {"id": "execute", "max_attempts": 2},
            previous_stage_id=None,
        )
    ]
    stage_results = [
        {
            "schema_version": codex_exec.SCHEMA_VERSION,
            "stage_id": "execute",
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [
                {"op": "add", "path": "/facts/-", "value": {"status": "ok"}}
            ],
        }
    ]
    stage_logs = [
        {
            "stage_id": "execute",
            "attempt": 1,
            "retry_scheduled": True,
            "stage_result": {
                "status": "retryable_error",
            },
        },
        {
            "stage_id": "execute",
            "attempt": 2,
            "stage_result": stage_results[0],
        },
    ]

    evaluation = codex_exec.build_pipeline_evaluation(
        stage_specs=stage_specs,
        stage_results=stage_results,
        stage_logs=stage_logs,
        final_capsule=codex_exec.build_initial_capsule(
            "goal",
            "run-1",
            codex_exec.SandboxMode.READ_ONLY,
        ),
        unauthorized_write_detected=False,
        used_graph=False,
    )

    assert evaluation["retry_policy_followed"] is True


def test_build_pipeline_evaluation_detects_missing_retry_evidence():
    stage_specs = [
        codex_exec.normalize_stage_spec(
            {"id": "execute", "max_attempts": 2},
            previous_stage_id=None,
        )
    ]
    stage_results = [
        {
            "schema_version": codex_exec.SCHEMA_VERSION,
            "stage_id": "execute",
            "status": "ok",
            "output_is_partial": False,
            "capsule_patch": [
                {"op": "add", "path": "/facts/-", "value": {"status": "ok"}}
            ],
        }
    ]
    stage_logs = [
        {
            "stage_id": "execute",
            "attempt": 1,
            "stage_result": {
                "status": "retryable_error",
            },
        },
        {
            "stage_id": "execute",
            "attempt": 2,
            "stage_result": stage_results[0],
        },
    ]

    evaluation = codex_exec.build_pipeline_evaluation(
        stage_specs=stage_specs,
        stage_results=stage_results,
        stage_logs=stage_logs,
        final_capsule=codex_exec.build_initial_capsule(
            "goal",
            "run-1",
            codex_exec.SandboxMode.READ_ONLY,
        ),
        unauthorized_write_detected=False,
        used_graph=False,
    )

    assert evaluation["retry_policy_followed"] is False


@pytest.mark.asyncio
async def test_execute_competition_hybrid_uses_pairwise_judge(monkeypatch):
    async def fake_execute_parallel(*args, **kwargs):
        del args, kwargs
        return [
            codex_exec.CodexResult(
                agent_id="agent_a", output="A", success=True
            ),
            codex_exec.CodexResult(
                agent_id="agent_b", output="B", success=True
            ),
        ]

    async def fake_compare_with_llm_judge(**kwargs):
        del kwargs
        return {"winner": "B", "rationale": "better"}

    monkeypatch.setattr(codex_exec, "execute_parallel", fake_execute_parallel)
    monkeypatch.setattr(
        codex_exec,
        "compare_with_llm_judge",
        fake_compare_with_llm_judge,
    )

    outcome = await codex_exec.execute_competition(
        prompt="compare",
        judge_mode=codex_exec.JudgeMode.HYBRID,
    )

    assert outcome.best.result.agent_id == "agent_b"
    assert outcome.selection["selected_by"] == "pairwise_judge"
