# Agent Skills Overview (Repository)

## Current Skill Locations
- `.codex/skills/.system/` contains system skills (`skill-creator`, `skill-installer`) and `.codex-system-skills.marker`.
- `.agents/skills/` stores the concrete repo-local skill implementation.
- `.claude/skills/` holds compatibility symlinks for Claude Code discovery.
- `.codex/skills/` holds compatibility symlinks that point to `.agents/skills/`.
- No repo-level `skills/` directory is expected; keep system skills under `.codex/skills/.system`.

## Existing Skills
- `skill-creator`: Defines skill anatomy, naming, frontmatter rules, optional resources, and packaging scripts.
  - File: `.codex/skills/.system/skill-creator/SKILL.md`
- `skill-installer`: Installs skills from curated lists or GitHub repos.
  - File: `.codex/skills/.system/skill-installer/SKILL.md`
- `codex-subagent`: Project-local skill to orchestrate `codex exec` runs (single/parallel/competition) with logging and guardrails.
  - Files: `.agents/skills/codex-subagent/SKILL.md`, `.agents/skills/codex-subagent/scripts/*`, `.claude/skills/codex-subagent`, `.codex/skills/codex-subagent`
- `dependabot-pr-maintainer`: Project-local skill to triage, update, verify, and merge Dependabot pull requests with explicit merge intent.
  - Files: `.agents/skills/dependabot-pr-maintainer/SKILL.md`, `.claude/skills/dependabot-pr-maintainer`, `.codex/skills/dependabot-pr-maintainer`
- `grill-me`: Project-local vendored skill imported from `mattpocock/skills` to pressure-test a plan or design one question at a time.
  - Files: `.agents/skills/grill-me/SKILL.md`, `.claude/skills/grill-me`, `.codex/skills/grill-me`
- `grill-me-essential-first`: Project-local skill to pressure-test a plan or design while forcing the unresolved essential questions to be handled before low-priority details.
  - Files: `.agents/skills/grill-me-essential-first/SKILL.md`, `.claude/skills/grill-me-essential-first`, `.codex/skills/grill-me-essential-first`
- `ai-agent-collaboration-exec`: Project-local skill to design and operate AI collaboration where execution is delegated to subagents (Executor/Reviewer/Verifier).
  - Files: `.agents/skills/ai-agent-collaboration-exec/SKILL.md`, `.agents/skills/ai-agent-collaboration-exec/references/*`, `.claude/skills/ai-agent-collaboration-exec`, `.codex/skills/ai-agent-collaboration-exec`

## Templates (Non-skill References)
- Subagent SKILL.md template: `.agents/skills/skill-authoring/references/subagent_skill_md_template.md`

## Skill Structure (From skill-creator)
- Required: `SKILL.md` with YAML frontmatter containing `name` and `description`.
- `description` is the primary trigger text for when the skill is selected.
- Optional resource folders:
  - `scripts/` for deterministic helpers
  - `references/` for detailed docs
  - `assets/` for templates or files used in output

## Helper Scripts (System Skill)
Located under `.codex/skills/.system/skill-creator/scripts/`:
- `init_skill.py` (scaffold a new skill)
- `quick_validate.py` (validate structure)
- `package_skill.py` (package to .skill)

Local policy: do not add a top-level `scripts/` directory. If you run any of the helper scripts, invoke Python with `uv run python` or `python3`.

## Tests
- `tests/test_base_harness_set.py` checks retained skill layout and shim targets.
- `tests/test_template_contract.py` checks template validator failures for missing skill source and shims.
- `tests/template_smoke/test_sync_upstream_skill.py` checks upstream sync into `.agents/skills` and shim recreation.
