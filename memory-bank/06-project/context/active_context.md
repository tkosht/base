# Active Context

## 現在の焦点
- Gradio UI のスレッド選択状態の一貫性改善（新規作成時/サイドバー開閉時）。

## 主な決定事項
- スレッド一覧HTMLに `data-selected` と `selected` クラスを付与し、選択状態をサーバ側で明示的に伝播する。
- `demo.load` およびリフレッシュ関数は `current_thread_id` を入力に取り、HTML生成時に選択を反映する。
- JSは `MutationObserver` によりリストDOM差し替え時に `data-selected` を最優先して選択を復元。フォールバックで `.thread-link.selected` と `window.__selectedTid` を使用。
- サイドバー閉状態で「＋」→ 初回発話→自動タイトル確定時に当該スレッドを選択維持。サイドバー再表示時も `data-selected` を優先して上書きしない。

## 変更概要（関連ファイル）
- `app/app_factory.py`: `_build_threads_html(_tab)` に `selected_tid` を追加、`data-selected` 埋め込み。`demo.load` や `.change()` で `current_thread_id` を渡すよう修正。リネーム/削除後も選択を維持/更新。
- `public/scripts/threads_ui.js`: リスト差し替え検知時と再適用時に `data-selected` を最優先して `markSelectedLists()` を実行。競合上書きを解消。

## テスト観点
- サイドバー閉→「＋」→発話→自動タイトル確定→サイドバー開: 新規スレッドが選択されていること。
- サイドバー開で既存選択→「＋」: 一旦解除→新規発話/タイトル確定で新規スレッド選択に遷移。
- 右クリック/インラインリネーム: 選択維持のままタイトル更新反映。


