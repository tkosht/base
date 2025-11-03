# auto-refine-agents: Agent Commands

本ディレクトリは auto-refine-agents サブプロジェクト専用の実行タスクを集約します。

## 命名規約
- ファイル名は snake_case + `.md`
- 役割プレフィックスを付与: `agent_` / `outerloop_` / `eval_` / `worktree_`
- 一タスク一目的（入出力・前提・手順・注意・終了条件を明記）

## 想定タスク一覧（計画）
- `agent_init.md`: `.agent/**` の遅延初期化（ACE）と FTS5 DB 作成
- `agent_goal_run.md`: Goal のみで Inner-Loop 最短経路実行（Evaluator I/O v2）
- `agent_templates_pull.md`: `agent/registry/**` → `.agent/**` 同期
- `agent_templates_push_pr.md`: `.agent/**` → `agent/registry/**` 昇格 PR（Step2）
- `eval_perturb_suite.md`: 摂動ロバスト性スイート実行（Step2）
- `outerloop_abtest.md`: テンプレ A/B 比較（Step2）
- `outerloop_promote.md`: Gate MUST 基準で昇格判定（Step2）
- `outerloop_rollback.md`: 劣化時の自動降格（Step2）
- `worktree_ops.md`: worktree 作成/削除/分離ガイド

詳細は `docs/auto-refine-agents/*.md` を参照してください。


