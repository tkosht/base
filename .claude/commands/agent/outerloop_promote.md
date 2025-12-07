# outerloop_promote — 昇格判定（Gate MUST）

目的: A/B 比較・ロバスト性・コスト・監査条件に基づき、テンプレートの昇格可否を判定します。

## 前提
- `outerloop_abtest.md` 実行済み（`summary.json` あり）
- `eval_perturb_suite.md` 合格
- 監査ログ: input-hash, rubric_id, template_id, scores, metrics（コスト/レイテンシ）

## 判定（擬似ロジック例）
```bash
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

set -euo pipefail

AB=.agent/logs/eval/ab/summary.json
PERT=.agent/logs/eval/perturb.json

# 既定・設定の読み込み（優先順位: 環境変数 > loop_config.yaml > 既定）
AB_MIN_N="${AB_MIN_N:-}"
MIN_DELTA="${MIN_DELTA:-}"
MAX_COST="${MAX_COST:-}"

if command -v yq >/dev/null 2>&1; then
  [ -z "${AB_MIN_N:-}" ] && AB_MIN_N=$(yq -e '.gate.min_n' .agent/config/loop_config.yaml 2>/dev/null || true)
  [ -z "${MIN_DELTA:-}" ] && MIN_DELTA=$(yq -e '.gate.min_delta' .agent/config/loop_config.yaml 2>/dev/null || true)
  [ -z "${MAX_COST:-}" ] && MAX_COST=$(yq -e '.gate.max_cost' .agent/config/loop_config.yaml 2>/dev/null || true)
fi

AB_MIN_N="${AB_MIN_N:-5}"
# MIN_DELTA は summary を見て skeleton を検出して動的既定を決める
# summary が無い/読めない場合は保守的に 0.0
if [ -z "${MIN_DELTA:-}" ]; then
  if [ -f "$AB" ]; then
    # s_avg の一意数が1かつ値が1.0なら skeleton とみなす
    SKELETON=$((jq -r '([.[].s_avg] | unique | length==1) and (.[0].s_avg==1.0)' "$AB" 2>/dev/null || echo "false") | tr -d '\n')
    if [ "$SKELETON" = "true" ]; then
      MIN_DELTA="0.0"
    else
      MIN_DELTA="0.02"
    fi
  else
    MIN_DELTA="0.0"
  fi
fi
# YAMLから取得した null は未設定として扱う
if [ "${MAX_COST:-}" = "null" ]; then MAX_COST=""; fi

# 昇格候補の算出（平均スコアで降順）
jq -e '.' "$AB" >/dev/null
jq 'sort_by(.s_avg) | reverse | .[0]' "$AB" > .agent/logs/eval/ab/best.json
cat .agent/logs/eval/ab/best.json

# Gate MUST の簡易チェック（例）
PASS_PERT=$(jq -r '.ok' "$PERT")
if [ "$PASS_PERT" != "true" ]; then
  echo "NG: perturbation suite failed" >&2; exit 1
fi

# 反復数の検証
N_MIN=$(jq 'map(.n) | min' "$AB")
if ! awk "BEGIN{exit !($N_MIN >= $AB_MIN_N)}"; then
  echo "NG: AB反復不足 (min_n=$N_MIN < $AB_MIN_N)" >&2; exit 1
fi

# スコア差（上位2テンプレ）とコストSLO
LEN=$(jq 'length' "$AB")
if [ "$LEN" -lt 2 ]; then
  echo "NG: テンプレート比較対象が不足 (count=$LEN < 2)" >&2; exit 1
fi

SORTED=$(jq 'sort_by(.s_avg) | reverse' "$AB")
DELTA=$(jq -r '.[0].s_avg - .[1].s_avg' <<<"$SORTED")
BEST_ID=$(jq -r '.[0].id' <<<"$SORTED")
BEST_COST=$(jq -r '.[0].c_avg' <<<"$SORTED")

if ! awk "BEGIN{exit !($DELTA >= $MIN_DELTA)}"; then
  echo "NG: Δ=$DELTA < $MIN_DELTA" >&2; exit 1
fi
if [ -n "${MAX_COST:-}" ]; then
  if ! awk "BEGIN{exit !($BEST_COST <= $MAX_COST)}"; then
    echo \"NG: cost $BEST_COST > $MAX_COST\" >&2; exit 1
  fi
fi

# 合格: current_template_id を更新
mkdir -p .agent/state
echo "$BEST_ID" > .agent/state/current_template_id
echo "PROMOTE OK: best=$BEST_ID Δ=$DELTA cost=$BEST_COST (n_min=$N_MIN)" | tee -a .agent/logs/eval/ab/promotion.log
```

## 結果
- ベスト候補と Gate MUST 合否をログに記録
- 合格時は `agent_templates_push_pr.md` へ進む

参照: `docs/auto-refine-agents/evaluation-governance.md`

