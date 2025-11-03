# agent_goal_run — Goalのみで Inner-Loop 最短経路を実行（Evaluator I/O v2）

目的: ユーザ入力を Goal のみに限定し、RAS/AO 自動補完の最小経路で `ok:true|false` を判定します。

## 前提
- CLI: `jq`, `rg`, `sqlite3`（FTSは任意）

## 手順
```bash
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

GOAL="あなたのGoal"

# eval ログディレクトリを確実に作成
mkdir -p .agent/logs/eval

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

