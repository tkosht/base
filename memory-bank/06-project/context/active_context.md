# Active Context

## 現在の焦点
- Gradio UI のスレッド選択状態の一貫性改善（新規作成時/サイドバー開閉時）。
- `app_factory.py` スリム化と再配置（段階移行）

## 主な決定事項
- スレッド一覧HTMLに `data-selected` と `selected` クラスを付与し、選択状態をサーバ側で明示的に伝播する。
- `demo.load` およびリフレッシュ関数は `current_thread_id` を入力に取り、HTML生成時に選択を反映する。
- JSは `MutationObserver` によりリストDOM差し替え時に `data-selected` を最優先して選択を復元。フォールバックで `.thread-link.selected` と `window.__selectedTid` を使用。
- サイドバー閉状態で「＋」→ 初回発話→自動タイトル確定時に当該スレッドを選択維持。サイドバー再表示時も `data-selected` を優先して上書きしない。

## 変更概要（関連ファイル）
- `app/app_factory.py`: `_build_threads_html(_tab)` に `selected_tid` を追加、`data-selected` 埋め込み。`demo.load` や `.change()` で `current_thread_id` を渡すよう修正。リネーム/削除後も選択を維持/更新。
- `public/scripts/threads_ui.js`: リスト差し替え検知時と再適用時に `data-selected` を最優先して `markSelectedLists()` を実行。競合上書きを解消。
- `checklists/refactor_app_factory_staged_migration.md`: 段階移行の手順・受け入れ基準・ブランチ運用・PRフローを定義。各ステップで「ブランチ作成」「PR作成・マージ待ち」を明記。

## テスト観点

## 参照導線
- 進行中のリファクタリング手順・最新状態は `checklists/refactor_app_factory_staged_migration.md` を参照。
- サイドバー閉→「＋」→発話→自動タイトル確定→サイドバー開: 新規スレッドが選択されていること。
- サイドバー開で既存選択→「＋」: 一旦解除→新規発話/タイトル確定で新規スレッド選択に遷移。
- 右クリック/インラインリネーム: 選択維持のままタイトル更新反映。


## Scope/Phase（auto-refine-agents）
- 現在フェーズ: MVP
- 達成ゲート: SCOPE-MVP-001〜004 の受け入れ基準
- 参照: `docs/auto-refine-agents/mvp-scope.md`


## 決定事項（auto-refine-agents）
- 三層分離の正式採用:
  - ランタイム（非Git）: `.agent/`（worktree専用、RAG DB含む）
  - 共有正典（Git）: `agent/registry/`（prompts/playbooks/rubrics/config/*.defaults.yaml）
  - 意思決定（Git）: `memory-bank/`（目的/判断/進捗の記録）
- 同期モデル: pull=`agent/registry → .agent` / push=`.agent → PR → agent/registry`（昇格はガバナンス MUST 準拠）
- 設定優先順位: `.agent/config/*` > `agent/registry/config/*.defaults.yaml` > built-in
- 運用手順: Makefile 依存を廃し、`.cursor/commands/agent/*.md` にプロンプトタスクを整備
- RAG 対象: `docs/**.md`, `memory-bank/**.md`（`agent/registry/**` は対象外）
- `.gitignore`: ルートに `.agent/` を明記
- ドキュメント更新: `cli-implementation-design.md`, `worktree-guide.md`, `evaluation-governance.md`, `architecture*.md`
- 新規: `registry-guidelines.md`, `mvp-tracker.md`

