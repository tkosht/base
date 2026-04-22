.PHONY: bootstrap doctor lint test test-codex-live template-smoke use-python-starter use-nextjs-starter sync-skill

default: all


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

sync-skill:
	@test -n "$(SKILL)" || { echo "SKILL=<registered-skill> を指定してください。"; exit 1; }
	uv run python scripts/template/sync_upstream_skill.py --skill "$(SKILL)" $(if $(REF),--ref "$(REF)",)

# ==================================================
# controlling container tasks


all: up install

install: install-venv install-agent-cli

install-venv:
	docker compose exec app bash bin/make_venv.sh

install-agent-cli:
	docker compose exec app bash bin/install_agentcli.sh

webapp:
	poetry run gunicorn app.demo:api -k uvicorn.workers.UvicornWorker -b 0.0.0.0:7860 \
	-w 1 --threads 8 --timeout 0 --graceful-timeout 0 --keep-alive 65 \
	--forwarded-allow-ips="*"

container-webapp:
	docker compose exec app \
	poetry run gunicorn app.demo:api -k uvicorn.workers.UvicornWorker -b 0.0.0.0:7860 \
	-w 1 --threads 8 --timeout 0 --graceful-timeout 0 --keep-alive 65 \
	--forwarded-allow-ips="*"

# ==========
# interaction tasks
bash:
	docker compose exec app bash

python:
	docker compose exec app bash -i -c 'uv run python'

external-network:
	docker network create base_net


# switch mode
cpu gpu:
	@rm -f compose.yml
	@ln -s docker/compose.$@.yml compose.yml

mode:
	@echo $$(ls -l compose.yml | awk -F. '{print $$(NF-1)}')


# ==========
# docker compose aliases
up:
	docker compose up -d --build
	docker compose exec app sudo service docker start

active:
	docker compose up

ps images down:
	docker compose $@

im:images

build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

reup: down up

clean: clean-container clean-logs clean-venv clean-npm

clean-venv:
	rm -rf .venv uv.lock

clean-npm:
	rm -rf .npm-global node_modules

clean-logs:
	rm -rf logs/*.log

clean-container:
	docker compose down --rmi all
	rm -rf app/__pycache__

clean-external-network:
	docker network rm base_net

clean-repository: clean-venv clean-logs
	rm -rf app/* tests/* data/*
