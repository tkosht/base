# outerloop_rollback — 劣化時の自動降格

目的: 新テンプレ導入後にスコア/ロバスト性/コストが劣化した場合、直前安定版へ自動降格します。

## 前提
- 直前安定版テンプレIDの記録（例: `.agent/state/stable_template_id`）
- 監査ログ/比較結果の保存先があること

## 手順（例）
```bash
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

set -euo pipefail

STABLE=$(cat .agent/state/stable_template_id 2>/dev/null || echo "planner.default.v1")
CURRENT=$(cat .agent/state/current_template_id 2>/dev/null || echo "planner.candidate.v2")

# 条件はプロジェクトに合わせて判定
DEGRADED=true

if [ "$DEGRADED" = true ]; then
  echo "$STABLE" > .agent/state/current_template_id
  echo "rolled back to $STABLE"
fi
```

## 出力
- `.agent/state/current_template_id` 更新
- ロールバックログ

## 注意
- 具体的な劣化判定（しきい値/傾向）はプロジェクト要件に合わせて定義してください。
- ロールバック後は `outerloop_abtest.md` の再計測を推奨。

