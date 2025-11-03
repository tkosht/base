# agent_full_cycle — 完全ルート（評価/AB/昇格/PR）

目的: Quickstartの後、摂動ロバスト性→A/B比較→昇格判定→PR提出までのフルサイクルを実行します。ACEにより手動初期化は不要です。

## 実行
```bash
bash ./.cursor/commands/agent/agent_goal_run.md
bash ./.cursor/commands/agent/eval_perturb_suite.md
bash ./.cursor/commands/agent/outerloop_abtest.md
bash ./.cursor/commands/agent/outerloop_promote.md
# 合格時のみ
bash ./.cursor/commands/agent/agent_templates_push_pr.md
```

## 成果物
- `.agent/logs/**` 一式（入力/結果/AB/ロバスト）
- `pr_evidence/**`（昇格PR添付）

参照: `docs/auto-refine-agents/evaluation-governance.md`

