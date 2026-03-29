from __future__ import annotations

import re
import sys
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
    "repo-instruction-optimizer",
    "skill-authoring",
]
REQUIRED_PATHS = [
    "README.md",
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
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/base-harness-set.toml",
    "docs/architecture/decision-records/README.md",
    "docs/architecture/decision-records/knowledge-surface-consolidation.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "docs/standards/communication.md",
    "docs/repository-template-design.md",
    "scripts/ci/validate_template.py",
    "scripts/template/apply_overlay.py",
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
    "AGENTS.md",
    "CLAUDE.md",
    "docs/ai/repo-contract.md",
    "docs/ai/mcp.md",
    "docs/ai/operator-checklist.md",
    "docs/ai/execution-playbooks.md",
    "docs/ai/checklists/codex-mcp-collaboration-template.md",
    "docs/architecture/overview.md",
    "docs/architecture/knowledge-architecture.md",
    "docs/architecture/base-harness-set.md",
    "docs/architecture/decision-records/README.md",
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
