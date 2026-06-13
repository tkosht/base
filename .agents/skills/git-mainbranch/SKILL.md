---
name: git-mainbranch
description: "Pull Request マージ後に main/master へ戻し、リモート同期とマージ済みローカルブランチの安全削除を実行する。ユーザーが『mainに戻す』『マージ後の掃除』『作業ブランチ削除』『main同期』を求めるときに使う。git-commit-pr の後処理専用。"
---

# Git Mainbranch

## Purpose
- PR マージ後の後処理を、安全に再現できる手順へ固定する。
- `git-commit-pr` の後段のみを担当し、コミット作成や PR 作成は扱わない。

## Required Output
- `current_branch`: 開始時のブランチ名
- `target_branch`: 切り替え先 (`main` または `master`)
- `sync_status`: `up_to_date` / `updated` / `conflict`
- `removed_worktrees`: 不要と確認して削除した worktree path
- `skipped_worktrees`: dirty、locked、用途不明などで削除しなかった worktree path と理由
- `deleted_branches`: `git branch -d` で削除できたローカルブランチ
- `force_deleted_branches`: Pull Request（PR）merge、upstream/remote branch gone、worktree 不在、merged PR の `headRefName` が `<branch>` と一致し、`headRefOid` が `git rev-parse <branch>` と一致し、`baseRefName` が `<target_branch>` と一致し、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することを確認し、`git branch -D` で削除したローカルブランチ
- `force_delete_candidates`: squash merge などで `git branch -d` できず、obsolete の可能性はあるが、自動削除に必要な客観証拠が不足しているため保持したブランチと理由
- `skipped_branches`: 未マージ、所有不明などで削除しなかったローカルブランチ
- `notes`: 競合や手動対応が必要な項目

## Workflow
1. 作業開始時のブランチを取得する。
   - `git branch --show-current` を実行し、`current_branch` に格納する。
2. 目標ブランチを決定する。
   - `main` が存在すれば `target_branch=main`。
   - `main` が無く `master` が存在すれば `target_branch=master`。
   - どちらも無ければ停止し、`notes` に記録して終了する。
3. 目標ブランチへ切り替える。
   - `git switch <target_branch>` を実行する。
4. GitHub HTTPS authentication preflight を実行する。
   - `git fetch --prune`、`git pull --ff-only`、`gh pr list` を含む branch cleanup の前に必ず実行する。
   - `git remote get-url --push origin` を実行し、失敗または空の場合だけ `git remote get-url origin` を fallback として実行する。
   - remote URL が `https://github.com/` で始まる GitHub HTTPS remote の場合、`gh auth status -h github.com` を実行する。
   - 結果が認証なし、または non-zero で `not logged in` を示す場合は local GitHub HTTPS authentication is known missing と判断する。
   - この場合は fetch、pull、`gh pr list`、worktree cleanup、branch deletion を行わず停止する。
   - 停止時は「GitHub HTTPS authentication is required. Run `gh auth login -h github.com`, choose/enable HTTPS Git operations, then retry.」とユーザーへ伝える。
   - 認証済みを確認できた場合だけ次へ進む。
5. リモート同期を行う。
   - `git fetch --prune` を実行する。
   - `git pull --ff-only` を実行する。
   - `git pull --ff-only` が失敗した場合は `sync_status=conflict` として停止し、競合解消手順を `notes` に出力する。
   - 成功時は出力に応じて `sync_status` を `up_to_date` または `updated` に設定する。
6. worktree 状態を確認する。
   - `git worktree list --porcelain` を実行する。
   - 削除候補ブランチが別 worktree で checkout されている場合は、先にその worktree を評価する。
   - `git -C <path> status --porcelain` が空で、PR が merge 済みまたは remote branch が gone であり、現在の task 用に作成した一時 worktree だと確認できる場合だけ `git worktree remove <path>` を実行し、`removed_worktrees` に記録する。
   - dirty、locked、用途不明、ユーザー所有の可能性がある worktree は削除せず、`skipped_worktrees` に理由を記録する。
   - worktree を削除できなかった候補ブランチは削除せず、`skipped_branches` または `force_delete_candidates` に理由を記録する。
7. 削除対象ブランチを抽出する。
   - `git branch --merged <target_branch>` と `git branch -vv` の両方を使う。
   - `main`、`master`、`<target_branch>`、現在ブランチ（`*` が付く行）を除外する。
   - `git branch --merged <target_branch>` に出る候補は `git branch -d` 対象にする。
   - squash merge 済みブランチは `git branch --merged <target_branch>` に出ないため、`git branch -vv` で upstream が gone のローカルブランチを抽出し、`gh pr list --state merged --search "head:<branch>" --json number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeCommit` で PR merge、merged PR head、merge 先を確認する。
   - force delete の客観証拠は、PR merged、upstream/remote branch gone、残存 worktree で checkout されていないこと、merged PR の `headRefName` が `<branch>` と一致すること、`headRefOid` が `git rev-parse <branch>` と一致すること、`baseRefName` が `<target_branch>` と一致すること、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することのすべてとする。
   - 証拠が 1 つでも不足する場合は削除せず、`force_delete_candidates` に不足証拠の理由を記録する。
8. マージ済みローカルブランチを安全削除する。
   - `git branch -d` 対象の候補ごとに `git branch -d <branch>` を実行する。
   - 削除成功は `deleted_branches` に追加する。
   - 削除失敗は `skipped_branches` に理由付きで追加し、次の候補へ進む。
9. 客観証拠が揃った force delete 候補を削除する。
   - PR merged、upstream/remote branch gone、残存 worktree で checkout されていないこと、merged PR の `headRefName` が `<branch>` と一致すること、`headRefOid` が `git rev-parse <branch>` と一致すること、`baseRefName` が `<target_branch>` と一致すること、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することを実行直前に再確認する。
   - すべての証拠を確認できる候補は、追加のユーザー承認を求めず `git branch -D <branch>` を実行し、`force_deleted_branches` に記録する。
   - 再確認に失敗した候補は削除せず、`skipped_branches` に理由を記録する。
10. Required Output を返す。

## Guardrails
- `git branch -D` は、PR merged、upstream/remote branch gone、残存 worktree で checkout されていないこと、merged PR の `headRefName` が `<branch>` と一致すること、`headRefOid` が `git rev-parse <branch>` と一致すること、`baseRefName` が `<target_branch>` と一致すること、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することを確認できる場合だけ使う。
- 上記の客観証拠が揃った obsolete branch は、ユーザーへの追加確認を求めず削除する。
- 証拠欠落をユーザー承認で補わない。証拠が不足する場合は削除せず、`force_delete_candidates` または `skipped_branches` に理由を記録する。
- `git worktree remove --force` を使わない。
- `git reset --hard`、`git push --force` を使わない。
- リモートブランチ削除（`git push --delete`）を既定で実行しない。
- 競合時は自動解消せず、`sync_status=conflict` と `notes` で手動対応へ切り替える。
- 確認できない情報は推測せず `unknown` または `n/a` とする。

## References
- `references/mainbranch-playbook.md`
