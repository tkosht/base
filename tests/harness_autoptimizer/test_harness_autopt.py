from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / ".claude" / "skills" / "harness-autoptimizer" / "scripts"
sys.path.append(str(SCRIPTS))

import harness_autopt  # noqa: E402


def test_load_resource_registry_includes_codex_subagent() -> None:
    resources = harness_autopt.load_resource_registry(
        ROOT / "docs" / "architecture" / "harness-resources.toml"
    )

    resource = resources["codex-subagent"]
    assert resource.kind == "skill"
    assert "make test" in resource.validators
    assert ".claude/skills/codex-subagent" in resource.mutable_paths


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
        target="codex-subagent",
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
