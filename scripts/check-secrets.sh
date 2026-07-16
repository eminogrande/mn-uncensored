#!/bin/zsh

set -euo pipefail

repo_dir="${0:A:h:h}"
cd "$repo_dir"

files=("${(@f)$(git diff --cached --name-only --diff-filter=ACMR)}")
files=("${(@)files:#}")
if (( ${#files} == 0 )); then
  files=("${(@f)$(git ls-files --cached --others --exclude-standard)}")
  files=("${(@)files:#}")
fi

(( ${#files} == 0 )) && exit 0

patterns=(
  'sk-mn-[A-Za-z0-9_-]{20,}'
  'MODAL_PROXY_(KEY|SECRET)=[A-Za-z0-9_-]{8,}'
  '(^|[^A-Za-z0-9])(wk|ws)-[A-Za-z0-9_-]{8,}'
  'hf_[A-Za-z0-9]{20,}'
)

for pattern in "${patterns[@]}"; do
  if rg --line-number --no-heading --color never --regexp "$pattern" -- "${files[@]}"; then
    print -u2 "Potential secret found. Refusing to continue."
    exit 1
  fi
done

print "Secret scan passed."
