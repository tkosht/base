# AIエージェント協調・実行分担フレームワーク

date: 2026-01-05
status: active
scope: 親エージェントが唯一のユーザ窓口となり、実行はサブエージェントに委譲する協調開発プロセス

## 目的/適用範囲
- 目的: 親エージェントが要件/品質合意を担い、実ファイル変更・テスト実行はサブエージェントが行う。
- 適用範囲: 仕様設計/実装/テスト/ドキュメント整合を伴う開発全般。

## 前提
- ユーザとの合意形成は親エージェントのみが行う（Single-Contact）。
- サブエージェントはユーザと直接対話しない。
- 親エージェントは原則として実行を行わない（例外のみ）。
- レビュー記録先は入力で指定し、固定パスへの依存は持たせない。
- 既定のレビュー記録先は `docs/ai-agent-reviews/`（必要に応じて変更）。

## 役割分担（実行責任の明確化）
- 親エージェント: 要件/品質の合意、協調ループ起動、ゲート判定、最終報告。
- 実行サブエージェント（Executor）: 実ファイル変更、テスト実行、ログ収集。
- レビューサブエージェント（Reviewer）: 独立レビュー、根拠付き指摘、未解消事項の提示。
- 検証サブエージェント（Verifier）: テスト/CI 再実行、失敗時の切り分け・再試行。
- リリースサブエージェント（Releaser, 任意）: commit/PR 等の運用作業。

## 例外（親が実行するケース）
- 仕様変更/品質基準変更など、ユーザ合意が必要な判断。
- サブエージェントの権限不足で進行不可となった場合。
- 秘密情報や承認が必要な操作。

## 実行権限・書き込み範囲（ガードレール）
- Executor
  - 書き込み: 対象コード領域のみ（例: src/, app/, tests/）。
  - 実行: テスト/整形/CI 再現コマンド。
  - 出力: 変更一覧・実行ログ・テスト結果を /facts と /revise に記録。
- Reviewer
  - 書き込み: <review_output_dir> のみ（レビュー .md 作成）。
  - 実行: 読み取りのみ。
- Verifier
  - 書き込み: 原則なし（必要なら /facts への追記のみ）。
  - 実行: テスト再実行・再現確認。
- Releaser（任意）
  - 書き込み: <review_output_dir>（運用記録）。
  - 実行: commit/PR などの運用作業（必要時のみ）。

## スキル間の関係（簡易図）
ai-agent-collaboration-exec は「協調ループの設計/テンプレ」を担い、codex-subagent が実行エンジンとして各サブエージェントを起動する。

```mermaid
flowchart LR
  User[ユーザ] --> Parent[親エージェント]
  Parent -->|要件/品質合意| CollabSkill[ai-agent-collaboration-exec\n(協調設計・テンプレ)]
  CollabSkill -->|パイプライン仕様/依頼文| CodexSubagent[codex-subagent\n(実行オーケストレーター)]
  CodexSubagent --> Executor[Executor]
  CodexSubagent --> Reviewer[Reviewer]
  CodexSubagent --> Verifier[Verifier]
  Executor -->|変更/テスト| Repo[(リポジトリ)]
  Reviewer -->|レビュー .md| ReviewStore[(review_output_dir)]
  Verifier -->|再実行ログ| ReviewStore
  CodexSubagent -->|capsule/log| Sessions[(.codex/sessions)]
  Parent -->|統合/報告| User
```

## codex-subagent pipeline 構成（例）
※この構成例は `--pipeline-spec` 使用前提（`--pipeline-stages` の既定は `draft,critique,revise` のみ）。
- **既定パイプラインの踏襲は禁止**。タスクに合わせて初期/動的ステージを設計し、理由と最適化観点を /draft に記録すること。
- 途中での再設計は `next_stages` で動的追加する。動的追加を許容する場合は `allow_dynamic_stages: true` を明示すること。
- 動的設計が必要な場合は `--pipeline-spec` を使用し、`--pipeline-stages` の固定テンプレートに依存しないこと。
- `allowed_stage_ids` は初期/動的追加の候補を含む。`stages` は初期実行順のみを列挙すること。
```json
{
  "allow_dynamic_stages": true,
  "allowed_stage_ids": ["draft", "execute", "review", "revise", "verify", "release"],
  "stages": [
    { "id": "draft",   "instructions": "開発案・差分方針を /draft に記録。根拠は /facts。" },
    { "id": "execute", "instructions": "Executor が実ファイル変更＋テスト実行。結果/ログを /facts に記録。" },
    { "id": "review",  "instructions": "Reviewer が指摘・リスクを /critique に記録。根拠必須。" }
  ]
}
```
`release`/`verify` などの動的追加を使う可能性がある場合は `allowed_stage_ids` に含め、使わない場合は除外して整合させる。

## Capsule 構造（責務と格納先）
- /draft: 開発案・変更方針
- /critique: レビュー指摘・リスク
- /revise: 修正反映まとめ
- /facts: 実行ログ・テスト結果・根拠
- /open_questions: 仕様未確定事項
- /assumptions: 仮定（最小）

## ループ条件 / 終了条件
- 継続条件:
  - /critique に重大指摘が残る
  - /open_questions が残る
  - /facts と不整合
  - テスト/CI 未通過
  - パイプライン設計が既定踏襲でタスク最適化されていない
- 終了条件:
  - 重大指摘ゼロ
  - /open_questions が解消または受理
  - /facts 整合
  - テスト/CI 通過

## 非決定性対策
- サブエージェントの依頼文はテンプレ固定（JSON/箇条書き）。
- 再実行上限を明示（例: 最大 2～3 回）。
- 逸脱時は 再生成 → それでも失敗ならタスク分割。

## 実行ポリシー（品質優先）
- タスク難易度や要求水準を下げての短縮はしない。
- 時間がかかる場合は timeout を延長して対応する。
- timeout が発生したら、同一スコープで再実行する（再実行上限を明示）。
- 再実行しても進められない場合は、タスクを停止しフレームワークのデバッグ/改善に移行する。

## テスト/CI ゲート
- Unit → Integration → CI の順で通過させる。
- CI 失敗時は原因抽出 → 最小修正 → 再実行で収束。

## 成果物命名規約（推奨）
- <review_output_dir>/<topic>_design_<YYYY-MM-DD>.md
- <review_output_dir>/<topic>_review_<YYYY-MM-DD>_roundN.md
- <review_output_dir>/<topic>_test_method_<YYYY-MM-DD>.md
- <review_output_dir>/<topic>_notes_<YYYY-MM-DD>.md

## 実行サブエージェントの契約出力（必須）
- 変更ファイル一覧
- 実行コマンド一覧
- テスト結果（成功/失敗）
- 失敗時の原因と次の手（具体的なアクション）
出力は完結な文で記載し、曖昧な語で終わらせない。
