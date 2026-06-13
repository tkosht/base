from __future__ import annotations

import fnmatch
import re
import subprocess
import tomllib
from pathlib import Path

from scripts.ci.validate_template import REQUIRED_PATHS

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "architecture" / "base-harness-set.toml"
RESOURCE_REGISTRY_PATH = (
    ROOT / "docs" / "architecture" / "harness-resources.toml"
)
PYPROJECT_PATH = ROOT / "pyproject.toml"


def load_manifest() -> dict[str, object]:
    with MANIFEST_PATH.open("rb") as fh:
        return tomllib.load(fh)


def _path_matches_manifest_pattern(pattern: str, path: str) -> bool:
    return (
        path == pattern
        or path.startswith(pattern.rstrip("/") + "/")
        or fnmatch.fnmatchcase(path, pattern)
    )


def _manifest_path_covers_required_path(
    manifest_path: str, required_path: str
) -> bool:
    return (
        required_path == manifest_path
        or required_path.startswith(manifest_path.rstrip("/") + "/")
        or fnmatch.fnmatchcase(required_path, manifest_path)
    )


def test_manifest_exists() -> None:
    assert MANIFEST_PATH.exists()


def test_harness_resource_registry_exists() -> None:
    assert RESOURCE_REGISTRY_PATH.exists()


def test_harness_resource_registry_covers_retained_autoptimizer() -> None:
    registry = tomllib.loads(
        RESOURCE_REGISTRY_PATH.read_text(encoding="utf-8")
    )
    resource_ids = {
        item["id"]
        for item in registry["resources"]
        if isinstance(item, dict) and "id" in item
    }
    assert "codex-subagent" in resource_ids
    assert "harness-autoptimizer" in resource_ids
    assert "instruction-surface" in resource_ids
    assert "knowledge-docs" in resource_ids
    assert "project-docs" in resource_ids
    assert "repo-template-specializer" in resource_ids
    assert "test-performance" in resource_ids


def test_markdown_harness_resources_keep_guardrails() -> None:
    registry = tomllib.loads(
        RESOURCE_REGISTRY_PATH.read_text(encoding="utf-8")
    )
    resources = {
        item["id"]: item
        for item in registry["resources"]
        if isinstance(item, dict) and "id" in item
    }

    project_docs = resources["project-docs"]
    assert project_docs["kind"] == "documentation"
    assert project_docs["mutation_policy"] == "guarded_pr"
    assert "README.md" in project_docs["mutable_paths"]
    assert project_docs["max_changed_files"] == 2
    assert project_docs["max_changed_lines"] == 200

    knowledge_docs = resources["knowledge-docs"]
    assert "docs/architecture/decision-records" in (
        knowledge_docs["excluded_paths"]
    )

    test_performance = resources["test-performance"]
    assert test_performance["kind"] == "test_performance"
    assert test_performance["goals"] == ["efficiency"]
    assert "scripts/ci/repo_copy.py" in test_performance["mutable_paths"]


def test_manifest_paths_match_filesystem() -> None:
    manifest = load_manifest()
    included_paths = manifest["included_paths"]
    excluded_paths = manifest["excluded_paths"]

    assert isinstance(included_paths, list)
    assert isinstance(excluded_paths, list)

    for rel in included_paths:
        assert isinstance(rel, str)
        assert (ROOT / rel).exists(), rel

    for rel in excluded_paths:
        assert isinstance(rel, str)
        assert not (ROOT / rel).exists(), rel


def test_manifest_declares_portable_harness_groups() -> None:
    manifest = load_manifest()
    groups = manifest["portable_harness_groups"]
    assert isinstance(groups, list)

    expected_ids = {
        "agent-instruction-surface",
        "knowledge-and-standards",
        "skill-surface",
        "collaboration-command-docs",
        "harness-registry",
        "validation-and-copy-tools",
        "automation-workflows",
        "ops-scaffold",
        "local-runtime-state",
    }
    by_id = {group["id"]: group for group in groups}
    assert set(by_id) == expected_ids

    expected_tiers = {
        "agent-instruction-surface": "must_copy",
        "knowledge-and-standards": "copy_with_adjustments",
        "skill-surface": "must_copy",
        "collaboration-command-docs": "optional",
        "harness-registry": "must_copy",
        "validation-and-copy-tools": "must_copy",
        "automation-workflows": "copy_with_adjustments",
        "ops-scaffold": "copy_with_adjustments",
        "local-runtime-state": "do_not_copy",
    }
    for group_id, tier in expected_tiers.items():
        assert by_id[group_id]["tier"] == tier

    assert "AGENTS.md" in by_id["agent-instruction-surface"]["paths"]
    assert ".agents/skills" in by_id["skill-surface"]["paths"]
    assert (
        "docs/architecture/harness-resources.toml"
        in by_id["harness-registry"]["paths"]
    )
    local_runtime_paths = by_id["local-runtime-state"]["paths"]
    assert ".codex/auth.json" in local_runtime_paths
    assert ".claude/settings.local.json" in local_runtime_paths
    assert "output" in local_runtime_paths
    assert "tmux-*.log" in local_runtime_paths
    assert by_id["local-runtime-state"]["preserve_paths"] == [
        ".env.example",
        "secrets/README.md",
    ]


def test_portable_harness_group_paths_exist_when_copied() -> None:
    manifest = load_manifest()
    groups = manifest["portable_harness_groups"]
    assert isinstance(groups, list)

    for group in groups:
        assert isinstance(group, dict)
        if group["tier"] == "do_not_copy":
            continue
        paths = group["paths"]
        assert isinstance(paths, list)
        for rel in paths:
            assert isinstance(rel, str)
            assert (ROOT / rel).exists(), (group["id"], rel)


def test_portable_harness_groups_cover_template_required_paths() -> None:
    manifest = load_manifest()
    groups = manifest["portable_harness_groups"]
    assert isinstance(groups, list)

    copy_group_paths = {
        rel
        for group in groups
        if isinstance(group, dict) and group["tier"] != "do_not_copy"
        for rel in group["paths"]
    }
    missing = sorted(
        rel
        for rel in REQUIRED_PATHS
        if not any(
            _manifest_path_covers_required_path(group_path, rel)
            for group_path in copy_group_paths
        )
    )

    assert missing == []


def test_runtime_exclusions_preserve_public_placeholders() -> None:
    manifest = load_manifest()
    included_paths = set(manifest["included_paths"])
    groups = manifest["portable_harness_groups"]
    assert isinstance(groups, list)
    by_id = {group["id"]: group for group in groups}

    local_runtime = by_id["local-runtime-state"]
    do_not_copy_patterns = local_runtime["paths"]
    preserve_paths = set(local_runtime["preserve_paths"])
    expected_preserve_paths = {".env.example", "secrets/README.md"}
    assert expected_preserve_paths <= preserve_paths
    assert expected_preserve_paths <= included_paths

    copyable_paths = set(included_paths)
    for group in groups:
        assert isinstance(group, dict)
        if group["tier"] == "do_not_copy":
            continue
        copyable_paths.update(group["paths"])

    collisions = {
        rel
        for rel in copyable_paths
        for pattern in do_not_copy_patterns
        if _path_matches_manifest_pattern(pattern, rel)
    }
    assert collisions <= preserve_paths


def test_manifest_skills_match_repo_layout() -> None:
    manifest = load_manifest()
    skills = manifest["skills"]
    assert isinstance(skills, list)

    expected = sorted(skills)
    actual_skill_dirs = sorted(
        path.name
        for path in (ROOT / ".agents" / "skills").iterdir()
        if path.is_dir()
    )
    actual_claude_symlinks = sorted(
        path.name
        for path in (ROOT / ".claude" / "skills").iterdir()
        if path.is_symlink()
    )
    actual_codex_symlinks = sorted(
        path.name
        for path in (ROOT / ".codex" / "skills").iterdir()
        if path.is_symlink()
    )

    assert actual_skill_dirs == expected
    assert actual_claude_symlinks == expected
    assert actual_codex_symlinks == expected
    for skill in expected:
        expected_target = Path(f"../../.agents/skills/{skill}")
        assert (
            ROOT / ".claude" / "skills" / skill
        ).readlink() == expected_target
        assert (
            ROOT / ".codex" / "skills" / skill
        ).readlink() == expected_target


def test_manifest_skills_have_canonical_docs() -> None:
    manifest = load_manifest()
    skills = manifest["skills"]
    assert isinstance(skills, list)

    for skill in skills:
        assert isinstance(skill, str)
        assert (
            ROOT / "docs" / "ai" / "skills" / f"{skill}.md"
        ).exists(), skill


def test_git_operation_skills_require_github_https_auth_preflight() -> None:
    common_needles = (
        "GitHub HTTPS authentication preflight",
        "git remote get-url origin",
        "git remote get-url --push origin",
        "fallback",
        "https://github.com/",
        "git@github.com:",
        "ssh://git@github.com/",
        "GitHub HTTPS remote",
        "GitHub SSH remote",
        "gh auth status -h github.com",
        "not logged in",
        "local GitHub HTTPS authentication is known missing",
        "gh auth login -h github.com",
        "HTTPS Git operations",
        "認証済みを確認できた場合だけ次へ進む",
    )
    expectations = {
        ".agents/skills/git-commit-pr/SKILL.md": (
            "コミット、`git push`、`gh pr create` の前に必ず実行する",
            "fetch URL または push URL が `git@github.com:` または "
            "`ssh://git@github.com/`",
            "`gh pr create` には GitHub CLI authentication が必要",
            "コミットせず、push せず、Pull Request（PR）作成もせず停止する",
        ),
        ".agents/skills/git-mainbranch/SKILL.md": (
            "`git fetch --prune`、`git pull --ff-only`、`gh pr list`",
            "`git fetch --prune` と `git pull --ff-only` の認証判定には"
            "必ず fetch URL を使う",
            "`gh pr list` には GitHub CLI authentication が必要",
            "fetch、pull、`gh pr list`、worktree cleanup、branch deletion "
            "を行わず停止する",
        ),
        ".agents/skills/git-mainbranch/references/mainbranch-playbook.md": (
            "`git fetch --prune`、`git pull --ff-only`、`gh pr list`",
            "`git fetch --prune` と `git pull --ff-only` の認証判定には"
            "必ず fetch URL を使う",
            "`gh pr list` には GitHub CLI authentication が必要",
            "fetch、pull、`gh pr list`、worktree cleanup、branch deletion "
            "を行わず停止する",
        ),
    }

    for rel, needles in expectations.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in (*common_needles, *needles):
            assert needle in text, (rel, needle)


def test_manifest_command_docs_and_workflows_exist() -> None:
    manifest = load_manifest()

    for key in ("command_docs", "workflows"):
        values = manifest[key]
        assert isinstance(values, list)
        for rel in values:
            assert isinstance(rel, str)
            assert (ROOT / rel).exists(), rel


def test_only_expected_task_command_docs_remain() -> None:
    manifest = load_manifest()
    command_docs = manifest["command_docs"]
    assert isinstance(command_docs, list)

    expected = sorted(Path(rel).name for rel in command_docs)
    actual = sorted(
        path.name
        for path in (ROOT / ".claude" / "commands" / "tasks").iterdir()
        if path.is_file()
    )
    assert actual == expected


def test_agents_load_map_references_exist() -> None:
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    matches = re.findall(r"`([^`]+)`", agents_text)
    referenced = [
        value for value in matches if "/" in value and "..." not in value
    ]
    for rel in referenced:
        path = ROOT / rel
        assert path.exists(), rel


def test_python_baseline_is_312_everywhere() -> None:
    manifest = load_manifest()
    python_meta = manifest["python"]
    assert isinstance(python_meta, dict)
    assert python_meta["version"] == "3.12"
    assert python_meta["requires_python"] == ">=3.12,<=3.14"

    pyproject_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    assert 'requires-python = ">=3.12,<=3.14"' in pyproject_text
    assert "target-version = ['py312']" in pyproject_text

    workflow_expectations = {
        ".github/workflows/ci.yml": ["python-version: '3.12'"],
        ".github/workflows/template-health.yml": ['python-version: "3.12"'],
        ".github/workflows/claude.yml": ["python-version: '3.12'"],
    }
    for rel, needles in workflow_expectations.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, (rel, needle)


def test_gitignore_tracks_codex_skill_symlinks() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for needle in ("!.codex/skills/", "!.codex/skills/*"):
        assert needle in text


def test_gitignore_keeps_shipped_codex_files_trackable() -> None:
    for rel in (
        ".codex/config.toml",
        ".codex/version.json",
        ".codex/skills/git-commit-pr",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", rel],
            cwd=ROOT,
            check=False,
        )
        assert result.returncode == 1, rel

    ignored_result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", ".codex/auth.json"],
        cwd=ROOT,
        check=False,
    )
    assert ignored_result.returncode == 0

    system_skill_result = subprocess.run(
        [
            "git",
            "check-ignore",
            "--no-index",
            "-q",
            ".codex/skills/.system/.codex-system-skills.marker",
        ],
        cwd=ROOT,
        check=False,
    )
    assert system_skill_result.returncode == 0
