from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "harness-autoptimizer" / "scripts"
sys.path.append(str(SCRIPTS))

import harness_autopt  # noqa: E402


def _resource(
    *,
    resource_id: str = "project-docs",
    kind: str = "documentation",
    goals: tuple[str, ...] = ("consistency",),
) -> harness_autopt.HarnessResource:
    return harness_autopt.HarnessResource(
        id=resource_id,
        kind=kind,
        authority="canonical",
        paths=("README.md",),
        mutable_paths=("README.md",),
        validators=("make doctor", "make lint", "make test"),
        excluded_paths=("docs/architecture/decision-records",),
        goals=goals,
        max_changed_files=2,
        max_changed_lines=200,
    )


def test_load_resource_registry_includes_codex_subagent() -> None:
    resources = harness_autopt.load_resource_registry(
        ROOT / "docs" / "architecture" / "harness-resources.toml"
    )

    resource = resources["codex-subagent"]
    assert resource.kind == "skill"
    assert "make test" in resource.validators
    assert ".claude/skills/codex-subagent" in resource.mutable_paths


def test_load_resource_registry_includes_markdown_docs_resource() -> None:
    resources = harness_autopt.load_resource_registry(
        ROOT / "docs" / "architecture" / "harness-resources.toml"
    )

    resource = resources["project-docs"]
    assert resource.kind == "documentation"
    assert "README.md" in resource.mutable_paths
    assert "docs/architecture/decision-records" in (
        resources["knowledge-docs"].excluded_paths
    )
    assert resource.max_changed_files == 2
    assert resource.max_changed_lines == 200


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (".claude/skills/codex-subagent/SKILL.md", True),
        ("tests/codex_subagent/test_pipeline_cli.py", True),
        ("docs/ai/skills/codex-subagent.md", True),
        ("package.json", False),
        ("secrets/token.txt", False),
        (".codex/auth.json", False),
        (".env", False),
    ],
)
def test_is_path_allowed(path: str, expected: bool) -> None:
    allowed = (
        ".claude/skills/codex-subagent",
        "docs/ai/skills/codex-subagent.md",
        "tests/codex_subagent",
    )
    assert harness_autopt.is_path_allowed(path, allowed) is expected


def test_evaluate_diff_guard_rejects_unallowed_path() -> None:
    result = harness_autopt.evaluate_diff_guard(
        changed_files=("package.json",),
        changed_lines=2,
        allowed_prefixes=("tests/codex_subagent",),
        max_changed_files=8,
        max_changed_lines=800,
    )

    assert result.ok is False
    assert result.violations == ("path is not allowed: package.json",)


def test_evaluate_diff_guard_rejects_excluded_path() -> None:
    result = harness_autopt.evaluate_diff_guard(
        changed_files=("docs/architecture/decision-records/old.md",),
        changed_lines=2,
        allowed_prefixes=("docs/architecture",),
        excluded_prefixes=("docs/architecture/decision-records",),
        max_changed_files=8,
        max_changed_lines=800,
    )

    assert result.ok is False
    assert result.violations == (
        "path is excluded: docs/architecture/decision-records/old.md",
    )


def test_evaluate_diff_guard_rejects_large_diff() -> None:
    result = harness_autopt.evaluate_diff_guard(
        changed_files=(
            "tests/codex_subagent/a.py",
            "tests/codex_subagent/b.py",
        ),
        changed_lines=900,
        allowed_prefixes=("tests/codex_subagent",),
        max_changed_files=1,
        max_changed_lines=800,
    )

    assert result.ok is False
    assert "changed file count 2 exceeds 1" in result.violations
    assert "changed line count 900 exceeds 800" in result.violations


def test_parse_status_paths_handles_renames() -> None:
    output = " M a.py\n?? b.py\nR  old.py -> new.py\n"
    assert harness_autopt.parse_status_paths(output) == (
        "a.py",
        "b.py",
        "new.py",
        "old.py",
    )


def test_build_branch_name_uses_autopt_prefix() -> None:
    branch = harness_autopt.build_branch_name(
        "codex-subagent", "20260424T000000Z-abc12345"
    )

    assert branch.startswith("autopt/codex-subagent-")
    assert branch.endswith("-abc12345")


def test_build_autopt_request_includes_constraints_and_all_resources() -> None:
    resources = {
        "project-docs": _resource(),
        "test-performance": _resource(
            resource_id="test-performance",
            kind="test_performance",
            goals=("efficiency",),
        ),
    }
    signal = harness_autopt.AutoptSignal(
        command="make test",
        returncode=1,
        duration_seconds=12.5,
        stdout_tail="failed",
    )
    request = harness_autopt.build_autopt_request(
        resources=resources,
        resource_id="project-docs",
        goal="consistency",
        trigger_source="codex-session",
        confidence=0.82,
        reason="docs contract failure",
        evidence=("docs contract failed",),
        signals=(signal,),
    )

    assert request.classification.resource_id == "project-docs"
    assert request.constraints.editable_paths == ("README.md",)
    assert request.constraints.excluded_paths == (
        "docs/architecture/decision-records",
    )
    assert request.constraints.max_changed_files == 2
    assert "make test" in request.constraints.validators
    assert "project-docs" in request.candidate_resource_ids
    assert "test-performance" in request.candidate_resource_ids
    assert request.success_criteria


def test_low_confidence_request_is_not_actionable() -> None:
    request = harness_autopt.build_autopt_request(
        resources={"project-docs": _resource()},
        resource_id="project-docs",
        goal="consistency",
        trigger_source="codex-session",
        confidence=0.4,
        reason="weak signal",
        evidence=("ambiguous failure",),
    )

    assert harness_autopt.is_request_actionable(request) is False


def test_agent_controller_prompt_lists_all_resources() -> None:
    prompt = harness_autopt.build_controller_prompt(
        {
            "project-docs": _resource(),
            "test-performance": _resource(
                resource_id="test-performance",
                kind="test_performance",
                goals=("efficiency",),
            ),
        }
    )

    assert "Codex agent is the controller" in prompt
    assert "Sense -> Classify -> Constrain -> Repair -> Verify" in prompt
    assert "Self-Audit Contract" in prompt
    assert "Experience-to-Rule Contract" in prompt
    assert '"project-docs"' in prompt
    assert '"test-performance"' in prompt


def test_repair_prompt_includes_request_constraints_and_evidence() -> None:
    request = harness_autopt.build_autopt_request(
        resources={"project-docs": _resource()},
        resource_id="project-docs",
        goal="consistency",
        trigger_source="codex-session",
        confidence=0.9,
        reason="docs contract failure",
        evidence=("docs contract failed",),
    )

    prompt = harness_autopt.build_repair_prompt(request)

    assert "AutoptRequest" in prompt
    assert "docs contract failed" in prompt
    assert "README.md" in prompt
    assert "make doctor" in prompt
    assert "Do not edit outside editable_paths" in prompt


def test_parser_does_not_accept_manual_target_goal_controls() -> None:
    parser = harness_autopt.build_parser()
    dests = {action.dest for action in parser._actions}

    assert "target" not in dests
    assert "goal" not in dests
    assert "candidate_count" not in dests
    assert "print_controller_prompt" in dests


def test_self_audit_prompt_defines_intensional_retention_question() -> None:
    prompt = harness_autopt.build_self_audit_prompt()

    assert "Self-Audit is not a checklist" in prompt
    assert "Can this experience be compressed" in prompt
    assert "Do not promote raw traces" in prompt
    assert "pending ExperienceCandidate" in prompt
    assert "Plan Mode" in prompt


def test_experience_assessment_detects_controller_responsibility_mix() -> None:
    candidate = harness_autopt.ExperienceCandidate(
        trigger_source="codex-session",
        observation=(
            "Python runner still owns candidate_generation despite Codex "
            "controller responsibility."
        ),
        evidence=("run_candidate_generation called codex-subagent",),
    )

    assessment = harness_autopt.assess_experience_candidate(candidate)

    assert assessment.decision == "code-simplification"
    assert assessment.placement.endswith("harness_autopt.py")
    assert assessment.confidence >= 0.9


def test_experience_assessment_detects_manual_orchestration_failure() -> None:
    candidate = harness_autopt.ExperienceCandidate(
        trigger_source="user-correction",
        observation="A human had to set TARGET/GOAL for autonomous repair.",
        evidence=("manual orchestration is not autonomous",),
    )

    assessment = harness_autopt.assess_experience_candidate(candidate)

    assert assessment.decision == "canonical-rule"
    assert assessment.placement == "docs/ai/repo-contract.md"


def test_experience_to_rule_prompt_includes_candidate_and_assessment() -> None:
    candidate = harness_autopt.ExperienceCandidate(
        trigger_source="codex-session",
        observation="Instruction authority conflict between Markdown files.",
        evidence=("authority conflict",),
    )
    assessment = harness_autopt.assess_experience_candidate(candidate)

    prompt = harness_autopt.build_experience_to_rule_prompt(
        candidate, assessment
    )

    assert "ExperienceCandidate" in prompt
    assert "ExperienceAssessment" in prompt
    assert "canonical-rule" in prompt
    assert "pending ExperienceCandidate" in prompt


def test_build_pr_title_uses_resource_and_goal() -> None:
    resource = harness_autopt.HarnessResource(
        id="project-docs",
        kind="documentation",
        authority="canonical",
        paths=("README.md",),
        mutable_paths=("README.md",),
        validators=("make test",),
    )

    assert (
        harness_autopt.build_pr_title(resource, "consistency")
        == "[harness-autopt] improve project-docs consistency"
    )


def test_build_pr_create_command_uses_draft_flag() -> None:
    command = harness_autopt.build_pr_create_command(
        title="[harness-autopt] improve project-docs consistency",
        body="body",
        base="main",
        head="autopt/project-docs-1",
        draft=True,
    )

    assert command[:3] == ["gh", "pr", "create"]
    assert "--draft" in command


def test_guarded_pr_requires_explicit_opt_in() -> None:
    resource = harness_autopt.HarnessResource(
        id="project-docs",
        kind="documentation",
        authority="canonical",
        paths=("README.md",),
        mutable_paths=("README.md",),
        validators=("make test",),
        mutation_policy="guarded_pr",
    )

    assert harness_autopt.is_pr_creation_allowed(resource, False) is False
    assert harness_autopt.is_pr_creation_allowed(resource, True) is True


def test_build_pr_body_omits_raw_prompt_and_output() -> None:
    resource = harness_autopt.HarnessResource(
        id="codex-subagent",
        kind="skill",
        authority="canonical",
        paths=("x",),
        mutable_paths=("x",),
        validators=("make test",),
    )
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/codex-subagent-20260424-run1",
        worktree=Path("/tmp/worktree"),
        resource_id="codex-subagent",
        goal="stability",
    )
    state.record("candidate_generation", stdout_tail="SECRET_PROMPT")
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("tests/codex_subagent/test_x.py",),
        changed_lines=12,
    )

    body = harness_autopt.build_pr_body(
        state=state,
        resource=resource,
        diff_guard=diff_guard,
        gate_commands=("make test",),
    )

    assert "run-1" in body
    assert "SECRET_PROMPT" not in body
    assert "`make test`: pass" in body


def test_autopt_state_omits_raw_prompt_and_output_payloads() -> None:
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/codex-subagent-20260424-run1",
        worktree=Path("/tmp/worktree"),
        resource_id="codex-subagent",
        goal="stability",
    )

    state.record(
        "gate",
        stdout_tail="SECRET_PROMPT",
        stderr_tail="RAW_MODEL_OUTPUT",
        returncode=0,
    )

    event = state.events[0]
    assert "stdout_tail" not in event
    assert "stderr_tail" not in event
    assert event["stdout_tail_omitted"] is True
    assert event["stderr_tail_omitted"] is True
    assert event["returncode"] == 0
