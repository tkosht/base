from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "architecture" / "base-harness-set.toml"
RESOURCE_REGISTRY_PATH = (
    ROOT / "docs" / "architecture" / "harness-resources.toml"
)
PYPROJECT_PATH = ROOT / "pyproject.toml"


def load_manifest() -> dict[str, object]:
    with MANIFEST_PATH.open("rb") as fh:
        return tomllib.load(fh)


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


def test_manifest_skills_match_repo_layout() -> None:
    manifest = load_manifest()
    skills = manifest["skills"]
    assert isinstance(skills, list)

    expected = sorted(skills)
    actual_skill_dirs = sorted(
        path.name
        for path in (ROOT / ".claude" / "skills").iterdir()
        if path.is_dir()
    )
    actual_symlinks = sorted(
        path.name
        for path in (ROOT / ".codex" / "skills").iterdir()
        if path.is_symlink()
    )
    actual_agent_symlinks = sorted(
        path.name
        for path in (ROOT / ".agents" / "skills").iterdir()
        if path.is_symlink()
    )

    assert actual_skill_dirs == expected
    assert actual_agent_symlinks == expected
    assert actual_symlinks == expected


def test_manifest_skills_have_canonical_docs() -> None:
    manifest = load_manifest()
    skills = manifest["skills"]
    assert isinstance(skills, list)

    for skill in skills:
        assert isinstance(skill, str)
        assert (
            ROOT / "docs" / "ai" / "skills" / f"{skill}.md"
        ).exists(), skill


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
        ".github/workflows/test-all-subsystems.yml": [
            "python-version: '3.12'"
        ],
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
