# agent_ras_autogen — RAS v0（Rubric Auto Synthesis 最小版）

目的: `agent/registry/config/rubric_autogen.defaults.yaml` から最小の Rubric YAML を生成し、`.agent/generated/rubrics/<task_id>.yaml` として保存、あわせて `.agent/state/rubric_history.json` に履歴を追記します。

## 手順
```bash
set -euo pipefail

# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

mkdir -p .agent/generated/rubrics .agent/state .agent/logs/eval

INPUT_JSON=".agent/logs/eval/input.json"

# TASK_ID / GOAL を決定（環境変数優先 → input.json）
TEMPLATE_ID_RESOLVED="${TEMPLATE_ID:-}"
if [ -n "${TASK_ID:-}" ]; then
  TASK_ID_RESOLVED="$TASK_ID"
elif [ -f "$INPUT_JSON" ]; then
  TASK_ID_RESOLVED="$(jq -r '.task_id // empty' "$INPUT_JSON")"
  if [ -z "$TASK_ID_RESOLVED" ] || [ "$TASK_ID_RESOLVED" = "null" ]; then
    TASK_ID_RESOLVED="$(date +%s)-$RANDOM"
  fi
else
  TASK_ID_RESOLVED="$(date +%s)-$RANDOM"
fi

GOAL_RESOLVED="${GOAL:-あなたのGoal}"
if [ -f "$INPUT_JSON" ]; then
  FROM_INPUT_GOAL="$(jq -r '.goal // empty' "$INPUT_JSON")"
  if [ -n "$FROM_INPUT_GOAL" ] && [ "$FROM_INPUT_GOAL" != "null" ]; then
    GOAL_RESOLVED="$FROM_INPUT_GOAL"
  fi
fi

TASK_ID="$TASK_ID_RESOLVED"
RUBRIC_ID="autogen_code_quality_v1"
RUBRIC_VERSION=1
RUBRIC_PATH=".agent/generated/rubrics/${TASK_ID}.yaml"
RUBRIC_SOURCE="rubric_autogen.defaults.yaml"

DEFAULTS_PATH="agent/registry/config/rubric_autogen.defaults.yaml"

# defaults を yq で読める場合は、その内容を元に Rubric YAML を生成
if [ -f "$DEFAULTS_PATH" ] && command -v yq >/dev/null 2>&1; then
  yq -o=json '.' "$DEFAULTS_PATH" \
  | jq --arg goal "$GOAL_RESOLVED" \
       --arg id "$RUBRIC_ID" \
       --arg source "$RUBRIC_SOURCE" \
       --arg template_id "$TEMPLATE_ID_RESOLVED" '
      . as $cfg
      | ($cfg.checks_catalog // {}) as $catalog
      | ($catalog | to_entries) as $checks
      | {
          id: $id,
          version: 1,
          objectives: (
            ($cfg.objectives_default // {})
            | to_entries
            | map({name: .key, weight: .value})
          ),
          checks: (
            if ($checks | length) == 0 then [] else
              $checks
              | map({
                  name: .key,
                  detector: (
                    .value.detector
                    # ランタイム標準パスに合わせてログ/メトリクスのパスを正規化
                    | gsub("logs/"; ".agent/logs/")
                    | gsub("artifacts/metrics.json"; ".agent/generated/artifacts/metrics.json")
                    | gsub("\\.cost"; ".total_cost")
                  ),
                  expect: .value.expect,
                  weight: (1.0 / ($checks | length))
                })
            end
          ),
          thresholds: $cfg.thresholds // {},
          metadata: (
            {goal: $goal, source: $source}
            + (if ($template_id // "") != "" then {template_id: $template_id} else {} end)
          )
        }' \
  | yq -P -o=yaml '.' > "$RUBRIC_PATH"
else
  # フォールバック: 設計書に準拠した最小 Rubric を直接生成（defaults 参照不可環境用）
  cat > "$RUBRIC_PATH" <<YAML
id: autogen_code_quality_v1
version: 1
objectives:
  - name: spec_compliance
    weight: 0.4
  - name: robustness
    weight: 0.3
  - name: cost_efficiency
    weight: 0.2
  - name: runtime_reliability
    weight: 0.1
checks:
  - name: no_errors_in_logs
    detector: "rg -n '(ERROR|FAIL|Timeout)' .agent/logs/ | wc -l"
    expect: "== 0"
    weight: 0.4
  - name: spec_tests_pass
    detector: "bash tests/spec_run.sh"
    expect: "exit_code == 0"
    weight: 0.3
  - name: budget_within_limit
    detector: "jq '.total_cost' .agent/generated/artifacts/metrics.json"
    expect: "<= budget.max_cost"
    weight: 0.3
thresholds:
  pass_score: 0.9
metadata:
  goal: "$GOAL_RESOLVED"
  source: rubric_autogen.defaults.yaml
  template_id: "$TEMPLATE_ID_RESOLVED"
YAML
fi

# rubric_history.json に履歴を追記
HISTORY_PATH=".agent/state/rubric_history.json"
TMP_HISTORY="$(mktemp)"
CREATED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ -f "$HISTORY_PATH" ]; then
  jq --arg task_id "$TASK_ID" \
     --arg rubric_id "${RUBRIC_ID}@${RUBRIC_VERSION}" \
     --arg source "$RUBRIC_SOURCE" \
     --arg goal "$GOAL_RESOLVED" \
     --arg created_at "$CREATED_AT" \
     '. + [{
        task_id: $task_id,
        rubric_id: $rubric_id,
        source: $source,
        goal: $goal,
        created_at: $created_at
      }]' "$HISTORY_PATH" > "$TMP_HISTORY" || { rm -f "$TMP_HISTORY"; exit 1; }
else
  jq -n --arg task_id "$TASK_ID" \
        --arg rubric_id "${RUBRIC_ID}@${RUBRIC_VERSION}" \
        --arg source "$RUBRIC_SOURCE" \
        --arg goal "$GOAL_RESOLVED" \
        --arg created_at "$CREATED_AT" \
        '[{
          task_id: $task_id,
          rubric_id: $rubric_id,
          source: $source,
          goal: $goal,
          created_at: $created_at
        }]' > "$TMP_HISTORY"
fi

mv "$TMP_HISTORY" "$HISTORY_PATH"

echo "Rubric generated at: $RUBRIC_PATH"
```

## 出力
- `.agent/generated/rubrics/<task_id>.yaml`
- `.agent/state/rubric_history.json`

参照: `agent/registry/config/rubric_autogen.defaults.yaml`, `docs/auto-refine-agents/mvp_impl_plan_phase1-3_evaluator_ras_ao.md`
