# agent_goal_run — Goalのみで Inner-Loop 最短経路を実行（Evaluator I/O v2）

目的: ユーザ入力を Goal のみに限定し、RAS/AO 自動補完の最小経路で `ok:true|false` を判定します。

## 前提
- `.agent/` 初期化済（未実施なら `agent_init.md` を先に実行）
- CLI: `jq`, `rg`, `sqlite3`（FTSは任意）

## 手順
```bash
GOAL="あなたのGoal"

# 入力（v2: rubric/artifacts を自動補完）
printf '{"goal":"%s","auto":{"rubric":true,"artifacts":true}}' "$GOAL" \
| tee .agent/logs/eval/input.json \
| jq -r '.' \
| rg -n "(ERROR|FAIL|Timeout)" - || true \
| jq -R -s '{ok:true, scores:{basic:1.0}, notes:["cli-eval (skeleton)"]}' \
| tee .agent/logs/eval/result.json
```

## 出力
- `.agent/logs/eval/input.json`
- `.agent/logs/eval/result.json`

## 注意
- 本タスクはスケルトン評価（`ok:true` 固定に近い）。正式な評価は rubric/チェックと `eval_perturb_suite.md`（Step2）を使用。
- RAS/AO の完全版は将来拡張。省略時は最小生成で継続する設計。

参照: `docs/auto-refine-agents/quickstart_goal_only.md`, `evaluation-governance.md`

