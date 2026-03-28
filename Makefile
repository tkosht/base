default: all

all: up install

install: install-venv install-agent-cli

install-venv:
	docker compose exec app bash bin/make_venv.sh

install-agent-cli:
	docker compose exec app bash bin/install_agentcli.sh


# ==========
# interaction tasks
bash:
	docker compose exec app bash

python:
	docker compose exec app bash -i -c 'uv run python'


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

clean: clean-container clean-venv clean-npm clean-logs

clean-container:
	docker compose down --rmi all
	rm -rf app/__pycache__

clean-venv:
	rm -rf .venv uv.lock

clean-npm:
	rm -rf .npm-global

clean-logs:
	rm -rf logs/*.log

clean-repository: clean-venv clean-logs
	rm -rf app/* tests/* data/*

