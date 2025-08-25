## 2025-08-24 UIテーマ不一致時の可読性改善（Gradio × Chrome）

- 問題:
  - Chrome(OS/ブラウザ)のテーマと Gradio の `__theme` が不一致のとき、スレッド一覧の非選択タイトルが極端に読みにくくなる。
  - 特に「Chrome: ダーク × Gradio: ライト」で顕著。

- 原因:
  - OSテーマに基づく `prefers-color-scheme` と Gradio のライト/ダーク指定が競合し、色の継承と不透明度が意図せず薄くなるケースがある。
  - 一部スタイルの優先度不足により、意図しない半透明化/色が残留。

- 解決:
  1) 実UIの背景明度で `ui-light`/`ui-dark` を自動判定するブリッジを導入。
     - 実装: `public/scripts/theme_bridge.js`
     - 優先順: URLの `__theme` パラメータ(light/dark)を最優先 → なければ背景色の相対輝度で判定
  2) `ui-light`/`ui-dark` に紐づく強制スタイルを追加し、非選択タイトルの文字色/不透明度を確実に上書き。
     - 実装: `public/styles/app.css`
     - ポイント: `.thread-link * { opacity:1 }`、`.thread-title` の色と太字化、selected行の背景/枠線を明示
  3) 既存のインラインCSS/JSは整理して外部に集約。

- 変更ファイル:
  - `app/app_factory.py`: head へ `theme_bridge.js` を読み込み。インラインのテーマ補正を削除。
  - `public/scripts/theme_bridge.js`: 新規。UIテーマブリッジ。
  - `public/styles/app.css`: `html.ui-light` / `html.ui-dark` セレクタで強制上書き追加。

- 検証結果:
  - 4パターンすべてで可読性OK
    - Chrome: ダーク × Gradio: ダーク → OK
    - Chrome: ダーク × Gradio: ライト → OK
    - Chrome: ライト × Gradio: ライト → OK
    - Chrome: ライト × Gradio: ダーク → OK

- 今後の運用/メモ:
  - SPA的な再描画で背景が変わる場合に備え、`theme_bridge.js` は `load/focus/timeout` で複数回評価。
  - 将来的にテーマ切替UIを追加する場合は、切替時に `applyUiMode()` を明示的に呼ぶと即反映される。

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

## リファクタリング進捗（app_factory スリム化・再配置）
- チェックリスト: `checklists/refactor_app_factory_staged_migration.md`（段階移行の手順・受け入れ基準・PRフローを記載）
- 現在のステータス:
  - Step 0: 完了（ベースライン検証、/gradio 307許容に更新）
  - Step 1: 実装中（assets抽出、`app/web/assets.py` 追加し `create_api_app()` から委譲）
  - 次ステップ: Step 1 のPR作成・マージ後に Step 2（APIルーター分離）
