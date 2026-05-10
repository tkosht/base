---
name: skill-authoring
description: "Create or update project-local Codex skills (SKILL.md) in this repo, including canonical placement under .agents/skills, compatibility symlinks under .claude/skills and .codex/skills, and adherence to local rules: no top-level scripts/, run Python with uv run python or python3, and prefer Serena or currently active MCP tools. Use when the user asks to add or edit skills or SKILL.md in this repository."
---

# Skill Authoring

## Scope
- Create or update skills stored under `.agents/skills/<skill-name>`.
- Keep project discovery in sync by adding symlinks in `.claude/skills/<skill-name>` and `.codex/skills/<skill-name>`.
- Avoid introducing a top-level `scripts/` directory.
- Do not use Cognee; use Serena or an active MCP when available.

## Workflow
1. Confirm the skill name (lowercase letters, digits, hyphens) and the trigger description.
2. Create the skill directory: `.agents/skills/<skill-name>/`.
3. Add `SKILL.md` with required frontmatter and concise instructions.
4. Add optional `references/` or `assets/` only when needed.
5. If any Python scripts are included inside the skill, run them with `uv run python` or `python3`.
6. Create symlink for discovery:
   - `ln -s ../../.agents/skills/<skill-name> .claude/skills/<skill-name>`
   - `ln -s ../../.agents/skills/<skill-name> .codex/skills/<skill-name>`
7. Sanity check by listing skill files and ensuring the symlink resolves.

## SKILL.md Skeleton
```markdown
---
name: <skill-name>
description: "What the skill does and when to use it; include explicit triggers."
---

# <Skill Title>

## Purpose
[1-2 sentences.]

## Workflow
1. Step ...
2. Step ...

## References
- `references/<file>.md` (if applicable)
```

## References
- Read `references/agent_skills_overview.md` for the current skill layout and existing system skills in this repo.
- Use `references/subagent_skill_md_template.md` as a reusable template for subagent/orchestrator-style SKILL.md files.

## Guardrails
- Keep SKILL.md concise; move details into `references/`.
- Do not add new top-level automation scripts; use existing tools or manual steps.
