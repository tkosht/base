# 段階移行チェックリスト: app_factory スリム化と再配置

このチェックリストは `app/app_factory.py` の責務分割と関連モジュールの再配置を、動作保証しながら段階的に実施するためのものです。各ステップには「実施項目」「受け入れ基準（テスト）」「ロールバック」が定義されています。実装は小さく区切り、各ステップ完了時にユーザー検証（手動テスト）を挟みます。

## 目的 / 範囲
- 目的: 肥大化した `app/app_factory.py` をスリム化し、API層/静的資産/Gradio UI を適切なサブディレクトリへ再配置
- 範囲: ルーティング/UI/イベント順序/レスポンス形/elem_id は互換維持（挙動変更なし）

## 不変条件（必ず守る）
- ルート/パス: `/gradio`, `/public`, `/manifest.json`, `/favicon.ico`, `/api/...` は不変
- UI契約: `elem_id` / `elem_classes` と外部 `threads_ui.js` の契約は不変
- レスポンス: dict構造とHTTPステータスは不変
- 文言/イベント順序: 既存と同一（submit→guard→rename→stream→status reset）

## ブランチ/品質ゲート
- 作業ブランチ: `feature/refactor-app-factory/step-<n>`（main/masterで作業しない）
- 各ステップ完了時: `black .` / `ruff check .` / 主要経路の手動テスト

---

## Step 0: 準備
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-0`
- [x] 変更影響の把握（現行動作のスクリーンショット/メモ）

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: develop など適切なベース）
- [x] レビュー＆マージ完了を待つ（マージ後に次ステップへ）

検証（受け入れ基準）
- [x] `uvicorn app.demo:api --reload` で起動し、現行UI/RESTが正常
- [x] `/gradio` は `200 OK` または `307 → /gradio/` のいずれかを許容（環境差異によるリダイレクトを仕様として認容）

ロールバック
- ブランチを破棄

---

## Step 1: 静的・PWAの抽出（assets）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-1`
- [x] `app/web/assets.py` を新規作成し、`/public` マウント、`/manifest.json`、`/favicon.ico` の提供関数を作成
- [x] `create_api_app()` から上記関数を呼び出す形に置換（挙動は等価）

検証（受け入れ基準）
- [x] `GET /public/...` が配信される
- [x] `GET /manifest.json` が200で現行と同じ内容
- [x] `GET /favicon.ico` が200（MIME/中身は現行同等）

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: develop）
- [x] レビュー＆マージ完了を待つ（マージ後に次ステップへ）

ロールバック
- 置換前の `app_factory.py` に戻す / 新規ファイル削除

---

## Step 2: APIルーター分離
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-2`
- [x] `app/web/routers/threads.py` に `/api/threads*` を移設
- [x] `app/web/routers/settings.py` に `/api/settings/app` を移設
- [x] `create_api_app()` は `include_router(...)` のみ呼ぶ

検証（受け入れ基準）
- [x] `GET /api/threads` 200（件数/shape 既存同等）
- [x] `POST /api/threads` 201 + 作成結果
- [x] `GET /api/threads/{id}/messages` 200/404
- [x] `PATCH /api/threads/{id}` 200（タイトル/アーカイブ）
- [x] `DELETE /api/threads/{id}` 204/404
- [x] `GET/PATCH /api/settings/app` 200

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: develop）
- [x] レビュー＆マージ完了を待つ（マージ後に次ステップへ）

補足メモ
- サイドバー初期表示はサーバ起動時の `show_thread_sidebar` に依存。UIトグル/再アクセスで永続値が反映され、起動時スナップショットと整合することを確認（今回のリファクタの影響なし）。

ロールバック
- ルーター定義を `app_factory.py` に戻し、新規ファイル削除

---

## Step 3: 共通ユーティリティの移行（SVG）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-3`
- [x] `app/svg_utils.py` → `app/utils/svg.py` へ移動
- [x] 参照元（favicon/アバター生成部）のimport差し替え

検証（受け入れ基準）
- [ ] すべてのアイコン/アバター表示が現行同等

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/8

ロールバック
- ファイル名/インポートを元に戻す

---

## Step 4: featuresへの移行（chat/search）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-4`
- [x] `app/chat_feature.py` → `app/features/chat.py`
- [x] `app/search_feature.py` → `app/features/search.py`
- [x] Gradio側のimport差し替え（関数名は不変）

検証（受け入れ基準）
- [ ] チャットの送受信/停止/ステータス復帰が現行同等
- [ ] 設定タブの検索/選択/保存が現行同等

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/9

ロールバック
- ファイル/インポートを元に戻す

---

## Step 5: UIヘッダー/アバター抽出
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-5`
- [x] `app/ui/head.py` に `<head>` 構築（favicon Data URI/CSS/JSリンク）
- [x] `app/ui/avatars.py` にアバターSVG生成
- [x] `create_blocks()`（後述）から利用

検証（受け入れ基準）
- [ ] ページタイトル/アイコン/外部JSの動作が同等（`threads_ui.js` が機能）

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/10

ロールバック
- 直前のimport差分を元に戻す

---

## Step 6: スレッドHTML生成の純関数化
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-6`
- [x] `app/ui/html/threads_html.py` に `_build_threads_html` / `_build_threads_html_tab` を移設
- [x] 参照側差し替え

検証（受け入れ基準）
- [ ] サイドバー/タブの一覧表示が同等（選択状態/disabled含む）

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/11

ロールバック
- 関数を元の場所に戻す

---

## Step 7: タブ分割（threads_tab）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-7`（実施: step-6 ブランチ上で同時実装）
- [x] `app/ui/tabs/threads_tab.py` に UI 構築/イベント配線（open/rename/share/owner/delete, refresh）
- [x] `threads_ui.py` を内部で再利用

検証（受け入れ基準）
- [ ] 一覧の更新/選択/コンテキスト操作（rename/delete 等）が同等

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [x] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/12

ロールバック
- タブ内ロジックを `app_factory.py` 側へ一時的に戻す

---

## Step 8: タブ分割（chat_tab）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-8`
- [x] `app/ui/tabs/chat_tab.py` に UI/イベント（submit→guard→rename→stream→reset, stop, sidebar toggle）
- [x] `TitleService` の初回リネーム条件維持（userのみ1件時）

検証（受け入れ基準）
- [ ] 新規/送信/停止/タイトル自動更新/サイドバー表示切替が同等

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/13

ロールバック
- タブ内ロジックを `app_factory.py` 側へ一時的に戻す

---

## Step 9: タブ分割（settings_tab）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-9`
- [x] `app/ui/tabs/settings_tab.py` に UI/イベント（検索/選択/保存）

検証（受け入れ基準）
- [x] ヒット件数/候補表示/チップ/差分保存表示が同等

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [x] レビュー＆マージ完了を待つ（マージ後に次ステップへ）
  - PR: https://github.com/tkosht/base/pull/14

ロールバック
- タブ内ロジックを `app_factory.py` 側へ一時的に戻す

---

## Step 10: 最終薄型化/委譲
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-10`
- [x] `app/ui/app_ui.py` に `create_blocks()` を集約
- [x] `app/web/factory.py` に `create_api_app()` と最小ロジックを集約
- [x] `create_app()` は統合のみ
- [x] `app/app_factory.py` は薄い委譲を残す（外部互換）

検証（受け入れ基準）
- [ ] 主要経路がすべて現行同等（新規/送信/停止/削除/リネーム/切替/検索/保存）
- [ ] ルーティング/パス/HTTPコード/文言/イベント順序の差分なし

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（完了）
  - PR: https://github.com/tkosht/base/pull/15

ロールバック
- ファイル構成の一時巻き戻し（委譲レイヤは残しておくと復旧容易）

---

## Step 11: レガシーファイル撤去とUI再確認（最終整合）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-11`
- [x] 参照洗い出し: `grep -R "chat_feature\|search_feature\|svg_utils" app tests`
- [x] 参照置換（コード/テスト）:
  - `app.chat_feature` → `app.features.chat`
  - `app.search_feature` → `app.features.search`
  - `app.svg_utils` → `app.utils.svg`
- [x] 旧ファイル削除: `app/chat_feature.py`, `app/search_feature.py`, `app/svg_utils.py`
- [x] UI再確認: `.hidden-trigger` のグローバル適用と `:root` 変数により、不要UI（Textbox/Run）およびアバター巨大化が解消
- [x] `public/styles/app.css` を最終形へ整理（`@import` 非採用、`<link>` のみ）

検証（受け入れ基準）
- [x] `grep -R "chat_feature\|search_feature\|svg_utils"` がゼロヒット（コード/テストとも）
- [x] 主要経路（新規/送信/停止/削除/リネーム/切替/検索/保存）が同等
- [x] 不要UI非表示、アバターサイズが正常

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了を待つ（完了）

ロールバック
- 旧ファイルを復元し、import を元に戻す

---

## Step 12: テスト移行と整備（別ステップ）
実施項目
- [x] 作業ブランチ作成 `feature/refactor-app-factory/step-12-tests`
- [x] 依存準備: pytest/ruff/mypy をCI/ローカルで動かす手順を確認
- [x] 旧前提のテスト名・import の改名/整理（必要に応じリネーム）
- [x] 主要経路のE2E/統合テストを軽量に補強（モック禁止方針に従う）
- [x] `pytest -q` 緑化

検証（受け入れ基準）
- [x] 全テストパス（18 passed）
- [x] 主要経路のリグレッション検出に有効（API/サービス/UIコントローラ）

完了フック（このステップが合格したら）
- [x] Pull Request 作成（宛先: main）
- [x] レビュー＆マージ完了
  - PR: https://github.com/tkosht/base/pull/18

ロールバック
- 変更前のテスト構成に戻す（改名/パスの巻き戻し）

---

## Step 13: DoD最終確認とクローズ
実施項目
- [ ] 作業ブランチ作成 `feature/refactor-app-factory/step-13-dod`
- [ ] 本チェックリストの全PR状態確認と未マージ分の対応（マージ or クローズ）
- [ ] `black .` / `ruff check .` / `mypy app` / `pytest -q` を全て通過
- [ ] `app/app_factory.py` の行数が 300LoC 未満で読みやすいことを確認
- [ ] 主要経路の手動確認（/gradio, /public, /api/... のレスポンス/イベント順序/UI契約）

検証（受け入れ基準）
- [ ] 「完了条件（DoD）」の全チェックが [x] になる

完了フック（このステップが合格したら）
- [ ] Pull Request 作成（宛先: main）
- [ ] レビュー＆マージ完了（本リファクタリングのクローズ）

ロールバック
- 未マージPRはそのまま保留、問題発生PRは個別に revert。委譲レイヤ構成（Step 10/11）に一時復帰可能。

---

## 完了条件（DoD）
- [ ] `app/app_factory.py` は 300LoC 未満（目安）で読みやすい
- [ ] すべてのステップで受け入れ基準を満たす
- [ ] Black/Ruff/Mypy を通過
- [ ] ユーザー確認完了

