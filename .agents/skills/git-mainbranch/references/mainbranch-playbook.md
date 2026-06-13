# Mainbranch Playbook

## 1. Target Branch Resolution
- `main` を優先する。
- `main` が無い場合だけ `master` を使う。
- 判定コマンド例:
  - `git show-ref --verify --quiet refs/heads/main`
  - `git show-ref --verify --quiet refs/heads/master`

## 2. GitHub HTTPS authentication preflight
- `git fetch --prune`、`git pull --ff-only`、`gh pr list` を含む branch cleanup の前に必ず実行する。
- fetch URL は `git remote get-url origin` で取得し、`git fetch --prune` と `git pull --ff-only` の認証判定には必ず fetch URL を使う。
- push URL は `git remote get-url --push origin` で取得し、失敗または空の場合だけ fetch URL を fallback として使う。
- fetch URL が `https://github.com/` で始まる GitHub HTTPS remote の場合、`gh auth status -h github.com` を実行する。
- fetch URL または push URL が `git@github.com:` または `ssh://git@github.com/` で始まる GitHub SSH remote の場合も、`gh pr list` には GitHub CLI authentication が必要なため `gh auth status -h github.com` を実行する。
- 結果が認証なし、または non-zero で `not logged in` を示す場合は local GitHub HTTPS authentication is known missing と判断する。
- この場合は fetch、pull、`gh pr list`、worktree cleanup、branch deletion を行わず停止する。
- 停止時は「GitHub HTTPS authentication is required. Run `gh auth login -h github.com`, choose/enable HTTPS Git operations, then retry.」とユーザーへ伝える。
- 認証済みを確認できた場合だけ次へ進む。

## 3. Sync Failure (`pull --ff-only`) Handling
- `git pull --ff-only` が失敗した場合は、ブランチ削除へ進まない。
- まず状態を確認する。
  - `git status --short --branch`
  - `git log --oneline --decorate --graph -20`
  - `git branch -vv`
- 競合/分岐を解消した後に、再度 `git pull --ff-only` を実行する。

## 4. Worktree Cleanup Before Branch Deletion
- `git branch -d <branch>` の前に `git worktree list --porcelain` を確認する。
- 削除候補ブランチが別 worktree で checkout されている場合、まずその worktree を評価する。
- 次のすべてを満たす場合だけ `git worktree remove <path>` を実行する。
  - `git -C <path> status --porcelain` が空である。
  - PR が merge 済み、または remote branch が gone である。
  - 現在の task 用に作成した一時 worktree だと説明できる。
- dirty、locked、用途不明、ユーザー所有の可能性がある worktree は削除しない。
- `git worktree remove --force` は使わない。
- worktree を削除できない場合、そのブランチは force delete しない。`skipped_worktrees` と `skipped_branches` または `force_delete_candidates` に理由を残す。
- worktree 削除後は `git worktree list --porcelain` を再確認し、残存 worktree で対象ブランチが checkout されていないことを branch deletion の証拠にする。

## 5. Branch Deletion Exclusion Rules
削除候補から常に除外する。
- `main`
- `master`
- 現在ブランチ（`git branch` の `*` 行）
- `target_branch`

## 6. Candidate Collection
- 通常削除候補は `git branch --merged <target_branch>` から集める。
- squash merge 済みブランチは ancestry 上 merge 済みではないため、`git branch --merged <target_branch>` だけでは見つからない。
- `git branch -vv` で upstream が gone のローカルブランチを抽出し、`gh pr list --state merged --search "head:<branch>" --json number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeCommit` で PR merge、merged PR head、merge 先を確認する。
- force delete の客観証拠は、remote branch gone と PR merge の両方、対象 worktree が残っていないこと、merged PR の `headRefName` が `<branch>` と一致すること、`headRefOid` が `git rev-parse <branch>` と一致すること、`baseRefName` が `<target_branch>` と一致すること、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することのすべてとする。
- すべての証拠を確認できる obsolete branch は、追加のユーザー承認を求めず `git branch -D <branch>` を実行し、`force_deleted_branches` に記録する。
- 証拠が 1 つでも不足する場合は削除せず、`force_delete_candidates` に不足証拠の理由を記録する。証拠欠落をユーザー承認で補わない。

## 7. Typical Failure Cases
### Case A: Unmerged work remains
- 症状: `git branch -d <branch>` が「not fully merged」で失敗する。
- 対応: PR merged、upstream/remote branch gone、残存 worktree で checkout されていないこと、merged PR の `headRefName` が `<branch>` と一致すること、`headRefOid` が `git rev-parse <branch>` と一致すること、`baseRefName` が `<target_branch>` と一致すること、`git merge-base --is-ancestor <mergeCommit.oid> <target_branch>` が成功することを確認できる場合だけ `git branch -D <branch>` を実行し、`force_deleted_branches` に記録する。証拠が不足する場合は削除せず、`force_delete_candidates` に理由を記録する。

### Case B: No target branch exists
- 症状: `main`/`master` がどちらも存在しない。
- 対応: 処理を停止し、`notes` に対象リポジトリのデフォルトブランチ確認を促す。

### Case C: Remote changed but fast-forward impossible
- 症状: `git pull --ff-only` が失敗する。
- 対応: `sync_status=conflict` として停止し、手動リベースまたはマージ方針をユーザーに確認する。

### Case D: Branch is checked out in an obsolete worktree
- 症状: `git branch -d <branch>` が「used by worktree」で失敗する。
- 対応: worktree が clean で task 用の一時 worktree だと確認できる場合は、先に `git worktree remove <path>` を実行してから `git branch -d <branch>` または証拠が揃った `git branch -D <branch>` を再試行する。worktree safety 条件を満たさない場合は branch deletion も skip する。
