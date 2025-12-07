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
TEMPLATES=(${TEMPLATES:-planner.default.v1 planner.candidate.v2})
GOAL="${GOAL:-あなたのGoal}"

# 反復回数（優先順位: 環境変数 > loop_config.yaml > 既定）
AB_N="${AB_N:-}"
if [ -z "${AB_N:-}" ] && command -v yq >/dev/null 2>&1; then
  AB_N=$(yq -e '.ab.iterations' .agent/config/loop_config.yaml 2>/dev/null || true)
fi
AB_N="${AB_N:-5}"

mkdir -p .agent/logs/eval/ab

# 生データ蓄積（jsonl）
: > .agent/logs/eval/ab/summary_raw.jsonl

for TID in "${TEMPLATES[@]}"; do
  : > ".agent/logs/eval/ab/${TID}.jsonl"
  for i in $(seq 1 "$AB_N"); do
    # 各試行ごとに一意な TASK_ID を付与し、Evaluator I/O v2 + RAS/AO 経由で評価を実施
    TASK_ID="ab-${TID}-${i}-$(date +%s)-$RANDOM"
    export TASK_ID GOAL TEMPLATES
    TEMPLATE_ID="$TID"
    export TEMPLATE_ID

    # Inner-Loop Goal 実行（Evaluator I/O v2 / RAS / AO）
    awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_goal_run.md | bash

    # 評価結果（result.json）を A/B 用の1行JSONに正規化して蓄積
    jq --arg tid "$TID" \
       --argjson i "$i" \
       --arg task_id "$TASK_ID" \
       '{
          template_id: $tid,
          iteration: $i,
          task_id: $task_id,
          ok: .ok,
          scores: .scores,
          metrics: .metrics,
          rubric_id: .rubric_id
        }' .agent/logs/eval/result.json \
    | tee -a ".agent/logs/eval/ab/${TID}.jsonl" >> .agent/logs/eval/ab/summary_raw.jsonl
  done
done

# 平均集計
jq -s '
  group_by(.template_id) |
  map({
    id: .[0].template_id,
    n: length,
    s_avg: (map(.scores.total)|add/length),
    c_avg: (map(.metrics.cost // 0)|add/length)
  })
' .agent/logs/eval/ab/summary_raw.jsonl > .agent/logs/eval/ab/summary.json

cat .agent/logs/eval/ab/summary.json
```

## 出力
- `.agent/logs/eval/ab/*.json`
- `.agent/logs/eval/ab/summary.json`

## 注意
- 実運用では v2 Evaluator を用いて正確なスコアリングを行ってください。
- 昇格基準は `outerloop_promote.md` を参照。
