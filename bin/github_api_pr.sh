#!/usr/bin/sh

. ./.env

OWNER=tkosht
REPO=base
N=10

pr_url_list=$(
curl -sSL \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=all&per_page=$N" \
  | jq -r '.[].url'
)

for url in $pr_url_list
do
    curl -sSL \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $GITHUB_TOKEN" \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      $url
    break
done
