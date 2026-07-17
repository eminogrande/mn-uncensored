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
if [[ "${MN_RELEASE_ORNITH397:-}" != "I_ACCEPT_2XH200" ]]; then
  print -u2 "This release includes cebeuq/Ornith-1.0-397B-abliterated-W4A16 on 2 x H200."
  print -u2 "Confirm the Modal hard budget, then set:"
  print -u2 "MN_RELEASE_ORNITH397=I_ACCEPT_2XH200"
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
[[ "$(PYTHONPATH="$repo_dir/src" .venv/bin/python -c 'from mn_uncensored.settings import load_settings; print(load_settings().models["ornith397"].deployment_enabled)')" == "True" ]] || {
  print -u2 "ornith397 must be explicitly enabled in the signed budget-approved release."
  exit 2
}
release_notes="$(
  .venv/bin/python scripts/extract-release-notes.py "$version"
)"

cleanup_models() {
  .venv/bin/mn stop || true
}
trap cleanup_models EXIT

# Fail closed before any app deployment. This updates every lifecycle record
# to stopped and terminates any pending or running backend containers.
.venv/bin/mn stop

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

deploy_backend qwen36
deploy_backend ornith35
deploy_backend qwythos9
deploy_backend ornith397
deploy_gateway

for model in qwen36 ornith35 qwythos9 ornith397; do
  if [[ "$model" == "ornith397" ]]; then
    .venv/bin/mn auto "$model" --allow-expensive
  else
    .venv/bin/mn auto "$model"
  fi
  PYTHONPATH="$repo_dir/src" .venv/bin/python scripts/smoke-catalog.py "$model"
  .venv/bin/mn stop "$model"
done

trap - EXIT

git tag -s "$version" -m "MN Uncensored $version"
git push origin HEAD
git push origin "$version"
gh release create "$version" \
  --title "MN Uncensored $version" \
  --notes "$release_notes"
