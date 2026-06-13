#!/usr/bin/sh
set -eu

d=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cd "$d/../"

VOLTA_HOME="${VOLTA_HOME:-$HOME/.volta}"
export VOLTA_HOME
export PATH="$VOLTA_HOME/bin:$PATH"

sh bin/install_node_toolchain.sh
volta install @openai/codex@latest

echo "Codex CLI: $(codex --version)"
