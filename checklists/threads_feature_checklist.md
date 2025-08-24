# チャットボット「スレッド機能」実装チェックリスト

本チェックリストは、TDD/DRY/YAGNI/実DB方針の下で、設計意図と進捗可視化を目的に作成する。実装時は常に本リストを更新し、粒度は「ユーザー価値を生む単位」で管理する。

## 0. 原則・方針
- [x] 実DB (sqlite3) を使用してテストする（モック禁止）
- [x] SQLAlchemy 2.0 を使用し、PostgreSQL 移行容易性を担保
- [x] DRY & YAGNI（必要最小限の機能を小さく積み上げる）
- [x] 設計意図・背景をドキュメント/コメントに残す
- [x] CI品質ゲート: カバレッジ>=85% を満たす

## 1. DB基盤（済）
- [x] ORMモデル: `Thread`, `Message`, `AppSettings`
- [x] セッション/エンジン: `SessionLocal`, `db_session()`
- [x] ブートストラップ: `create_all`, `seed_if_empty`
- [x] 起動時初期化: `create_app()` で `bootstrap_schema_and_seed()` を実行
- [x] TDD: `tests/test_db_bootstrap.py`（冪等・関係検証）

## 2. リポジトリ/サービス（最小）
- [x] ThreadRepository/Service: 作成/取得/一覧/名称変更/アーカイブ/削除
- [x] MessageRepository/Service: 追加/一覧（時系列）
- [x] SettingsRepository/Service: 取得/更新（サイドバー/タブ表示）
- [x] TDD: services層のユニットテスト（実DB使用）

## 3. API層（最小・今は保留）
- [x] `/api/threads` 系エンドポイント（一覧/作成/更新/削除）
- [x] `/api/threads/{id}/messages`（一覧/追加）
- [x] `/api/settings/app`（取得/更新）
- [ ] TDD: FastAPI TestClient による動作確認

## 4. Gradio UI拡張
- [x] Chatbotタブ: 左スレッドペイン（設定により表示/非表示）
- [x] Threadsタブ: フル画面一覧、選択でChatbotへ遷移
- [x] Settingsタブ: 表示設定トグル（DB永続化）
- [ ] TDD: UIハンドラ単体の入出力と状態更新の検証

## 5. 受け入れ基準
- [x] 設定でサイドバー/Threadsタブ表示が切替可能
- [x] Chatbotタブでスレッドを操作/選択/新規開始（初回送信時に作成）/削除が可能
- [x] Threadsタブからスレッド選択でChatbotへ遷移し会話再開
- [x] すべてのデータはSQLiteに永続化（シード含む）
- [ ] カバレッジ>=85% を満たし、テストは安定

## 進捗メモ
- 2025-08-23: DB基盤（モデル/セッション/シード）と起動時初期化をTDDで実装・通過。
- 2025-08-23: Repo/Service（Threads/Messages/Settings）をTDDで実装、Gradioテスト安定化、カバレッジ>90%。
- 2025-08-24: UI/UX調整完了（新規は空チャット→初回非空送信で作成、選択→新規で選択解除、空スレッドでは「…」/タブのアクション抑止、「…」は選択中かつ非空のみ表示、Threads→Chatbot自動遷移、サイドバー構造でスクロール責務を限定）。

## 6. 仕様更新（2025-08-24）
- 新規開始時はスレッドを作らない。初回の非空メッセージ送信時のみ作成。
- 空スレッド: メニュー非表示、タブのアクションは削除のみ。
- 選択状態: ＋新規の直後はDOMベースで一括解除（状態は持たない）。
- 「…」: 選択中かつ非空の行のみ表示。右クリックメニューと等価。
- スクロール: `#sidebar_col` は overflow:hidden、`#threads_list` に overflow-y:auto（構造で安定化）。
- ショートカット: Alt+N のみ（Ctrl/Cmd+N は不採用）。
