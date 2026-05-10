from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ci.repo_copy import copy_repo_for_test
from scripts.template.sync_upstream_skill import UnknownSkillError, sync_skill

ROOT = Path(__file__).resolve().parents[2]


def _copy_repo(tmp_path: Path) -> Path:
    return copy_repo_for_test(ROOT, tmp_path)


def test_sync_upstream_skill_updates_target_and_recreates_symlinks(
    tmp_path: Path,
) -> None:
    repo = _copy_repo(tmp_path)
    target = repo / ".agents" / "skills" / "grill-me" / "SKILL.md"
    claude_link = repo / ".claude" / "skills" / "grill-me"
    codex_link = repo / ".codex" / "skills" / "grill-me"

    target.write_text("stale\n", encoding="utf-8")
    claude_link.unlink()
    codex_link.unlink()

    result = sync_skill(
        "grill-me",
        root=repo,
        fetch_text=lambda url: "fresh\n",
    )

    assert result.skill_name == "grill-me"
    assert target.read_text(encoding="utf-8") == "fresh\n"
    assert claude_link.is_symlink()
    assert claude_link.readlink() == Path("../../.agents/skills/grill-me")
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
