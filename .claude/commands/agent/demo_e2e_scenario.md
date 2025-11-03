# demo_e2e_scenario — QuickstartベースのE2Eデモ

目的: Quickstart（Goalのみ）から評価・A/B・昇格判定までの一連を最短で再現します。

## フロー
1) `agent_init.md` — `.agent/**` 初期化
2) `agent_goal_run.md` — 最短経路で評価（スケルトン）
3) `eval_perturb_suite.md` — 摂動ロバスト性
4) `outerloop_abtest.md` — テンプレA/B 比較
5) `outerloop_promote.md` — Gate MUST 判定
6) `agent_templates_push_pr.md` — 昇格PR提出

## 実行（例）
```bash
bash ./.cursor/commands/agent/agent_init.md
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

参照: `docs/auto-refine-agents/quickstart_goal_only.md`, `evaluation-governance.md`, `worktree-guide.md`

