#!/bin/zsh

set -euo pipefail

launcher_dir="${0:A:h}"
model="${MN_MODEL:-qwen36}"
exec "$launcher_dir/.venv/bin/mn" launch --model "$model" pi "$@"
