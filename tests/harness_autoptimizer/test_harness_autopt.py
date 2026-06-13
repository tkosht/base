from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".agents" / "skills" / "harness-autoptimizer" / "scripts"
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


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], Path, bool]] = []

    def run(
        self,
        cmd: list[str],
        cwd: Path,
        *,
        check: bool = False,
    ) -> harness_autopt.CommandResult:
        self.calls.append((cmd, cwd, check))
        if cmd[:3] == ["gh", "pr", "create"]:
            return harness_autopt.CommandResult(
                0, "https://example.test/pull/1\n", ""
            )
        return harness_autopt.CommandResult(0, "", "")


def test_load_resource_registry_includes_codex_subagent() -> None:
    resources = harness_autopt.load_resource_registry(
        ROOT / "docs" / "architecture" / "harness-resources.toml"
    )

    resource = resources["codex-subagent"]
    assert resource.kind == "skill"
    assert "make test" in resource.validators
    assert ".agents/skills/codex-subagent" in resource.mutable_paths


def test_autoptimizer_prompts_require_manager_leaf_dag_team() -> None:
    prompt_dir = (
        ROOT / ".agents" / "skills" / "harness-autoptimizer" / "prompts"
    )
    auto_controller = (prompt_dir / "auto-controller.md").read_text(
        encoding="utf-8"
    )
    repair_request = (prompt_dir / "repair-request.md").read_text(
        encoding="utf-8"
    )

    combined = auto_controller + "\n" + repair_request

    assert 'team_policy: "manager_leaf_v1"' in combined
    assert "DAG-managed team" in combined
    assert "manager-only" in combined
    assert "leaf" in combined


def test_skill_workflow_delegates_actual_work_to_leaf_nodes() -> None:
    skill_text = (
        ROOT / ".agents" / "skills" / "harness-autoptimizer" / "SKILL.md"
    ).read_text(encoding="utf-8")
    workflow = skill_text.split("## Workflow", 1)[1].split(
        "## Controller Prompts", 1
    )[0]

    assert "Repair: Codex agent 自身が" not in workflow
    assert "Review: Codex agent 自身が" not in workflow
    assert 'team_policy: "manager_leaf_v1"' in workflow
    assert "repair leaf node" in workflow
    assert "verify leaf node" in workflow
    assert "review leaf node" in workflow
    assert "manager-only" in workflow
    assert "blocked reason" in workflow
    assert "代行せず" in workflow


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
        (".agents/skills/codex-subagent/SKILL.md", True),
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
        ".agents/skills/codex-subagent",
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
    assert (
        "Sense -> Classify -> Constrain -> Repair -> Verify -> Review"
        in prompt
    )
    assert "requirements, implementation, prompts, tests" in prompt
    assert "unresolved findings are stop reasons" in prompt
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
    assert "self-review pass" in prompt
    assert "helper boundaries" in prompt


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


def test_create_pull_request_rejects_unconverged_review_report(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    resource = _resource(resource_id="harness-autoptimizer")
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/harness-autoptimizer-20260427-run1",
        worktree=tmp_path,
        resource_id="harness-autoptimizer",
        goal="self-audit",
    )
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("tests/harness_autoptimizer/test_harness_autopt.py",),
        changed_lines=1,
    )
    review_report = harness_autopt.ReviewReport(
        loop_count=1,
        findings=(),
        convergence_conditions=("material findings unresolved",),
        converged=False,
        stop_reason="material findings unresolved",
    )

    with pytest.raises(RuntimeError, match="ReviewReport must be converged"):
        harness_autopt.create_pull_request(
            runner,
            tmp_path,
            state,
            resource,
            diff_guard,
            "main",
            review_report,
            draft=True,
        )

    assert runner.calls == []


def test_create_pull_request_includes_converged_review_report(
    tmp_path: Path,
) -> None:
    runner = RecordingRunner()
    resource = _resource(resource_id="harness-autoptimizer")
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/harness-autoptimizer-20260427-run1",
        worktree=tmp_path,
        resource_id="harness-autoptimizer",
        goal="self-audit",
    )
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("tests/harness_autoptimizer/test_harness_autopt.py",),
        changed_lines=1,
    )
    review_report = harness_autopt.build_review_report(
        findings=(
            harness_autopt.ReviewFinding(
                id="review-gate",
                severity="medium",
                material=True,
                status="fixed",
                verification_class="test",
                summary="PR creation requires converged review report",
            ),
        ),
        loop_count=2,
        gate_passed=True,
        diff_guard=diff_guard,
        self_audit_completed=True,
    )

    url = harness_autopt.create_pull_request(
        runner,
        tmp_path,
        state,
        resource,
        diff_guard,
        "origin/main",
        review_report,
        draft=True,
    )

    gh_command = runner.calls[-1][0]
    body = gh_command[gh_command.index("--body") + 1]
    assert url == "https://example.test/pull/1"
    assert "--draft" in gh_command
    assert "## Review Loop" in body
    assert "loop count: 2" in body
    assert "converged: true" in body


def test_review_report_converges_when_material_findings_are_closed() -> None:
    finding = harness_autopt.ReviewFinding(
        id="repo-identity",
        severity="high",
        material=True,
        status="fixed",
        verification_class="validator",
        summary="legacy repo identity removed",
        evidence=("make doctor",),
    )
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("scripts/ci/validate_template.py",),
        changed_lines=12,
    )

    report = harness_autopt.build_review_report(
        findings=(finding,),
        loop_count=2,
        gate_passed=True,
        diff_guard=diff_guard,
        self_audit_completed=True,
    )

    assert harness_autopt.is_review_converged(report) is True
    assert report.stop_reason == "converged"
    assert "material findings resolved" in report.convergence_conditions


def test_review_report_rejects_unresolved_material_finding() -> None:
    finding = harness_autopt.ReviewFinding(
        id="review-loop",
        severity="medium",
        material=True,
        status="unresolved",
        verification_class="manual_review",
        summary="loop evidence was not recorded",
    )
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("tests/harness_autoptimizer/test_harness_autopt.py",),
        changed_lines=8,
    )

    report = harness_autopt.build_review_report(
        findings=(finding,),
        loop_count=1,
        gate_passed=True,
        diff_guard=diff_guard,
        self_audit_completed=True,
    )

    assert report.converged is False
    assert report.stop_reason == "material findings unresolved"


def test_review_report_allows_non_material_deferred_finding() -> None:
    finding = harness_autopt.ReviewFinding(
        id="later-cleanup",
        severity="low",
        material=False,
        status="deferred",
        verification_class="manual_review",
        summary="follow-up cleanup can be handled separately",
    )
    diff_guard = harness_autopt.DiffGuardResult(
        ok=True,
        changed_files=("docs/ai/skills/harness-autoptimizer.md",),
        changed_lines=4,
    )

    report = harness_autopt.build_review_report(
        findings=(finding,),
        loop_count=1,
        gate_passed=True,
        diff_guard=diff_guard,
        self_audit_completed=True,
    )

    assert report.converged is True


def test_proactive_review_probe_detects_non_target_resource_issue(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    adjacent = tmp_path / "adjacent"
    target.mkdir()
    adjacent.mkdir()
    (target / "SKILL.md").write_text("current target\n", encoding="utf-8")
    (adjacent / "SKILL.md").write_text(
        "docs/architecture/base-" + "harness-set.md\n",
        encoding="utf-8",
    )
    resources = {
        "harness-autoptimizer": harness_autopt.HarnessResource(
            id="harness-autoptimizer",
            kind="skill",
            authority="canonical",
            paths=("target",),
            mutable_paths=("target",),
            validators=("make test",),
        ),
        "codex-subagent": harness_autopt.HarnessResource(
            id="codex-subagent",
            kind="skill",
            authority="canonical",
            paths=("adjacent",),
            mutable_paths=("adjacent",),
            validators=("make test",),
        ),
    }
    probe = harness_autopt.ProactiveReviewProbe(
        id="deleted-reference",
        summary="deleted reference remains in registry resource",
        needles=("docs/architecture/base-" + "harness-set.md",),
    )

    findings = harness_autopt.run_proactive_review_probes(
        tmp_path,
        resources,
        (probe,),
        target_resource_id="harness-autoptimizer",
    )
    report = harness_autopt.build_review_report(
        findings=findings,
        loop_count=1,
        gate_passed=True,
        diff_guard=harness_autopt.DiffGuardResult(
            ok=True,
            changed_files=("target/SKILL.md",),
            changed_lines=1,
        ),
        self_audit_completed=True,
    )

    assert len(findings) == 1
    assert findings[0].status == "out_of_scope"
    assert findings[0].material is True
    assert "resource=codex-subagent" in findings[0].evidence
    assert report.converged is False
    assert report.stop_reason == "material findings unresolved"


def test_proactive_review_probe_marks_target_issue_unresolved(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "SKILL.md").write_text("legacy marker\n", encoding="utf-8")
    resources = {
        "harness-autoptimizer": harness_autopt.HarnessResource(
            id="harness-autoptimizer",
            kind="skill",
            authority="canonical",
            paths=("target",),
            mutable_paths=("target",),
            validators=("make test",),
        )
    }
    probe = harness_autopt.ProactiveReviewProbe(
        id="legacy-marker",
        summary="legacy marker remains",
        needles=("legacy marker",),
    )

    findings = harness_autopt.run_proactive_review_probes(
        tmp_path,
        resources,
        (probe,),
        target_resource_id="harness-autoptimizer",
    )

    assert len(findings) == 1
    assert findings[0].status == "unresolved"


def test_proactive_review_probe_respects_resource_excluded_paths(
    tmp_path: Path,
) -> None:
    active = tmp_path / "docs" / "active"
    excluded = tmp_path / "docs" / "decision-records"
    active.mkdir(parents=True)
    excluded.mkdir(parents=True)
    (active / "current.md").write_text("current docs\n", encoding="utf-8")
    (excluded / "historical.md").write_text(
        "docs/architecture/base-" + "harness-set.md\n",
        encoding="utf-8",
    )
    resources = {
        "knowledge-docs": harness_autopt.HarnessResource(
            id="knowledge-docs",
            kind="knowledge_docs",
            authority="canonical",
            paths=("docs",),
            mutable_paths=("docs",),
            validators=("make test",),
            excluded_paths=("docs/decision-records",),
        )
    }
    probe = harness_autopt.ProactiveReviewProbe(
        id="deleted-reference",
        summary="deleted reference remains in registry resource",
        needles=("docs/architecture/base-" + "harness-set.md",),
    )

    findings = harness_autopt.run_proactive_review_probes(
        tmp_path,
        resources,
        (probe,),
        target_resource_id="knowledge-docs",
    )

    assert findings == ()


def test_review_finding_uses_verification_class_not_command() -> None:
    finding = harness_autopt.ReviewFinding(
        id="validator-coverage",
        severity="medium",
        material=True,
        status="fixed",
        verification_class="test",
        summary="regression is covered by a test class",
    )

    assert finding.verification_class == "test"
    assert not hasattr(finding, "command")


def test_write_review_report_omits_raw_trace_payloads(tmp_path: Path) -> None:
    finding = harness_autopt.ReviewFinding(
        id="raw-trace",
        severity="high",
        material=True,
        status="fixed",
        verification_class="manual_review",
        summary="raw_prompt SECRET_PROMPT",
        evidence=("raw_output=RAW_MODEL_OUTPUT", "safe evidence"),
    )
    report = harness_autopt.build_review_report(
        findings=(finding,),
        loop_count=1,
        gate_passed=True,
        diff_guard=harness_autopt.DiffGuardResult(
            ok=True,
            changed_files=("README.md",),
            changed_lines=1,
        ),
        self_audit_completed=True,
    )

    path = harness_autopt.write_review_report(tmp_path, "run-1", report)
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_json = json.dumps(payload)

    assert payload["findings"][0]["summary"] == "[omitted raw trace]"
    assert "safe evidence" in payload["findings"][0]["evidence"]
    assert "SECRET_PROMPT" not in raw_json
    assert "RAW_MODEL_OUTPUT" not in raw_json


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


def test_build_pr_body_includes_review_loop_summary() -> None:
    resource = harness_autopt.HarnessResource(
        id="harness-autoptimizer",
        kind="skill",
        authority="canonical",
        paths=("x",),
        mutable_paths=("x",),
        validators=("make test",),
    )
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/harness-autoptimizer-20260424-run1",
        worktree=Path("/tmp/worktree"),
        resource_id="harness-autoptimizer",
        goal="self-audit",
    )
    report = harness_autopt.build_review_report(
        findings=(
            harness_autopt.ReviewFinding(
                id="loop-report",
                severity="medium",
                material=True,
                status="fixed",
                verification_class="test",
                summary="review loop is structured",
            ),
        ),
        loop_count=3,
        gate_passed=True,
        diff_guard=harness_autopt.DiffGuardResult(
            ok=True,
            changed_files=(
                "tests/harness_autoptimizer/test_harness_autopt.py",
            ),
            changed_lines=20,
        ),
        self_audit_completed=True,
    )

    body = harness_autopt.build_pr_body(
        state=state,
        resource=resource,
        diff_guard=harness_autopt.DiffGuardResult(
            ok=True,
            changed_files=(
                "tests/harness_autoptimizer/test_harness_autopt.py",
            ),
            changed_lines=20,
        ),
        gate_commands=("make test",),
        review_report=report,
    )

    assert "## Review Loop" in body
    assert "loop count: 3" in body
    assert "finding status: fixed: 1" in body


def test_build_pr_body_omits_raw_trace_from_review_stop_reason() -> None:
    resource = harness_autopt.HarnessResource(
        id="harness-autoptimizer",
        kind="skill",
        authority="canonical",
        paths=("x",),
        mutable_paths=("x",),
        validators=("make test",),
    )
    state = harness_autopt.AutoptState(
        run_id="run-1",
        branch="autopt/harness-autoptimizer-20260424-run1",
        worktree=Path("/tmp/worktree"),
        resource_id="harness-autoptimizer",
        goal="self-audit",
    )
    report = harness_autopt.ReviewReport(
        loop_count=1,
        findings=(),
        convergence_conditions=("raw traces omitted",),
        converged=False,
        stop_reason="raw_output SECRET_PROMPT",
    )

    body = harness_autopt.build_pr_body(
        state=state,
        resource=resource,
        diff_guard=harness_autopt.DiffGuardResult(
            ok=True,
            changed_files=(
                "tests/harness_autoptimizer/test_harness_autopt.py",
            ),
            changed_lines=20,
        ),
        gate_commands=("make test",),
        review_report=report,
    )

    assert "[omitted raw trace]" in body
    assert "SECRET_PROMPT" not in body


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
