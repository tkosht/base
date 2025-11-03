# eval_perturb_suite — 摂動ロバスト性スイート実行

目的: 並べ替え/シャッフル/軽微ノイズ/境界ケースの摂動を加えた評価を実行し、ロバスト性を検証します。

## 前提
- `agent/registry/rubrics/code_quality_v1.yaml` が利用可能
- テストスクリプトの用意（例）: `tests/spec_run.sh`, `tests/perturbation_suite.sh`

## 手順（例）
```bash
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

set -euo pipefail

# 1) 事前: ログ/メトリクス初期化
mkdir -p .agent/logs .agent/generated/artifacts .agent/logs/eval
: > .agent/logs/app.log
: > .agent/generated/artifacts/metrics.json

# 2) スイート実行（例: シェルスクリプト委譲）
bash tests/perturbation_suite.sh
EC=$?

# 3) 成果物を検査
if [ "$EC" -eq 0 ]; then
  echo '{"ok":true,"note":"perturbation passed"}' > .agent/logs/eval/perturb.json
else
  echo '{"ok":false,"note":"perturbation failed"}' > .agent/logs/eval/perturb.json
fi

cat .agent/logs/eval/perturb.json
```

## 出力
- `.agent/logs/eval/perturb.json`

## 注意
- 実際のチェック内容・生成物はプロジェクトに合わせて実装してください。
- Gate MUST では本スイートの合格が必要です（`evaluation-governance.md`）。

