from __future__ import annotations

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
    "docs/architecture/overview.md",
    "docs/standards/coding.md",
    "docs/standards/testing.md",
    "docs/standards/security.md",
    "docs/standards/review.md",
    "scripts/ci/validate_template.py",
    "scripts/template/apply_overlay.py",
    "templates/manifest.yaml",
    "secrets/README.md",
]
FORBIDDEN_PATHS = [
    ".claude/settings.local.json",
    ".claude/.claude/settings.local.json",
]


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
        "docs/architecture/overview.md",
    ):
        if needle not in agents_text:
            errors.append(f"AGENTS.md must reference {needle}")
    if "docs/ai/repo-contract.md" not in claude_text:
        errors.append("CLAUDE.md must reference docs/ai/repo-contract.md")

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
