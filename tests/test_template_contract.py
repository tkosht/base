from __future__ import annotations

import shutil
from pathlib import Path

import pytest

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
    repo = tmp_path / "repo"
    shutil.copytree(ROOT, repo, symlinks=True)
    return repo


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
