#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"

cd "$repo_dir"
uv sync
mkdir -p "$HOME/.local/bin"
ln -sfn "$repo_dir/.venv/bin/mn" "$HOME/.local/bin/mn"

print "Installed MN Uncensored as: $HOME/.local/bin/mn"
print "If needed, add $HOME/.local/bin to PATH."
