from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.template.apply_overlay import list_templates

ROOT = Path(__file__).resolve().parents[2]
RETAINED_SKILLS = [
    "ai-agent-collaboration-exec",
    "codex-subagent",
    "git-commit-pr",
    "git-mainbranch",
    "grill-me",
    "grill-me-essential-first",
    "harness-autoptimizer",
    "repo-instruction-optimizer",
    "skill-authoring",
]
REQUIRED_PATHS = [
    "README.md",
    "DESIGN.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    ".env.example",
    ".editorconfig",
    ".gitattributes",
    ".mcp.json",
    ".codex/config.toml",
    ".claude/settings.json",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/feature.yml",
    ".github/ISSUE_TEMPLATE/agent-task.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/template-health.yml",
    "package.json",
    "package-lock.json",
    "docs/ai/repo-contract.md",
    "docs/ai/mcp.md",
    "docs/ai/operator-checklist.md",
    "docs/ai/execution-playbooks.md",
    "docs/ai/checklists/codex-mcp-collaboration-template.md",
    "docs/ai/skills/README.md",
    "docs/ai/skills/ai-agent-collaboration-exec.md",
    "docs/ai/skills/grill-me.md",
    "docs/ai/skills/grill-me-essential-first.md",
    "docs/ai/skills/harness-autoptimizer.md",
    "docs/design/README.md",
    "docs/design/samples/starter-b2b-corporate",
    "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
    "docs/design/samples/starter-b2b-corporate/preview.html",
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/base-harness-set.toml",
    "docs/architecture/harness-resources.toml",
    "docs/architecture/decision-records/README.md",
    "docs/architecture/decision-records/codex-shared-defaults.md",
    "docs/architecture/decision-records/knowledge-surface-consolidation.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "docs/standards/communication.md",
    "docs/repository-template-design.md",
    "scripts/ci/validate_template.py",
    "scripts/template/apply_overlay.py",
    "scripts/template/sync_upstream_skill.py",
    "scripts/template/upstream_skills.toml",
    "templates/manifest.yaml",
    "secrets/README.md",
]
FORBIDDEN_PATHS = [
    ".claude/settings.local.json",
    ".claude/.claude/settings.local.json",
    "docs/04.knowledge",
    "memory-bank",
]
PRIMARY_DOCS = [
    "README.md",
    "DESIGN.md",
    "AGENTS.md",
    "CLAUDE.md",
    "docs/ai/repo-contract.md",
    "docs/ai/mcp.md",
    "docs/ai/operator-checklist.md",
    "docs/ai/execution-playbooks.md",
    "docs/ai/checklists/codex-mcp-collaboration-template.md",
    "docs/design/README.md",
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/decision-records/README.md",
    "docs/architecture/decision-records/codex-shared-defaults.md",
    "docs/architecture/decision-records/knowledge-surface-consolidation.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "docs/standards/communication.md",
]
TERM_EXPANSIONS = {
    "TDD": ("テスト駆動開発（TDD）",),
    "CI": ("継続的インテグレーション（CI）",),
    "MCP": ("Model Context Protocol（MCP）",),
    "CLI": (
        "コマンドラインツール（CLI）",
        "コマンドラインツール（Codex CLI）",
    ),
    "OAuth": ("OAuth 認証",),
}
DESIGN_DOCS = [
    "DESIGN.md",
    "docs/design/README.md",
    "docs/design/samples/starter-b2b-corporate/DESIGN.sample.md",
]
DESIGN_TERM_EXPANSIONS = {
    "B2B": ("企業間取引（B2B）",),
    "LP": ("ランディングページ（LP）",),
    "CTA": (
        "行動喚起（CTA）",
        "コールトゥアクション（CTA）",
    ),
    "UI": ("ユーザーインターフェース（UI）",),
}
DESIGN_READ_FIRST_CONTRACT = (
    "design 系作業では、root の `DESIGN.md` を先に読み、"
    "必要に応じて `docs/design/README.md` を補助面として読む。"
)
DESIGN_ROLE_CONTRACT = "`DESIGN.md`: generated repo の visual contract の正本"
DESIGN_README_ROLE_CONTRACT = (
    "`docs/design/README.md`: root `DESIGN.md` を支える design guidance "
    "の canonical な補助面"
)
DESIGN_README_MIN_ROLE = (
    "この文書は root の `DESIGN.md` を支える design guidance "
    "の canonical な補助面です。"
)
DESIGN_README_SYNC_REF = (
    "同期ポリシーの正本は `docs/ai/repo-contract.md` です。"
)
DESIGN_SYNC_POLICY_CONTRACT = (
    "`docs/design/README.md` は template-maintained な補助面であり、"
    "自動同期はしない"
)
DESIGN_SYNC_INTAKE_CONTRACT = "maintainer が手動で取り込む"
DESIGN_CHECKLIST_UPDATE_CONTRACT = (
    "generated repo の visual contract の通常更新対象として、"
    "実プロジェクト向けに更新する"
)
DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT = (
    "template-maintained な補助面なので、generated repo では通常更新しない。"
)
DESIGN_PREVIEW_NOTES = {
    "docs/design/samples/starter-b2b-corporate/preview.html": (
        "Reference-only",
        "Source note:",
        "Reviewed date:",
        "Sync note:",
    )
}
SUPPORTED_CODEX_SANDBOX_MODES = {
    "danger-full-access",
    "workspace-write",
}
CODEX_SHARED_DEFAULT_EXPECTATIONS = {
    "docs/standards/security.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "mount 範囲",
        "秘密情報",
        "外向き通信",
        "sandbox_workspace_write.network_access = false",
    ),
    "docs/ai/repo-contract.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "threat model",
        "mount 範囲",
        "秘密情報",
        "外向き通信",
        "sandbox_workspace_write.network_access = false",
    ),
    "docs/architecture/decision-records/codex-shared-defaults.md": (
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
        "workspace-write",
        "generated repo",
        "threat model",
        "sandbox_workspace_write.network_access = false",
    ),
}


def _check_primary_terminology(root: Path, errors: list[str]) -> None:
    for rel in PRIMARY_DOCS:
        text = (root / rel).read_text(encoding="utf-8")
        if re.search(r"\bADR\b", text):
            errors.append(f"{rel} must use 設計判断メモ instead of ADR")
        for term, expansions in TERM_EXPANSIONS.items():
            if re.search(rf"\b{term}\b", text) and not any(
                expansion in text for expansion in expansions
            ):
                errors.append(
                    f"{rel} uses {term} without an approved expansion"
                )


def _check_codex_shared_defaults(root: Path, errors: list[str]) -> None:
    config_text = (root / ".codex/config.toml").read_text(encoding="utf-8")
    config = tomllib.loads(config_text)
    if config.get("approval_policy") != "never":
        return
    sandbox_mode = config.get("sandbox_mode")
    if sandbox_mode not in SUPPORTED_CODEX_SANDBOX_MODES:
        errors.append(
            ".codex/config.toml must keep sandbox_mode in "
            '{"danger-full-access", "workspace-write"} '
            'when approval_policy = "never" is shipped'
        )
    if sandbox_mode == "workspace-write":
        workspace_write = config.get("sandbox_workspace_write")
        if not isinstance(workspace_write, dict) or (
            workspace_write.get("network_access") is not False
        ):
            errors.append(
                ".codex/config.toml must keep "
                "sandbox_workspace_write.network_access = false "
                'when approval_policy = "never" is shipped'
            )

    for rel, needles in CODEX_SHARED_DEFAULT_EXPECTATIONS.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(
                    f"{rel} missing Codex shared default contract: {needle}"
                )


def _check_design_doc_terminology(root: Path, errors: list[str]) -> None:
    for rel in DESIGN_DOCS:
        text = (root / rel).read_text(encoding="utf-8")
        for term, expansions in DESIGN_TERM_EXPANSIONS.items():
            count = len(re.findall(rf"\b{term}\b", text))
            if count == 0:
                continue
            if not any(expansion in text for expansion in expansions):
                errors.append(
                    f"{rel} uses {term} without an approved expansion"
                )
            if count == 1:
                errors.append(
                    f"{rel} uses {term} only once; spell it out instead of abbreviating"
                )


def _check_design_contract(root: Path, errors: list[str]) -> None:
    repo_contract = (root / "docs/ai/repo-contract.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        DESIGN_READ_FIRST_CONTRACT,
        DESIGN_ROLE_CONTRACT,
        DESIGN_README_ROLE_CONTRACT,
        DESIGN_SYNC_POLICY_CONTRACT,
        DESIGN_SYNC_INTAKE_CONTRACT,
        "## Generated Repo Checklist",
        "3. `DESIGN.md`",
        DESIGN_CHECKLIST_UPDATE_CONTRACT,
        "8. `docs/design/README.md`",
        DESIGN_CHECKLIST_SUPPLEMENT_CONTRACT,
    ):
        if needle not in repo_contract:
            errors.append(
                "docs/ai/repo-contract.md missing design contract: " + needle
            )

    design_readme = (root / "docs/design/README.md").read_text(
        encoding="utf-8"
    )
    for needle in (DESIGN_README_MIN_ROLE, DESIGN_README_SYNC_REF):
        if needle not in design_readme:
            errors.append(
                "docs/design/README.md missing design guidance contract: "
                + needle
            )

    for rel, needles in DESIGN_PREVIEW_NOTES.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel} missing preview note: {needle}")


def _check_non_root_design_md(root: Path, errors: list[str]) -> None:
    unexpected = sorted(
        str(path.relative_to(root))
        for path in root.rglob("DESIGN.md")
        if path.relative_to(root).as_posix() != "DESIGN.md"
    )
    if unexpected:
        errors.append(
            "non-root DESIGN.md is forbidden: " + ", ".join(unexpected)
        )


def _extract_workflow_paths(text: str) -> list[list[str]]:
    sections: list[list[str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)paths:\s*$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        index += 1
        entries: list[str] = []
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip(" "))
            if stripped and current_indent <= indent:
                break
            item = re.match(r'^\s*-\s*[\'"]?([^\'"]+)[\'"]?\s*$', line)
            if item:
                entries.append(item.group(1))
            index += 1
        sections.append(entries)
    return sections


def _paths_cover_design_docs(paths: list[str]) -> bool:
    return any(path in {"docs/design/**", "docs/**", "**"} for path in paths)


def _check_workflow_path_filters(root: Path, errors: list[str]) -> None:
    for rel in (
        ".github/workflows/template-health.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/test-all-subsystems.yml",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        sections = _extract_workflow_paths(text)
        if not sections:
            continue
        for index, paths in enumerate(sections, start=1):
            if "DESIGN.md" not in paths:
                errors.append(
                    f"{rel} missing workflow path coverage for DESIGN.md "
                    f"in paths section {index}"
                )
            if not _paths_cover_design_docs(paths):
                errors.append(
                    f"{rel} missing workflow path coverage for docs/design/** "
                    f"in paths section {index}"
                )


def run_checks(root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            errors.append(f"missing required path: {rel}")

    for rel in FORBIDDEN_PATHS:
        if (root / rel).exists():
            errors.append(f"local-only path should not be tracked: {rel}")

    agents_text = (root / "AGENTS.md").read_text(encoding="utf-8")
    claude_text = (root / "CLAUDE.md").read_text(encoding="utf-8")
    for needle in (
        "docs/ai/repo-contract.md",
        "docs/architecture/knowledge-architecture.md",
        "docs/architecture/overview.md",
    ):
        if needle not in agents_text:
            errors.append(f"AGENTS.md must reference {needle}")
    for needle in (
        "docs/ai/repo-contract.md",
        "docs/standards/communication.md",
    ):
        if needle not in claude_text:
            errors.append(f"CLAUDE.md must reference {needle}")

    gitignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    for needle in (
        ".claude/settings.local.json",
        ".claude/.claude/",
        "secrets/**",
        "!secrets/README.md",
    ):
        if needle not in gitignore_text:
            errors.append(f".gitignore missing pattern: {needle}")

    claude_skill_dirs = sorted(
        path.name
        for path in (root / ".claude" / "skills").iterdir()
        if path.is_dir() and path.name != "__pycache__"
    )
    if claude_skill_dirs != RETAINED_SKILLS:
        errors.append(
            "unexpected .claude/skills layout: " + ", ".join(claude_skill_dirs)
        )

    agent_entries = sorted(
        path.name
        for path in (root / ".agents" / "skills").iterdir()
        if path.is_symlink()
    )
    if agent_entries != RETAINED_SKILLS:
        errors.append(
            "unexpected .agents/skills layout: " + ", ".join(agent_entries)
        )

    codex_entries = sorted(
        path.name
        for path in (root / ".codex" / "skills").iterdir()
        if path.is_symlink()
    )
    if codex_entries != RETAINED_SKILLS:
        errors.append(
            "unexpected .codex/skills layout: " + ", ".join(codex_entries)
        )

    template_ids = sorted(spec.template_id for spec in list_templates())
    if template_ids != ["nextjs-app", "python-minimal"]:
        errors.append(f"unexpected template ids: {template_ids}")

    makefile_text = (root / "Makefile").read_text(encoding="utf-8")
    for needle in (
        "test-codex-live:",
        '-m "not codex_live"',
        "CODEX_INTEGRATION=1 uv run pytest -q -m codex_live tests/codex_subagent",
    ):
        if needle not in makefile_text:
            errors.append(
                f"Makefile missing Codex live test contract: {needle}"
            )

    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    if "codex_live:" not in pyproject_text:
        errors.append("pyproject.toml must define the codex_live marker")

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    if "make test-codex-live" not in readme_text:
        errors.append("README.md must document make test-codex-live")
    if "docs/architecture/knowledge-architecture.md" not in readme_text:
        errors.append(
            "README.md must document docs/architecture/knowledge-architecture.md"
        )

    contract_text = (root / "docs/ai/repo-contract.md").read_text(
        encoding="utf-8"
    )
    for needle in (
        "make test-codex-live",
        "ChatGPT",
        "docs/architecture/knowledge-architecture.md",
    ):
        if needle not in contract_text:
            errors.append(
                "docs/ai/repo-contract.md missing test mode contract: "
                + needle
            )

    testing_text = (root / "docs/standards/testing.md").read_text(
        encoding="utf-8"
    )
    for needle in ("make test-codex-live", "codex_live"):
        if needle not in testing_text:
            errors.append(
                "docs/standards/testing.md missing live test guidance: "
                + needle
            )

    _check_primary_terminology(root, errors)
    _check_codex_shared_defaults(root, errors)
    _check_non_root_design_md(root, errors)
    _check_design_contract(root, errors)
    _check_design_doc_terminology(root, errors)

    workflow_expectations = {
        ".github/workflows/template-health.yml": (
            "make bootstrap",
            "make doctor",
            "make lint",
            "make test",
        ),
        ".github/workflows/ci.yml": (
            "make doctor",
            "make lint",
            "make test",
        ),
        ".github/workflows/test-all-subsystems.yml": (
            "make doctor",
            "make lint",
            "make test",
        ),
    }
    for rel, needles in workflow_expectations.items():
        text = (root / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel} missing workflow contract: {needle}")
        for forbidden in ("memory-bank/", "docs/04.knowledge/"):
            if forbidden in text:
                errors.append(f"{rel} must not reference {forbidden}")
    _check_workflow_path_filters(root, errors)

    live_marker_files = sorted(
        str(path.relative_to(root))
        for path in (root / "tests" / "codex_subagent").glob(
            "test_*integration.py"
        )
        if "pytest.mark.codex_live" in path.read_text(encoding="utf-8")
    )
    expected_live_marker_files = [
        "tests/codex_subagent/test_pipeline_integration.py",
        "tests/codex_subagent/test_tool_use_integration.py",
    ]
    if live_marker_files != expected_live_marker_files:
        errors.append(
            "unexpected codex_live marker layout: "
            + ", ".join(live_marker_files)
        )

    for rel in expected_live_marker_files:
        text = (root / rel).read_text(encoding="utf-8")
        if "ChatGPT-authenticated" not in text or "codex on PATH" not in text:
            errors.append(f"{rel} missing ChatGPT-authenticated skip reason")

    return errors


def main() -> int:
    errors = run_checks()
    if errors:
        for error in errors:
            print(error)
        return 1
    print("template validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
