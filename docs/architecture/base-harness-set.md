# ベースハーネス一覧

## 正本

- 一覧の正本は `docs/architecture/base-harness-set.toml`
- この文書は人が読むための要約
- 移植判断の group は `portable_harness_groups` に置く

## Python Baseline

- 標準 Python: `3.12`
- `pyproject.toml` の `requires-python`: `>=3.12,<=3.14`
- GitHub Actions の `ci`、`test-all-subsystems`、`claude` も `3.12` を基準に運用する

## 移植単位

他 repo へコピーする時は、単体ファイルではなく下の group 単位で扱う。
正確な path は `docs/architecture/base-harness-set.toml` の
`portable_harness_groups` を見る。

## 必ずコピーするもの

- agent instruction surface
  - `AGENTS.md` を正本にし、`CLAUDE.md`、`GEMINI.md`、`.cursor/rules/*` は薄い互換アダプタとして維持する
  - `DESIGN.md` は generated repo の visual contract として移す
- skill surface
  - `.claude/skills/` の実体
  - `.agents/skills/` と `.codex/skills/` の互換 entrypoint
  - `docs/ai/skills/` の利用者向け説明
- harness registry
  - `docs/architecture/base-harness-set.toml`
  - `docs/architecture/base-harness-set.md`
  - `docs/architecture/harness-resources.toml`
  - `docs/architecture/decision-records/` の正本説明と基礎判断メモ
- validation and copy tools
  - `Makefile`
  - `pyproject.toml`
  - `scripts/ci/validate_template.py`
  - `scripts/ci/repo_copy.py`
  - `scripts/template/`
  - `tests/test_base_harness_set.py`
  - `tests/test_template_contract.py`
  - `tests/template_smoke/`
  - `tests/codex_subagent/`
  - `tests/harness_autoptimizer/`

## 移植先で調整するもの

- knowledge and standards
  - `docs/ai/`、`docs/design/`、`docs/architecture/`、`docs/standards/` は構造を保ってコピーし、template 例を移植先 repo の事実へ置き換える
  - Model Context Protocol（MCP）や secret handling の記述は、移植先の実際の connector と権限に合わせて見直す
- automation workflows
  - `.github/workflows/ci.yml`
  - `.github/workflows/test-all-subsystems.yml`
  - `.github/workflows/claude.yml`
  - `.github/workflows/harness-autopt.yml`
  - `.github/workflows/template-health.yml`
  - workflow permission、secret、path filter は移植先に合わせて確認する
- ops scaffold
  - `.codex/config.toml`
  - `.codex/version.json`
  - `.claude/settings.json`
  - `.mcp.json`
  - `.env.example`
  - `.github/dependabot.yml`
  - `.github/ISSUE_TEMPLATE/simple.yml`
  - `README.md`
  - `package*.json`
  - `uv.lock`
  - `bin/`
  - `docker/`
  - `compose.override.yml`
  - `secrets/README.md`
  - 既存プロジェクトの package、container、tooling と競合する場合は、移植先を優先して統合する

## 任意でコピーするもの

- collaboration command docs
  - `.claude/commands/tasks/codex-subagent.md`
  - `.claude/commands/tasks/commit.md`
  - `.claude/commands/tasks/mainbranch.md`
  - Claude task docs を使う repo だけに移す

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
- `.env` と runtime `.env.*`。ただし公開 placeholder の `.env.example` は残す
- `secrets/**` の実 secret。保護境界を示す `secrets/README.md` は残す
- token、local auth state
- `.git`、`.venv`、`node_modules`、`.pytest_cache`、`.ruff_cache`

## 検証

- `tests/test_base_harness_set.py` で、一覧どおりに存在しているかと削除対象が消えているかを確認する
- `tests/codex_subagent/*` で `codex-subagent` の単体検証面と実行テスト面を維持する
- `ci.yml` / `test-all-subsystems.yml` はベースハーネス前提で `make test` を実行する
