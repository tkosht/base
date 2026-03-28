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

## 3. Branch Deletion Exclusion Rules
削除候補から常に除外する。
- `main`
- `master`
- 現在ブランチ（`git branch` の `*` 行）
- `target_branch`

## 4. Typical Failure Cases
### Case A: Unmerged work remains
- 症状: `git branch -d <branch>` が「not fully merged」で失敗する。
- 対応: `skipped_branches` に記録し、強制削除はしない。

### Case B: No target branch exists
- 症状: `main`/`master` がどちらも存在しない。
- 対応: 処理を停止し、`notes` に対象リポジトリのデフォルトブランチ確認を促す。

### Case C: Remote changed but fast-forward impossible
- 症状: `git pull --ff-only` が失敗する。
- 対応: `sync_status=conflict` として停止し、手動リベースまたはマージ方針をユーザーに確認する。
