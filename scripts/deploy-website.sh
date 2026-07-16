#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"
version="${1:-}"
temp_dir=""
worktree_dir=""
tag_created=false
tag_pushed=false

if [[ ! "$version" =~ ^website-v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  print -u2 "Usage: $0 website-vX.Y.Z"
  exit 2
fi

cleanup() {
  if [[ "$tag_created" == "true" && "$tag_pushed" != "true" ]]; then
    git -C "$repo_dir" tag -d "$version" >/dev/null 2>&1 || true
  fi
  if [[ -n "$worktree_dir" && -d "$worktree_dir" ]]; then
    git -C "$repo_dir" worktree remove --force "$worktree_dir" || true
  fi
  if [[ -n "$temp_dir" && -d "$temp_dir" ]]; then
    rmdir "$temp_dir" 2>/dev/null || true
  fi
}
trap cleanup EXIT

cd "$repo_dir"

[[ "$(git branch --show-current)" == "main" ]] || {
  print -u2 "Website deployments must start from main."
  exit 1
}
[[ -z "$(git status --porcelain)" ]] || {
  print -u2 "Working tree must be clean before deployment."
  exit 1
}
[[ "$(git config gpg.format)" == "ssh" ]]
[[ "$(git config commit.gpgsign)" == "true" ]]
[[ "$(git config tag.gpgsign)" == "true" ]]
[[ "$(git config user.signingkey)" == \
  "/Users/eminmahrt/.ssh/github_signing_ed25519.pub" ]]
[[ -n "$(git config gpg.ssh.allowedSignersFile)" ]]

git fetch origin main gh-pages --tags
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || {
  print -u2 "Local main must exactly match origin/main."
  exit 1
}
[[ "$(git log -1 '--format=%G?')" == "G" ]] || {
  print -u2 "HEAD must have a verified signature."
  exit 1
}
[[ "$(git log -1 '--format=%G?' origin/gh-pages)" == "G" ]] || {
  print -u2 "The current origin/gh-pages tip must have a verified signature."
  exit 1
}

git rev-parse "$version" >/dev/null 2>&1 && {
  print -u2 "Tag $version already exists."
  exit 1
}
git ls-remote --exit-code --tags origin "refs/tags/$version" >/dev/null 2>&1 && {
  print -u2 "Remote tag $version already exists."
  exit 1
}
gh release view "$version" >/dev/null 2>&1 && {
  print -u2 "GitHub release $version already exists."
  exit 1
}

release_notes="website/releases/$version.md"
[[ -f "$release_notes" ]] || {
  print -u2 "Missing curated release notes: $release_notes"
  exit 1
}
[[ -f website/index.html && -f website/.nojekyll ]]
[[ -z "$(find website -type l -print -quit)" ]] || {
  print -u2 "Symlinks are not allowed in the website deployment."
  exit 1
}

[[ "$(gh api "repos/{owner}/{repo}/pages" --jq .build_type)" == "legacy" ]]
[[ "$(gh api "repos/{owner}/{repo}/pages" --jq .source.branch)" == "gh-pages" ]]
[[ "$(gh api "repos/{owner}/{repo}/pages" --jq .source.path)" == "/" ]]
pages_url="$(gh api "repos/{owner}/{repo}/pages" --jq .html_url)"
pages_cname="$(gh api "repos/{owner}/{repo}/pages" --jq '.cname // ""')"
if [[ -z "$pages_cname" ]]; then
  [[ ! -e website/CNAME ]] || {
    print -u2 "Pages has no custom domain, but website/CNAME exists."
    exit 1
  }
else
  [[ -f website/CNAME && "$(<website/CNAME)" == "$pages_cname" ]] || {
    print -u2 "website/CNAME does not match the configured Pages domain."
    exit 1
  }
fi

.venv/bin/python -m pytest -q
./scripts/check-secrets.sh

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/mn-website-deploy.XXXXXX")"
worktree_dir="$temp_dir/site"
git worktree add --detach "$worktree_dir" origin/gh-pages

rsync -a --delete --exclude=".git" website/ "$worktree_dir/"
[[ -z "$(rsync -ani --delete --exclude=".git" website/ "$worktree_dir/")" ]]
git -C "$worktree_dir" add -A

if git -C "$worktree_dir" diff --cached --quiet; then
  print -u2 "The deployed website already matches website/."
  exit 1
fi

source_sha="$(git rev-parse HEAD)"
git -C "$worktree_dir" commit -S \
  -m "deploy: ABLITERATED.cloud $version" \
  -m "Source: $source_sha"
deploy_sha="$(git -C "$worktree_dir" rev-parse HEAD)"
[[ "$(git -C "$worktree_dir" log -1 '--format=%G?')" == "G" ]]

git tag -s "$version" "$deploy_sha" -m "ABLITERATED.cloud $version"
tag_created=true
git verify-tag "$version"
git push --atomic origin \
  "$deploy_sha:refs/heads/gh-pages" \
  "refs/tags/$version"
tag_pushed=true

owner_repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
build_verified=false
for attempt in {1..36}; do
  latest_commit="$(
    gh api "repos/$owner_repo/pages/builds/latest" --jq .commit
  )"
  latest_status="$(
    gh api "repos/$owner_repo/pages/builds/latest" --jq .status
  )"
  if [[ "$latest_commit" == "$deploy_sha" && "$latest_status" == "built" ]]; then
    build_verified=true
    break
  fi
  if [[ "$latest_commit" == "$deploy_sha" && "$latest_status" == "errored" ]]; then
    print -u2 "GitHub Pages reported an errored build for $deploy_sha."
    exit 1
  fi
  sleep 5
done
[[ "$build_verified" == "true" ]] || {
  print -u2 "Timed out waiting for the GitHub Pages build."
  exit 1
}
curl -fsSI "$pages_url" >/dev/null

gh release create "$version" \
  --verify-tag \
  --title "ABLITERATED.cloud $version" \
  --notes-file "$release_notes"

print "Published $version to GitHub Pages from signed commit:"
print "$deploy_sha"
print "Created signed tag and GitHub release: $version"
print "Verified GitHub Pages build and HTTP 200: $pages_url"
print "The website deploy does not invoke Modal or start a GPU."
