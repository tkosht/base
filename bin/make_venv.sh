#!/usr/bin/sh

export PATH="$HOME/.local/bin:$PATH"
export UV_LINK_MODE=copy

uv sync --python 3.12
# uvx migrate-to-uv
# uv python install 3.12
# uv venv --python 3.12
# uv lock
# uv sync

