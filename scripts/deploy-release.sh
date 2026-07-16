#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"
target="${1:-}"
version="${2:-}"

if [[ "$target" != "gateway" && "$target" != "backend" ]]; then
  print -u2 "Usage: $0 <gateway|backend> <vX.Y.Z>"
  exit 2
fi
if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  print -u2 "Version must look like v1.2.3."
  exit 2
fi

cd "$repo_dir"

[[ -z "$(git status --porcelain)" ]] || {
  print -u2 "Working tree must be clean before deployment."
  exit 1
}

[[ "$(git config --global gpg.format)" == "ssh" ]]
[[ "$(git config --global commit.gpgsign)" == "true" ]]
[[ "$(git config --global tag.gpgsign)" == "true" ]]

git rev-parse "$version" >/dev/null 2>&1 && {
  print -u2 "Tag $version already exists."
  exit 1
}

.venv/bin/python -m pytest -q
./scripts/check-secrets.sh

if [[ "$target" == "gateway" ]]; then
  PYTHONPATH="$repo_dir/src" .venv/bin/modal deploy modal_gateway.py --tag "$version"
else
  set -a
  source deployment.env
  set +a
  .venv/bin/modal deploy modal_vllm.py --tag "$version"
fi

git tag -s "$version" -m "MN Uncensored $version"
git push origin HEAD
git push origin "$version"
gh release create "$version" --generate-notes --title "MN Uncensored $version"
