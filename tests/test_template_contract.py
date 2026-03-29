from __future__ import annotations

import shutil
from pathlib import Path

from scripts.ci.validate_template import run_checks

ROOT = Path(__file__).resolve().parents[1]


def test_template_contract_checks_pass() -> None:
    assert run_checks(ROOT) == []


def test_template_contract_checks_fail_when_workspace_network_enabled(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, symlinks=True)

    config = repo / ".codex" / "config.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(
        text.replace("network_access = false", "network_access = true", 1),
        encoding="utf-8",
    )

    errors = run_checks(repo)

    assert (
        ".codex/config.toml must keep "
        "sandbox_workspace_write.network_access = false "
        'when approval_policy = "never" is shipped'
    ) in errors
