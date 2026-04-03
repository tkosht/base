from __future__ import annotations

import shutil
from pathlib import Path

from scripts.ci.validate_template import run_checks

ROOT = Path(__file__).resolve().parents[1]


def _copy_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, symlinks=True)
    return repo


def _replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


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
