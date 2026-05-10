# Mainbranch Playbook

## 1. Target Branch Resolution
- `main` を優先する。
- `main` が無い場合だけ `master` を使う。
- 判定コマンド例:
  - `git show-ref --verify --quiet refs/heads/main`
  - `git show-ref --verify --quiet refs/heads/master`

## 2. Sync Failure (`pull --ff-only`) Handling
- `git pull --ff-only` が失敗した場合は、ブランチ削除へ進まない。
- まず状態を確認する。
  - `git status --short --branch`
  - `git log --oneline --decorate --graph -20`
  - `git branch -vv`
- 競合/分岐を解消した後に、再度 `git pull --ff-only` を実行する。

## 3. Worktree Cleanup Before Branch Deletion
- `git branch -d <branch>` の前に `git worktree list --porcelain` を確認する。
- 削除候補ブランチが別 worktree で checkout されている場合、まずその worktree を評価する。
- 次のすべてを満たす場合だけ `git worktree remove <path>` を実行する。
  - `git -C <path> status --porcelain` が空である。
  - PR が merge 済み、または remote branch が gone である。
  - 現在の task 用に作成した一時 worktree だと説明できる。
- dirty、locked、用途不明、ユーザー所有の可能性がある worktree は削除しない。
- `git worktree remove --force` は使わない。

## 4. Branch Deletion Exclusion Rules
削除候補から常に除外する。
- `main`
- `master`
- 現在ブランチ（`git branch` の `*` 行）
- `target_branch`

## 5. Typical Failure Cases
### Case A: Unmerged work remains
- 症状: `git branch -d <branch>` が「not fully merged」で失敗する。
- 対応: PR merge、remote branch gone、worktree 削除済みを確認できる場合は `force_delete_candidates` に記録する。`git branch -D` はユーザーが明示承認した場合だけ使う。

### Case B: No target branch exists
- 症状: `main`/`master` がどちらも存在しない。
- 対応: 処理を停止し、`notes` に対象リポジトリのデフォルトブランチ確認を促す。

### Case C: Remote changed but fast-forward impossible
- 症状: `git pull --ff-only` が失敗する。
- 対応: `sync_status=conflict` として停止し、手動リベースまたはマージ方針をユーザーに確認する。

### Case D: Branch is checked out in an obsolete worktree
- 症状: `git branch -d <branch>` が「used by worktree」で失敗する。
- 対応: worktree が clean で task 用の一時 worktree だと確認できる場合は、先に `git worktree remove <path>` を実行してから `git branch -d <branch>` を再試行する。
