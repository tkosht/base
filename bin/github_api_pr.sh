#!/usr/bin/env bash
set -euo pipefail

if [[ -f ./.env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"

remote_url="${GITHUB_REMOTE_URL:-$(git config --get remote.origin.url)}"
repo_slug="${GITHUB_REPOSITORY:-}"

if [[ -z "$repo_slug" ]]; then
  if [[ "$remote_url" =~ github.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    repo_slug="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  else
    echo "Could not resolve GitHub owner/repo from remote.origin.url" >&2
    exit 1
  fi
fi

pr_limit="${PR_LIMIT:-10}"

pr_url_list=$(
  curl -sSL \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$repo_slug/pulls?state=all&per_page=$pr_limit" \
    | jq -r '.[].url'
)

for url in $pr_url_list
do
  curl -sSL \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GITHUB_TOKEN" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$url"
  break
done
