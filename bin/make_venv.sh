#!/usr/bin/sh

export PATH="$HOME/.local/bin:$PATH"

uvx migrate-to-uv
uv python install 3.12
uv venv --python 3.12
uv lock
uv sync

