# Base Harness Repository

このリポジトリは、repo-local instruction surface、再利用 skill、GitHub Actions、検証テスト、運用補助ファイルを保持するためのハーネス専用リポジトリです。

## Canonical References

- ハーネスセットの正本: [docs/04.knowledge/base_harness_set.toml](./docs/04.knowledge/base_harness_set.toml)
- 人間向け要約: [docs/04.knowledge/base_harness_set.md](./docs/04.knowledge/base_harness_set.md)
- repo-local instruction の正本: [AGENTS.md](./AGENTS.md)

## What Stays Here

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*`
- `.claude/skills/*` と `.codex/skills/*`
- `.claude/commands/tasks/codex-subagent.md`, `commit.md`, `mainbranch.md`
- `.github/workflows/*`
- `tests/codex_subagent/*`, `tests/test_base_harness_set.py`
- `bin/`, `docker/`, `compose*.yml`, `Makefile`, `package*.json`
