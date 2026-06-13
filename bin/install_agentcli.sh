#!/usr/bin/sh
set -eu

d=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cd "$d/../"

sh bin/install_claudecode.sh

sh bin/install_codexcli.sh

sh bin/install_geminicli.sh

# sh bin/install_cursorcli.sh
