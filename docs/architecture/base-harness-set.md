# ベースハーネス一覧

## 正本

- 一覧の正本は `docs/architecture/base-harness-set.toml`
- この文書は人が読むための要約

## Python Baseline

- 標準 Python: `3.12`
- `pyproject.toml` の `requires-python`: `>=3.12,<=3.14`
- GitHub Actions の `ci`、`test-all-subsystems`、`claude` も `3.12` を基準に運用する

## 残すハーネス

- instruction surface
  - `DESIGN.md`
  - `AGENTS.md`
  - `CLAUDE.md`
  - `GEMINI.md`
  - `.cursor/rules/*`
- 知識の正本
  - `docs/ai/`
  - `docs/ai/experience-capture.md`
  - `docs/design/`
  - `docs/architecture/`
  - `docs/architecture/decision-records/2026-05-06-harness-autoptimizer-downstream-feedback.md`
  - `docs/standards/`
- skills
  - `ai-agent-collaboration-exec`
  - `codex-subagent`
  - `git-commit-pr`
  - `git-mainbranch`
  - `grill-me`
  - `grill-me-essential-first`
  - `harness-autoptimizer`
  - `repo-instruction-optimizer`
  - `repo-template-specializer`
  - `skill-authoring`
- ハーネス資源 registry
  - `docs/architecture/harness-resources.toml`
- command docs
  - `codex-subagent.md`
  - `commit.md`
  - `mainbranch.md`
- workflows
  - `ci.yml`
  - `test-all-subsystems.yml`
  - `claude.yml`
  - `harness-autopt.yml`
- validation
  - `.claude/skills/harness-autoptimizer/prompts/*`
  - `scripts/ci/repo_copy.py`
  - `tests/codex_subagent/*`
  - `tests/harness_autoptimizer/*`
  - `tests/test_base_harness_set.py`
  - `tests/test_template_contract.py`
- ops scaffold
  - `.codex/config.toml`
  - `.codex/version.json`
  - `README.md`
  - `Makefile`
  - `bin/`
  - `docker/`
  - `compose*.yml`
  - `package*.json`

## 残さないもの

- 旧 knowledge surface
- `app/` と app 依存の `tests/test_*.py`
- `.claude/commands/` のうち retained task docs 以外
- `.codex` 配下の runtime state や cache

## 検証

- `tests/test_base_harness_set.py` で、一覧どおりに存在しているかと削除対象が消えているかを確認する
- `tests/codex_subagent/*` で `codex-subagent` の単体検証面と実行テスト面を維持する
- `ci.yml` / `test-all-subsystems.yml` はベースハーネス前提で `make test` を実行する
