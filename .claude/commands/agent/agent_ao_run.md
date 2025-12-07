# agent_ao_run — AO v0（Artifacts Orchestrator 最小版）

目的: `.agent/logs/app.log` と `.agent/generated/artifacts/metrics.json` の存在を保証し、必要に応じて `artifacts_map.json` に `task_id` → パスを記録します。

## 手順
```bash
set -euo pipefail

# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

# 標準 artifacts 用ディレクトリ
mkdir -p .agent/logs .agent/generated/artifacts .agent/state

# app.log の存在保証（空で良い）
: > .agent/logs/app.log

# metrics.json の存在保証（無い or 空のときだけ初期化）
METRICS_PATH=".agent/generated/artifacts/metrics.json"
if [ ! -s "$METRICS_PATH" ]; then
  printf '{"total_cost":0,"cost":0,"latency_ms":0,"calls":0}\n' > "$METRICS_PATH"
fi

# 任意: TASK_ID があれば artifacts_map.json に記録
if [ -n "${TASK_ID:-}" ]; then
  ARTIFACTS_MAP=".agent/state/artifacts_map.json"
  TMP="$(mktemp)"
  if [ -f "$ARTIFACTS_MAP" ]; then
    jq --arg t "$TASK_ID" \
       --arg app ".agent/logs/app.log" \
       --arg m "$METRICS_PATH" \
       '.[$t] = {app_log: $app, metrics: $m}' "$ARTIFACTS_MAP" > "$TMP" || { rm -f "$TMP"; exit 1; }
  else
    jq -n --arg t "$TASK_ID" \
          --arg app ".agent/logs/app.log" \
          --arg m "$METRICS_PATH" \
          '{($t): {app_log: $app, metrics: $m}}' > "$TMP"
  fi
  mv "$TMP" "$ARTIFACTS_MAP"
fi
```

## 出力
- `.agent/logs/app.log`
- `.agent/generated/artifacts/metrics.json`
- （任意）`.agent/state/artifacts_map.json`

参照: `docs/auto-refine-agents/evaluation-governance.md`, `agent/registry/rubrics/code_quality_v1.yaml`
