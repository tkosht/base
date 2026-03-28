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
- `deleted_branches`: `git branch -d` で削除できたローカルブランチ
- `skipped_branches`: 未マージなどで削除しなかったローカルブランチ
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
4. リモート同期を行う。
   - `git fetch --prune` を実行する。
   - `git pull --ff-only` を実行する。
   - `git pull --ff-only` が失敗した場合は `sync_status=conflict` として停止し、競合解消手順を `notes` に出力する。
   - 成功時は出力に応じて `sync_status` を `up_to_date` または `updated` に設定する。
5. 削除対象ブランチを抽出する。
   - `git branch --merged <target_branch>` の結果を使う。
   - `main`、`master`、`<target_branch>`、現在ブランチ（`*` が付く行）を除外する。
6. マージ済みローカルブランチを安全削除する。
   - 候補ごとに `git branch -d <branch>` を実行する。
   - 削除成功は `deleted_branches` に追加する。
   - 削除失敗は `skipped_branches` に理由付きで追加し、次の候補へ進む。
7. Required Output を返す。

## Guardrails
- `git branch -D` を使わない。
- `git reset --hard`、`git push --force` を使わない。
- リモートブランチ削除（`git push --delete`）を既定で実行しない。
- 競合時は自動解消せず、`sync_status=conflict` と `notes` で手動対応へ切り替える。
- 確認できない情報は推測せず `unknown` または `n/a` とする。

## References
- `references/mainbranch-playbook.md`
