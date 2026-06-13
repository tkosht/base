#!/usr/bin/sh
set -eu

VOLTA_HOME="${VOLTA_HOME:-$HOME/.volta}"
export VOLTA_HOME
export PATH="$VOLTA_HOME/bin:$PATH"

if ! command -v volta >/dev/null 2>&1; then
    echo "Installing Volta ..."
    curl -fsSL https://get.volta.sh | bash -s -- --skip-setup
    export PATH="$VOLTA_HOME/bin:$PATH"
fi

volta install node@24.16.0 npm@11.13.0
