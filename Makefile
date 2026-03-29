.PHONY: bootstrap doctor lint test test-codex-live template-smoke use-python-starter use-nextjs-starter

bootstrap:
	uv sync --all-groups --all-extras
	npm ci

doctor:
	uv run python scripts/ci/validate_template.py

lint:
	uv run ruff check .
	uv run black --check .

test:
	uv run pytest -q -m "not codex_live" tests/test_base_harness_set.py tests/test_template_contract.py tests/template_smoke tests/codex_subagent

test-codex-live:
	@command -v codex >/dev/null 2>&1 || { echo "codex CLI が見つかりません。まず make bootstrap を実行してください。"; exit 1; }
	CODEX_INTEGRATION=1 uv run pytest -q -m codex_live tests/codex_subagent

template-smoke:
	uv run pytest -q tests/template_smoke

use-python-starter:
	uv run python scripts/template/apply_overlay.py --template python-minimal

use-nextjs-starter:
	uv run python scripts/template/apply_overlay.py --template nextjs-app
