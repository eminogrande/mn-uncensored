#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"
target="${1:-}"
version="${2:-}"

if [[ "$target" != "catalog" ]]; then
  print -u2 "Usage: $0 catalog <vX.Y.Z>"
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

[[ "$(git config gpg.format)" == "ssh" ]]
[[ "$(git config commit.gpgsign)" == "true" ]]
[[ "$(git config tag.gpgsign)" == "true" ]]
[[ -n "$(git config user.signingkey)" ]]
[[ -n "$(git config gpg.ssh.allowedSignersFile)" ]]
[[ "$(git log -1 '--format=%G?')" == "G" ]] || {
  print -u2 "HEAD must have a verified signature."
  exit 1
}

git rev-parse "$version" >/dev/null 2>&1 && {
  print -u2 "Tag $version already exists."
  exit 1
}

.venv/bin/python -m pytest -q
./scripts/check-secrets.sh

deploy_backend() {
  local model="$1"
  print "Deploying MN backend: $model"
  MN_MODEL="$model" PYTHONPATH="$repo_dir/src" \
    .venv/bin/modal deploy modal_vllm.py --tag "$version-$model"
}

deploy_gateway() {
  print "Deploying MN catalog gateway"
  PYTHONPATH="$repo_dir/src" \
    .venv/bin/modal deploy modal_gateway.py --tag "$version-gateway"
}

deploy_backend god
deploy_backend code
deploy_backend fast
deploy_gateway

cleanup_models() {
  .venv/bin/mn stop || true
}
trap cleanup_models EXIT

.venv/bin/mn auto
for model in god code fast; do
  PYTHONPATH="$repo_dir/src" .venv/bin/python scripts/smoke-catalog.py "$model"
  .venv/bin/mn stop "$model"
done
.venv/bin/mn auto

trap - EXIT

git tag -s "$version" -m "MN Uncensored $version"
git push origin HEAD
git push origin "$version"
gh release create "$version" --generate-notes --title "MN Uncensored $version"
