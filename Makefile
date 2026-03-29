.PHONY: bootstrap doctor lint test template-smoke use-python-starter use-nextjs-starter

bootstrap:
	uv sync --all-groups --all-extras
	npm ci

doctor:
	uv run python scripts/ci/validate_template.py

lint:
	uv run ruff check .
	uv run black --check .

test:
	uv run pytest -q tests/test_base_harness_set.py tests/test_template_contract.py tests/template_smoke tests/codex_subagent

template-smoke:
	uv run pytest -q tests/template_smoke

use-python-starter:
	uv run python scripts/template/apply_overlay.py --template python-minimal

use-nextjs-starter:
	uv run python scripts/template/apply_overlay.py --template nextjs-app
