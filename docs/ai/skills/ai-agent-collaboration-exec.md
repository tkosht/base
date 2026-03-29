# AI エージェント協調実行

## Purpose

親エージェントを唯一のユーザー窓口として保ちつつ、Executor、Reviewer、Verifier に仕事を分けるときの説明正本です。

## Use When

- 協調実行が必要
- 実装とレビューを分離したい
- テストと検証を独立させたい
- 役割ごとに書き込み範囲を固定したい

## Durable Best Practices

- 親エージェントは要件整理、優先順位付け、最終報告だけを担当する
- Executor、Reviewer、Verifier の責務と書き込み範囲を最初に固定する
- `review_output_dir` のような成果物の置き場を事前に決める
- `codex-subagent` を実行エンジンとして使い、単一の大きい指示ではなく役割ごとの依頼に分ける
- 既定の pipeline をそのまま踏襲せず、タスクに合わせて stage を選ぶ
- `release` stage を使う場合だけ `allowed_stage_ids` に含め、使わない stage を漫然と許可しない
- 根拠はファイルパス、行番号、ログ、コマンド結果で残す
- 実行が重いときは、pipeline より小さい単位の single 実行へ戻して詰める

## Expected Outputs

- pipeline spec
- role assignments
- stage results
- review artifacts
- verification summary

## Entrypoints

- Codex entrypoint: `.agents/skills/ai-agent-collaboration-exec`
- Claude entrypoint: `.claude/skills/ai-agent-collaboration-exec`
