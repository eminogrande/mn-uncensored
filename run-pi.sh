#!/bin/zsh

set -euo pipefail

launcher_dir="${0:A:h}"
model="${MN_MODEL:-god}"
exec "$launcher_dir/.venv/bin/mn" launch --model "$model" pi "$@"
