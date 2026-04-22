from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.template.sync_upstream_skill import UnknownSkillError, sync_skill

ROOT = Path(__file__).resolve().parents[2]


def _copy_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, symlinks=True)
    return repo


def test_sync_upstream_skill_updates_target_and_recreates_symlinks(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    target = repo / ".claude" / "skills" / "grill-me" / "SKILL.md"
    agent_link = repo / ".agents" / "skills" / "grill-me"
    codex_link = repo / ".codex" / "skills" / "grill-me"

    target.write_text("stale\n", encoding="utf-8")
    agent_link.unlink()
    codex_link.unlink()

    result = sync_skill(
        "grill-me",
        root=repo,
        fetch_text=lambda url: "fresh\n",
    )

    assert result.skill_name == "grill-me"
    assert target.read_text(encoding="utf-8") == "fresh\n"
    assert agent_link.is_symlink()
    assert agent_link.readlink() == Path("../../.claude/skills/grill-me")
    assert codex_link.is_symlink()
    assert codex_link.readlink() == Path("../../.agents/skills/grill-me")
    assert result.url.endswith("/main/grill-me/SKILL.md")


def test_sync_upstream_skill_allows_ref_override(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    seen: dict[str, str] = {}

    def fake_fetch(url: str) -> str:
        seen["url"] = url
        return "fresh\n"

    result = sync_skill(
        "grill-me",
        root=repo,
        ref_override="topic-branch",
        fetch_text=fake_fetch,
    )

    assert result.ref == "topic-branch"
    assert seen["url"].endswith("/topic-branch/grill-me/SKILL.md")


def test_sync_upstream_skill_rejects_unknown_skill(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)

    with pytest.raises(UnknownSkillError):
        sync_skill("missing-skill", root=repo, fetch_text=lambda url: "noop")
