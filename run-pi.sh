#!/bin/zsh

set -euo pipefail

launcher_dir="${0:A:h}"
exec "$launcher_dir/.venv/bin/mn" launch pi "$@"
