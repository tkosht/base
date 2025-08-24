# Progress

## 完了項目
- 新規作成後・初回発話/自動タイトル確定時に新規スレッドへ選択移動（サイドバー開閉に依らず保持）
- サイドバー開状態での「＋」の既存OK挙動の維持
- リネーム時の選択維持（右クリック/インライン/F2 含む）

## 実装ポイント
- HTML側に `data-selected` を埋め込み、`selected` クラスもサーバ生成で反映
- JSで `data-selected` を最優先に選択を復元し、`window.__selectedTid` はフォールバックに限定
- `current_thread_id` を各リフレッシュ/ロードに渡すようにして選択伝播

## 変更ファイル
- `app/app_factory.py`
- `public/scripts/threads_ui.js`
- `memory-bank/06-project/context/active_context.md`

## 今後の改善候補
- 新規作成直後（発話前）からの即選択切替の仕様可否を検討（`_on_new` での選択反映）
- E2E テスト（Playwright 等）でのUI選択状態の自動検証の追加
