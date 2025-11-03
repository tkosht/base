# outerloop_abtest — テンプレ A/B 比較実験

目的: テンプレート候補（例: `planner.default.v1` vs `planner.candidate.v2`）を同一条件で比較し、スコア/コストの差分を収集します。

## 前提
- 比較対象テンプレが `.agent/prompts/templates.yaml` または `agent/registry/prompts/templates.yaml` に定義
- 評価ルーブリック: `agent/registry/rubrics/code_quality_v1.yaml`

## 手順（例）
```bash
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

set -euo pipefail
TEMPLATES=(planner.default.v1 planner.candidate.v2)
GOAL="あなたのGoal"
mkdir -p .agent/logs/eval/ab

for TID in "${TEMPLATES[@]}"; do
  printf '{"goal":"%s","template_id":"%s","auto":{"rubric":true,"artifacts":true}}' "$GOAL" "$TID" \
  | jq -r '.' \
  | rg -n "(ERROR|FAIL|Timeout)" - || true \
  | jq -R -s '{ok:true, scores:{basic:1.0}, notes:["cli-eval (abtest)"]}' \
  | tee ".agent/logs/eval/ab/${TID}.json"

done

jq -s 'map({id:.template_id,s: .scores.total//0, c: .metrics.cost//0})' .agent/logs/eval/ab/*.json > .agent/logs/eval/ab/summary.json
cat .agent/logs/eval/ab/summary.json
```

## 出力
- `.agent/logs/eval/ab/*.json`
- `.agent/logs/eval/ab/summary.json`

## 注意
- 実運用では v2 Evaluator を用いて正確なスコアリングを行ってください。
- 昇格基準は `outerloop_promote.md` を参照。

