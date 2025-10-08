default: all

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
	docker compose up -d
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

clean: clean-logs clean-venv clean-npm clean-container

clean-venv:
	rm -rf .venv uv.lock

clean-npm:
	rm -rf .npm-global

clean-logs:
	rm -rf logs/*.log

clean-container:
	docker compose down --rmi all
	rm -rf app/__pycache__

clean-external-network:
	docker network rm base_net

clean-repository: clean-venv clean-logs
	rm -rf app/* tests/* data/*

# ==========
# Serena MCP controls
.PHONY: serena-up serena-down serena-restart serena-logs serena-init serena-status

serena-up:
	@mkdir -p .serena_home/logs .serena_home/prompt_templates projects
	@echo "Starting Serena MCP server (SSE :9121)..."
	docker compose up -d serena
	@echo "Hint: use 'make serena-logs' to tail logs"

serena-down:
	@echo "Stopping Serena MCP server..."
	docker compose stop serena || true

serena-restart:
	@echo "Restarting Serena MCP server..."
	docker compose restart serena

serena-logs:
	@echo "Tailing Serena MCP logs (Ctrl-C to stop)"
	docker compose logs -f serena

serena-status:
	@docker compose ps serena

