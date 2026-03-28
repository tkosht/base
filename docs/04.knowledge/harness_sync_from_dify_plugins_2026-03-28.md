# Harness Sync From `dify_plugins` (2026-03-28)

## Status

- Historical sync note
- Canonical harness inventory now lives in `docs/04.knowledge/base_harness_set.toml`
- Human-readable summary now lives in `docs/04.knowledge/base_harness_set.md`

## Summary

- Source of truth: `https://github.com/tkosht/dify_plugins`
- Target: `https://github.com/tkosht/base`
- Scope: canonical instruction surface, AGENTS-referenced docs, reusable core skills, `tests/codex_subagent`, and genericized GitHub Actions workflows for `ci`, `test-all-subsystems`, and `claude`

## Included

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*`
- `memory-bank/00-core/*` entries referenced by `AGENTS.md`
- `memory-bank/02-organization/tmux_organization_success_patterns.md`
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`
- `memory-bank/11-checklist-driven/*` entries referenced by `AGENTS.md`
- `memory-bank/03-patterns/ai-agent-collaboration-exec_skill_usability_review_2026-01-05.md`
- `.claude/skills/{ai-agent-collaboration-exec,codex-subagent,git-commit-pr,git-mainbranch,repo-instruction-optimizer,skill-authoring}`
- `.codex/skills/*` symlink discovery surface for the synced skills
- `.claude/commands/tasks/{codex-subagent.md,commit.md,mainbranch.md}`
- `tests/codex_subagent/*`
- `.github/workflows/ci.yml`
- `.github/workflows/test-all-subsystems.yml`
- `.github/workflows/claude.yml`

## Excluded

- Dify-specific skills: `app-security-review`, `dify-plugin-dev-generic`, `dify-plugin-dev-repo`
- Repo-local runtime state under `.codex/` other than tracked metadata and skill symlinks
- `.github/dependabot.yml`, `.github/ISSUE_TEMPLATE/simple.yml`
- `docs/ai-agent-reviews/**` and Dify-specific project history not required by copied skills/tests

## Verification

- `find .codex/skills -maxdepth 1 -xtype l -print`
- `uv run pytest -q --no-cov tests/codex_subagent/test_pipeline_schema.py tests/codex_subagent/test_pipeline_spec.py tests/codex_subagent/test_model_option.py`
- `rg -n 'openai_gpt5_responses|gpt5_agent_strategies|allow_schemaless_tool_args|pip_audit_gate|GOOGLE_API_KEY|bandit' .github/workflows/ci.yml`
