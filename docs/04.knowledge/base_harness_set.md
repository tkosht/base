# Base Harness Set

## 正本

- この一覧の正本は `docs/04.knowledge/base_harness_set.toml`
- この文書は、人が読むための要約

## Python Baseline

- 標準 Python: `3.12`
- `pyproject.toml` の `requires-python`: `>=3.12,<=3.14`
- GitHub Actions の `ci`、`test-all-subsystems`、`claude` も `3.12` を基準に運用する

## 残すハーネス

- instruction surface
  - `AGENTS.md`
  - `CLAUDE.md`
  - `GEMINI.md`
  - `.cursor/rules/*`
- AGENTS が参照する `memory-bank` 文書
- skills
  - `ai-agent-collaboration-exec`
  - `codex-subagent`
  - `git-commit-pr`
  - `git-mainbranch`
  - `repo-instruction-optimizer`
  - `skill-authoring`
- command docs
  - `codex-subagent.md`
  - `commit.md`
  - `mainbranch.md`
- workflows
  - `ci.yml`
  - `test-all-subsystems.yml`
  - `claude.yml`
- validation
  - `tests/codex_subagent/*`
  - `tests/test_base_harness_set.py`

## 残さないもの

- Dify 固有 skill
  - `app-security-review`
  - `dify-plugin-dev-generic`
  - `dify-plugin-dev-repo`
- Dify 固有レビュー履歴
  - `docs/ai-agent-reviews/**`
- `.codex` 配下の runtime state や cache

## 検証

- `tests/test_base_harness_set.py` で、一覧どおりに存在しているかを確認する
- `tests/codex_subagent/*` で `codex-subagent` の unit/結合検証面を維持する
