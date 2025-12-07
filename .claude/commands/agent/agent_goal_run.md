# agent_goal_run — Goalのみで Inner-Loop 最短経路を実行（Evaluator I/O v2）

目的: ユーザ入力を Goal のみに限定し、RAS/AO 自動補完の最小経路で `ok:true|false` を判定します。

## 前提
- CLI: `jq`, `rg`, `sqlite3`（FTSは任意）

## 手順
```bash
# 安全実行
set -euo pipefail
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

GOAL="${GOAL:-あなたのGoal}"

# eval ログディレクトリ / AO / RAS 生成物ディレクトリを作成
mkdir -p .agent/logs/eval .agent/generated/rubrics .agent/generated/artifacts .agent/state

# TASK_ID を決定（環境変数優先）
TASK_ID="${TASK_ID:-$(date +%s)-$RANDOM}"
export TASK_ID GOAL

# rubric_autogen.defaults.yaml から weights デフォルトを取得（失敗時は learned）
REFINE_WEIGHTS="learned"
if [ -f agent/registry/config/rubric_autogen.defaults.yaml ] && command -v yq >/dev/null 2>&1; then
  REFINE_WEIGHTS="$(yq -er '.refine.weights' agent/registry/config/rubric_autogen.defaults.yaml 2>/dev/null || echo "learned")"
fi

# Evaluator I/O v2 形式の input.json を生成
printf '{
  "task_id": "%s",
  "goal": "%s",
  "auto": {
    "rubric": true,
    "artifacts": true,
    "weights": "%s"
  },
  "rubric": null,
  "artifacts": null,
  "budget": {
    "max_cost": 0
  }
}
' "$TASK_ID" "$GOAL" "$REFINE_WEIGHTS" \
| tee .agent/logs/eval/input.json \
| jq -r '.'

# RAS v0: Rubric 自動生成（rubrics/<task_id>.yaml + rubric_history.json）
if [ -f .cursor/commands/agent/agent_ras_autogen.md ]; then
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_ras_autogen.md | bash
fi

# AO v0: 標準 artifacts セットアップ（app.log / metrics.json / artifacts_map）
if [ -f .cursor/commands/agent/agent_ao_run.md ]; then
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_ao_run.md | bash
fi

# スケルトン Evaluator: ログをスキャンし、result.json（v2構造）を書き出す
rg -n "(ERROR|FAIL|Timeout)" .agent/logs || true >/dev/null

jq -n --arg task_id "$TASK_ID" --arg rubric_id "autogen_code_quality_v1@1" '{
  ok: true,
  scores: {
    total: 1.0
  },
  notes: ["cli-eval (skeleton)"],
  evidence: {
    failed_checks: [],
    raw: {}
  },
  metrics: {
    cost: 0,
    latency_ms: 0
  },
  rubric_id: $rubric_id,
  task_id: $task_id
}' | tee .agent/logs/eval/result.json
```

## 出力
- `.agent/logs/eval/input.json`
- `.agent/logs/eval/result.json`

## 注意
- 本タスクはスケルトン評価（`ok:true` 固定に近い）。正式な評価は rubric/チェックと `eval_perturb_suite.md`（Step2）を使用。
- RAS/AO の完全版は将来拡張。省略時は最小生成で継続する設計。

参照: `docs/auto-refine-agents/quickstart_goal_only.md`, `evaluation-governance.md`
