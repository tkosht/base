---
name: git-commit-pr
description: "コミット・プッシュ・プルリクエスト作成を一気通貫で実行する。ユーザーが『コミットして』『pushしてPRを作って』『変更をまとめて提出して』などを依頼したときに使う。変更内容を確認し、main/master では作業ブランチを作成し、定義済みフォーマットでコミットメッセージを作り、最後に PR URL を報告する。"
---

# Git Commit PR

## Purpose
- `commit -> push -> PR 作成` を再現可能な手順で完了する。
- 実行結果として PR URL を必ず返す。

## Required Output
- `branch`: 使用した作業ブランチ名
- `commit`: 作成したコミットハッシュ（短縮可）
- `pr_url`: 発行した Pull Request URL
- `summary`: 変更要約（1-3行）
- `lint_status`: `pass` または `fail`
- `lint_commands`: 実行した lint コマンド一覧

## Workflow
1. 作業ブランチを準備する。
   - `git branch --show-current` を実行する。
   - ブランチが `main` または `master` の場合は `task/<topic>` または `fix/<topic>` で作業ブランチを作成し、切り替える。
   - `<topic>` は小文字英数字とハイフンに正規化する。

2. 変更を精緻に把握する。
   - 次を実行する。
     - `git status --short --branch`
     - `git diff --stat`
     - `git diff --cached --stat`
   - 変更ファイルを読み、変更の背景・主変更点・検証内容を抽出する。
   - 差分がない場合は `nothing to commit` として終了する。

3. コミットメッセージ形式を選ぶ。
   - `references/commit-message-formats.md` を参照する。
   - 原則は `simple` 形式を使う。
   - 変更が小さく意図が自明な場合のみ `super-light` 形式を使う。
   - すべて事実ベースで埋める。不要な行は削除する。

4. Preflight Lint Gate を実行する。
   - 次を順番に実行する。
     - `uv run ruff check .`
     - `uv run black --check .`
   - `black --check` が失敗した場合はコミットを中断する。
   - 失敗したファイルへ `uv run black <path...>` を実行し、再度 gate を通す。
   - 失敗箇所が `.codex/skills/.system/**` のみであれば、local system skill の未整形が原因なので対象ファイルをローカル整形してから再実行する。
   - `.codex/*` は `.gitignore` 対象のため、`.codex/skills/.system/**` の整形結果は通常コミットに含めない。
   - `lint_status=pass` を確認するまでコミットしない。

5. ステージングしてコミットする。
   - ユーザーから部分コミットの指示がない限り `git add -A` を使う。
   - 複数行メッセージはヒアドキュメントで渡す。
   - 例:
     ```bash
     git commit -F - <<'EOF'
     <message>
     EOF
     ```
   - 失敗した場合は原因を解消してから再実行する。

6. リモートへプッシュする。
   - 初回プッシュは `git push -u origin <branch>` を使う。
   - 追跡設定済みなら `git push` を使う。

7. Pull Request を作成する。
   - タイトルはコミット要約から作る。
   - 本文は `references/pr-body-template.md` を使って作る。
   - 推奨コマンド:
     ```bash
     gh pr create --title "<title>" --body "<body>"
     ```
   - URL を必ず取得する。
   - 既存 PR がある場合は `gh pr view --json url -q .url` で URL を返す。

8. 結果を報告する。
   - `branch` / `commit` / `pr_url` / `summary` / `lint_status` / `lint_commands` を返す。
   - テスト未実施などの注意点があれば明記する。

## Guardrails
- 秘密情報、トークン、`.env` 値をコミットメッセージや PR 本文に含めない。
- ユーザーが作成した無関係の変更は巻き戻さない。
- 明示依頼なしで破壊的操作（`reset --hard`、`push --force` など）を行わない。
- 推測で埋めず、確認できない情報は `unknown` または `n/a` とする。
- lint 未通過の状態でコミットや PR 作成をしない。

## References
- `references/commit-message-formats.md`
- `references/pr-body-template.md`
