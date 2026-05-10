from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.ci.repo_copy import copy_repo_for_test
from scripts.ci.validate_template import (
    DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT,
    DESIGN_CHECKLIST_UPDATE_CONTRACT,
    DESIGN_READ_FIRST_CONTRACT,
    DESIGN_README_MIN_ROLE,
    DESIGN_README_SYNC_REF,
    run_checks,
)

ROOT = Path(__file__).resolve().parents[1]


def _copy_repo(tmp_path: Path) -> Path:
    return copy_repo_for_test(ROOT, tmp_path)


def test_copy_repo_prunes_runtime_and_dependency_dirs(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)

    for rel in (
        ".git",
        ".env",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "node_modules",
    ):
        assert not (repo / rel).exists(), rel
    assert (repo / ".env.example").exists()
    assert (repo / ".codex" / "config.toml").exists()
    assert (repo / ".codex" / "skills").exists()
    assert not (repo / ".codex" / "sessions").exists()
    assert (repo / "secrets" / "README.md").exists()


def test_copy_repo_preserves_placeholders_without_runtime_secrets(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    (source / ".env.local").write_text("TOKEN=secret\n", encoding="utf-8")
    (source / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
    secrets = source / "secrets"
    secrets.mkdir()
    (secrets / "README.md").write_text("# secrets\n", encoding="utf-8")
    (secrets / "token.txt").write_text("secret\n", encoding="utf-8")

    repo = copy_repo_for_test(source, tmp_path)

    assert not (repo / ".env").exists()
    assert not (repo / ".env.local").exists()
    assert (repo / ".env.example").exists()
    assert (repo / "secrets" / "README.md").exists()
    assert not (repo / "secrets" / "token.txt").exists()


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _append_text(path: Path, text: str) -> None:
    original = path.read_text(encoding="utf-8")
    path.write_text(original + text, encoding="utf-8")


def _write_design_doc(path: Path, body: str) -> None:
    if path.name == "README.md" and path.parent.name == "design":
        content = (
            "# Design Guidance\n\n"
            f"{DESIGN_README_MIN_ROLE}\n\n"
            f"{DESIGN_README_SYNC_REF}\n\n"
            f"{body}\n"
        )
    else:
        content = f"# Design\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def test_template_contract_checks_pass() -> None:
    assert run_checks(ROOT) == []


def test_template_contract_checks_pass_for_workspace_write(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    config = repo / ".codex" / "config.toml"
    _replace_once(
        config,
        'sandbox_mode = "danger-full-access"',
        'sandbox_mode = "workspace-write"',
    )

    assert run_checks(repo) == []


def test_template_contract_checks_fail_when_git_mainbranch_worktree_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill = repo / ".claude" / "skills" / "git-mainbranch" / "SKILL.md"
    _replace_once(skill, "skipped_worktrees", "skipped-worktrees")
    _replace_once(skill, "skipped_worktrees", "skipped-worktrees")

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/SKILL.md "
        "missing cleanup contract: skipped_worktrees"
    ) in errors


def test_template_contract_checks_fail_when_git_mainbranch_playbook_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    playbook = (
        repo
        / ".claude"
        / "skills"
        / "git-mainbranch"
        / "references"
        / "mainbranch-playbook.md"
    )
    _replace_once(
        playbook,
        "Worktree Cleanup Before Branch Deletion",
        "Worktree Cleanup Removed",
    )

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/references/mainbranch-playbook.md "
        "missing cleanup contract: Worktree Cleanup Before Branch Deletion"
    ) in errors


def test_template_contract_checks_fail_when_git_mainbranch_squash_candidate_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill = repo / ".claude" / "skills" / "git-mainbranch" / "SKILL.md"
    _replace_once(
        skill,
        'gh pr list --state merged --search "head:<branch>"',
        'gh pr list --state merged --search "removed:<branch>"',
    )

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/SKILL.md "
        'missing cleanup contract: gh pr list --state merged --search "head:<branch>" '
        "--json number,state,mergedAt,headRefName"
    ) in errors


def test_template_contract_checks_fail_when_git_mainbranch_remote_gone_evidence_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill = repo / ".claude" / "skills" / "git-mainbranch" / "SKILL.md"
    _replace_once(skill, "upstream が gone", "upstream を確認")

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/SKILL.md "
        "missing cleanup contract: upstream が gone のローカルブランチ"
    ) in errors


def test_template_contract_checks_fail_when_git_mainbranch_force_delete_guard_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill = repo / ".claude" / "skills" / "git-mainbranch" / "SKILL.md"
    _replace_once(
        skill,
        "PR merge、remote branch gone、worktree 削除済みを確認し",
        "PR merge を確認し",
    )

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/SKILL.md "
        "missing cleanup contract: PR merge、remote branch gone、worktree 削除済みを確認し"
    ) in errors


def test_template_contract_checks_fail_when_git_mainbranch_playbook_remote_gone_and_pr_merge_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    playbook = (
        repo
        / ".claude"
        / "skills"
        / "git-mainbranch"
        / "references"
        / "mainbranch-playbook.md"
    )
    _replace_once(
        playbook,
        "remote branch gone と PR merge の両方を確認でき",
        "PR merge を確認でき",
    )

    errors = run_checks(repo)

    assert (
        ".claude/skills/git-mainbranch/references/mainbranch-playbook.md "
        "missing cleanup contract: remote branch gone と PR merge の両方"
    ) in errors


def test_template_contract_checks_fail_when_workspace_network_enabled(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    config = repo / ".codex" / "config.toml"
    _replace_once(
        config,
        'sandbox_mode = "danger-full-access"',
        'sandbox_mode = "workspace-write"',
    )
    _replace_once(config, "network_access = false", "network_access = true")

    errors = run_checks(repo)

    assert (
        ".codex/config.toml must keep "
        "sandbox_workspace_write.network_access = false "
        'when approval_policy = "never" is shipped'
    ) in errors


def test_template_contract_checks_fail_for_unsupported_sandbox_mode(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    config = repo / ".codex" / "config.toml"
    _replace_once(
        config,
        'sandbox_mode = "danger-full-access"',
        'sandbox_mode = "read-only"',
    )

    errors = run_checks(repo)

    assert (
        ".codex/config.toml must keep sandbox_mode in "
        '{"danger-full-access", "workspace-write"} '
        'when approval_policy = "never" is shipped'
    ) in errors


def test_template_contract_checks_fail_when_full_access_guidance_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    security_doc = repo / "docs" / "standards" / "security.md"
    _replace_once(
        security_doc,
        'sandbox_mode = "danger-full-access"',
        'sandbox_mode = "danger-full-access-removed"',
    )

    errors = run_checks(repo)

    assert (
        "docs/standards/security.md missing Codex shared default contract: "
        'sandbox_mode = "danger-full-access"'
    ) in errors


def test_template_contract_checks_fail_when_project_docs_resource_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    registry = repo / "docs" / "architecture" / "harness-resources.toml"
    _replace_once(registry, 'id = "project-docs"', 'id = "project-docs-old"')

    errors = run_checks(repo)

    assert "missing harness resource: project-docs" in errors


def test_template_contract_checks_fail_when_project_docs_path_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    registry = repo / "docs" / "architecture" / "harness-resources.toml"
    marker = 'id = "project-docs"'
    text = registry.read_text(encoding="utf-8")
    head, tail = text.split(marker, 1)
    tail = tail.replace('  "README.md",\n', "", 2)
    registry.write_text(head + marker + tail, encoding="utf-8")

    errors = run_checks(repo)

    assert "project-docs missing path: README.md" in errors
    assert "project-docs missing mutable path: README.md" in errors


def test_template_contract_checks_fail_when_knowledge_docs_exclusion_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    registry = repo / "docs" / "architecture" / "harness-resources.toml"
    _replace_once(
        registry,
        '  "docs/architecture/decision-records",',
        '  "docs/architecture/decision-records-old",',
    )

    errors = run_checks(repo)

    assert (
        "knowledge-docs must exclude docs/architecture/decision-records"
    ) in errors


def test_template_contract_checks_fail_for_unbounded_repo_copy(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    contract_test = repo / "tests" / "test_template_contract.py"
    _replace_once(
        contract_test,
        "return copy_repo_for_test(ROOT, tmp_path)",
        "return shutil.copytree(ROOT, tmp_path / 'repo', symlinks=True)",
    )

    errors = run_checks(repo)

    assert (
        "tests/test_template_contract.py copies ROOT with "
        "shutil.copytree without ignore"
    ) in errors


def test_template_contract_checks_fail_when_autopt_prompt_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    prompt = (
        repo
        / ".claude"
        / "skills"
        / "harness-autoptimizer"
        / "prompts"
        / "auto-controller.md"
    )
    prompt.unlink()

    errors = run_checks(repo)

    assert (
        "missing required path: "
        ".claude/skills/harness-autoptimizer/prompts/auto-controller.md"
    ) in errors


def test_template_contract_checks_fail_when_self_audit_prompt_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    prompt = (
        repo
        / ".claude"
        / "skills"
        / "harness-autoptimizer"
        / "prompts"
        / "self-audit.md"
    )
    prompt.unlink()

    errors = run_checks(repo)

    assert (
        "missing required path: "
        ".claude/skills/harness-autoptimizer/prompts/self-audit.md"
    ) in errors


def test_template_contract_checks_fail_when_experience_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    experience = repo / "docs" / "ai" / "experience-capture.md"
    experience.unlink()

    errors = run_checks(repo)

    assert "missing required path: docs/ai/experience-capture.md" in errors


def test_template_contract_checks_fail_when_autopt_helper_keeps_candidate_runner(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    helper = (
        repo
        / ".claude"
        / "skills"
        / "harness-autoptimizer"
        / "scripts"
        / "harness_autopt.py"
    )
    _append_text(helper, "\ndef run_candidate_generation():\n    pass\n")

    errors = run_checks(repo)

    assert (
        "harness_autopt.py must not keep Python-runner control path: "
        "def run_candidate_generation"
    ) in errors


def test_template_contract_checks_fail_when_makefile_keeps_autopt_target(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    makefile = repo / "Makefile"
    _append_text(
        makefile,
        "\nharness-autopt:\n\tTARGET=project-docs GOAL=consistency echo bad\n",
    )

    errors = run_checks(repo)

    assert (
        "Makefile must not expose TARGET/GOAL harness-autopt entrypoint"
        in errors
    )


def test_template_contract_checks_fail_when_autopt_workflow_missing_codex_agent(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    workflow = repo / ".github" / "workflows" / "harness-autopt.yml"
    _replace_once(workflow, "codex_exec.py", "python_runner_only.py")

    errors = run_checks(repo)

    assert (
        "harness-autopt workflow must start a Codex agent controller" in errors
    )


def test_template_contract_checks_fail_when_autopt_review_contract_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill = repo / ".claude" / "skills" / "harness-autoptimizer" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            "ReviewReport", "StructuredReviewRemoved"
        ),
        encoding="utf-8",
    )

    errors = run_checks(repo)

    assert (
        ".claude/skills/harness-autoptimizer/SKILL.md "
        "missing controller contract: ReviewReport"
    ) in errors


def test_template_contract_checks_fail_when_github_helper_targets_base(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    helper = repo / "bin" / "github_api_pr.sh"
    helper.write_text(
        "#!/usr/bin/env bash\nOWNER=" + "tkosht\nREPO=" + "base\n",
        encoding="utf-8",
    )

    errors = run_checks(repo)

    assert (
        "bin/github_api_pr.sh must not hard-code base repo: REPO=" + "base"
    ) in errors


def test_template_contract_checks_fail_when_github_helper_is_not_dynamic(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    helper = repo / "bin" / "github_api_pr.sh"
    text = helper.read_text(encoding="utf-8")
    helper.write_text(
        text.replace("GITHUB_REPOSITORY", "GH_REPOSITORY_REMOVED"),
        encoding="utf-8",
    )

    errors = run_checks(repo)

    assert (
        "bin/github_api_pr.sh must resolve owner/repo dynamically: "
        "GITHUB_REPOSITORY"
    ) in errors


def test_template_contract_checks_fail_when_grill_me_doc_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill_doc = repo / "docs" / "ai" / "skills" / "grill-me.md"
    skill_doc.unlink()

    errors = run_checks(repo)

    assert "missing required path: docs/ai/skills/grill-me.md" in errors


def test_template_contract_checks_fail_when_grill_me_skill_dir_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    shutil.rmtree(repo / ".claude" / "skills" / "grill-me")

    errors = run_checks(repo)

    assert (
        "unexpected .claude/skills layout: ai-agent-collaboration-exec, "
        "codex-subagent, dependabot-pr-maintainer, "
        "git-commit-pr, git-mainbranch, "
        "grill-me-essential-first, harness-autoptimizer, "
        "repo-instruction-optimizer, repo-template-specializer, "
        "skill-authoring"
    ) in errors


def test_template_contract_checks_fail_when_grill_me_essential_first_doc_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    skill_doc = repo / "docs" / "ai" / "skills" / "grill-me-essential-first.md"
    skill_doc.unlink()

    errors = run_checks(repo)

    assert (
        "missing required path: docs/ai/skills/grill-me-essential-first.md"
    ) in errors


def test_template_contract_checks_fail_when_grill_me_essential_first_skill_dir_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    shutil.rmtree(repo / ".claude" / "skills" / "grill-me-essential-first")

    errors = run_checks(repo)

    assert (
        "unexpected .claude/skills layout: ai-agent-collaboration-exec, "
        "codex-subagent, dependabot-pr-maintainer, "
        "git-commit-pr, git-mainbranch, grill-me, harness-autoptimizer, "
        "repo-instruction-optimizer, repo-template-specializer, "
        "skill-authoring"
    ) in errors


def test_template_contract_checks_fail_when_grill_me_essential_first_agent_entrypoint_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    (repo / ".agents" / "skills" / "grill-me-essential-first").unlink()

    errors = run_checks(repo)

    assert (
        "unexpected .agents/skills layout: ai-agent-collaboration-exec, "
        "codex-subagent, dependabot-pr-maintainer, "
        "git-commit-pr, git-mainbranch, grill-me, harness-autoptimizer, "
        "repo-instruction-optimizer, repo-template-specializer, "
        "skill-authoring"
    ) in errors


def test_template_contract_checks_fail_when_grill_me_essential_first_codex_entrypoint_is_missing(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    (repo / ".codex" / "skills" / "grill-me-essential-first").unlink()

    errors = run_checks(repo)

    assert (
        "unexpected .codex/skills layout: ai-agent-collaboration-exec, "
        "codex-subagent, dependabot-pr-maintainer, "
        "git-commit-pr, git-mainbranch, grill-me, harness-autoptimizer, "
        "repo-instruction-optimizer, repo-template-specializer, "
        "skill-authoring"
    ) in errors


def test_template_contract_checks_fail_when_non_root_design_md_is_added(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    extra_design = repo / "docs" / "extra" / "DESIGN.md"
    extra_design.parent.mkdir(parents=True, exist_ok=True)
    extra_design.write_text("# stray design doc\n", encoding="utf-8")

    errors = run_checks(repo)

    assert ("non-root DESIGN.md is forbidden: docs/extra/DESIGN.md") in errors


def test_template_contract_checks_fail_when_design_read_first_is_removed(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    contract = repo / "docs" / "ai" / "repo-contract.md"
    _replace_once(
        contract, DESIGN_READ_FIRST_CONTRACT, "design guidance removed"
    )

    errors = run_checks(repo)

    assert (
        "docs/ai/repo-contract.md missing design contract: "
        + DESIGN_READ_FIRST_CONTRACT
    ) in errors


def test_template_contract_checks_fail_when_design_readme_role_is_removed(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    design_readme = repo / "docs" / "design" / "README.md"
    _replace_once(
        design_readme,
        DESIGN_README_MIN_ROLE,
        "design guidance role removed",
    )

    errors = run_checks(repo)

    assert (
        "docs/design/README.md missing design guidance contract: "
        + DESIGN_README_MIN_ROLE
    ) in errors


def test_template_contract_checks_fail_when_design_readme_sync_ref_is_removed(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    design_readme = repo / "docs" / "design" / "README.md"
    _replace_once(
        design_readme,
        DESIGN_README_SYNC_REF,
        "sync reference removed",
    )

    errors = run_checks(repo)

    assert (
        "docs/design/README.md missing design guidance contract: "
        + DESIGN_README_SYNC_REF
    ) in errors


def test_template_contract_checks_fail_when_design_checklist_update_is_removed(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    contract = repo / "docs" / "ai" / "repo-contract.md"
    _replace_once(
        contract,
        DESIGN_CHECKLIST_UPDATE_CONTRACT,
        "design checklist update removed",
    )

    errors = run_checks(repo)

    assert (
        "docs/ai/repo-contract.md missing design contract: "
        + DESIGN_CHECKLIST_UPDATE_CONTRACT
    ) in errors


def test_template_contract_checks_fail_when_design_checklist_supplement_is_removed(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    contract = repo / "docs" / "ai" / "repo-contract.md"
    _replace_once(
        contract,
        DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT,
        "design checklist supplement removed",
    )

    errors = run_checks(repo)

    assert (
        "docs/ai/repo-contract.md missing design contract: "
        + DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT
    ) in errors


def test_template_contract_checks_fail_when_workflow_loses_root_design_path(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    workflow = repo / ".github" / "workflows" / "ci.yml"
    _replace_once(workflow, "      - 'DESIGN.md'\n", "")

    errors = run_checks(repo)

    assert (
        ".github/workflows/ci.yml missing workflow path coverage for DESIGN.md "
        "in paths section 1"
    ) in errors


def test_template_contract_checks_fail_when_workflow_loses_design_docs_path(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    workflow = repo / ".github" / "workflows" / "template-health.yml"
    _replace_once(workflow, '      - "docs/**"', '      - "docs-nope/**"')

    errors = run_checks(repo)

    assert (
        ".github/workflows/template-health.yml missing workflow path coverage "
        "for docs/design/** in paths section 1"
    ) in errors


@pytest.mark.parametrize(
    ("rel", "term", "body"),
    [
        (
            "DESIGN.md",
            "B2B",
            "B2B の導線を先に置く。\nB2B の比較表を先に読む。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "LP",
            "LP を短く保つ。\nLP の hero で結論を先に出す。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "CTA",
            "CTA を hero に置く。\nCTA を footer にも置く。",
        ),
        (
            "docs/design/README.md",
            "UI",
            "UI は略語のまま書かない。\nUI は反復時だけ使う。",
        ),
    ],
)
def test_design_terms_fail_without_expansion(
    tmp_path: Path,
    rel: str,
    term: str,
    body: str,
) -> None:
    repo = _copy_repo(tmp_path)
    _write_design_doc(repo / rel, body)

    errors = run_checks(repo)

    assert f"{rel} uses {term} without an approved expansion" in errors


def test_design_terms_fail_when_ui_is_used_only_once(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    design_readme = repo / "docs" / "design" / "README.md"
    _append_text(
        design_readme,
        "\nユーザーインターフェース（UI）の説明を追加する。\n",
    )

    errors = run_checks(repo)

    assert (
        "docs/design/README.md uses UI only once; spell it out instead of abbreviating"
    ) in errors


@pytest.mark.parametrize(
    ("rel", "body"),
    [
        (
            "DESIGN.md",
            "企業間取引（B2B）の比較表を先に置く。\nB2B の導線は hero で明示する。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "ランディングページ（LP）の導線を一つに絞る。\nLP の中腹で proof を追加する。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "行動喚起（CTA）は hero と footer に置く。\nCTA の文言は行動を明確にする。",
        ),
        (
            "docs/design/README.md",
            "ユーザーインターフェース（UI）の語は具体値と一緒に使う。\nUI の状態差分は component state まで書く。",
        ),
    ],
)
def test_design_terms_accept_repeated_abbreviation_usage(
    tmp_path: Path,
    rel: str,
    body: str,
) -> None:
    repo = _copy_repo(tmp_path)
    _write_design_doc(repo / rel, body)

    assert run_checks(repo) == []


@pytest.mark.parametrize(
    ("rel", "body"),
    [
        (
            "DESIGN.md",
            "企業間取引の比較表を先に置く。\n企業間取引の要点を短く保つ。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "ランディングページの主張を一つに絞る。\nランディングページの主導線は二択までに抑える。",
        ),
        (
            "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
            "行動喚起は hero と footer に置く。\n行動喚起の文言は動詞で終える。",
        ),
        (
            "docs/design/README.md",
            "ユーザーインターフェースの語を使うときは具体値も添える。\nユーザーインターフェースの説明は曖昧語で逃げない。",
        ),
    ],
)
def test_design_terms_accept_spelled_out_usage_without_abbreviation(
    tmp_path: Path,
    rel: str,
    body: str,
) -> None:
    repo = _copy_repo(tmp_path)
    _write_design_doc(repo / rel, body)

    assert run_checks(repo) == []


def test_template_contract_checks_fail_when_design_readme_uses_common_term_without_expansion(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    design_readme = repo / "docs" / "design" / "README.md"
    _append_text(design_readme, "\nMCP を追加説明なしで使う。\n")

    errors = run_checks(repo)

    assert (
        "docs/design/README.md uses MCP without an approved expansion"
    ) in errors
