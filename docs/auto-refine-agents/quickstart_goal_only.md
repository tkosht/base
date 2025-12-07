# Quickstart（Goalのみで起動）

本ガイドは、ユーザ入力を「Goal」1点に限定し、Rubric/Artifacts を自動生成（RAS/AO）して自己改善ループを実行する最短手順を示します。

注: 各タスクは先頭にACE（自動初期化）を内蔵しているため、手動の初期化は不要です。以下の「初期化」ブロックは参考・復旧用です。

## 事前要件
- CLIツール: `jq`, `yq`, `ripgrep(rg)`, `awk`, `sed`, `sqlite3`
- リポジトリ配置: 本ドキュメントと同一リポジトリ直下
- 推奨: Git worktree を用い、各 worktree 毎に `.agent/` を分離（RAG DB 共有禁止）

## 初期化（冪等・任意）
```bash
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml
```

## 推奨: CLIエージェント経由での利用（人間のUI）

- 人間は `GOAL=...` を手で書く必要はありません。
- CLIエージェント（Cursor CLI / Claude Code / Gemini CLI 等）に対して、自然言語で「やりたいこと」を伝えれば、エージェント側が内部的に `GOAL` と `TASK_ID` を設定して `agent_goal_run` / `agent_full_cycle` を呼び出します。

例（対話イメージ）:

> 「このリポジトリで、『◯◯を達成する』ことを Goal にして agent_full_cycle を実行して。結果と Rubric / メトリクスのサマリも教えて。」

これに対してエージェントは内部的に:

- `GOAL="◯◯を達成する"` を設定
- `.cursor/commands/agent/agent_goal_run.md` → `eval_perturb_suite.md` → `outerloop_abtest.md` → `outerloop_promote.md` → `agent_templates_push_pr.md`

という順でコマンドを実行し、`.agent/` 以下のログと生成物を更新します。

## 低レベル: シェルから直接実行する場合（開発者向け）
Rubric と Artifacts は省略すると自動生成されます（Evaluator I/O v2）。  
※ これは CLI エージェントの内部実装例に近く、通常のユーザには推奨しません。
```bash
GOAL="あなたのGoal"
TASK_ID="$(date +%s)-$RANDOM"

mkdir -p .agent/logs/eval .agent/generated/{rubrics,artifacts} .agent/state

printf '{
  "task_id": "%s",
  "goal": "%s",
  "auto": {
    "rubric": true,
    "artifacts": true,
    "weights": "learned"
  },
  "rubric": null,
  "artifacts": null,
  "budget": {
    "max_cost": 0
  }
}
' "$TASK_ID" "$GOAL" \
| tee .agent/logs/eval/input.json \
| jq -r '.'

rg -n "(ERROR|FAIL|Timeout)" .agent/logs || true >/dev/null

jq -n --arg task_id "$TASK_ID" '{
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
  rubric_id: "skeleton_v0@0",
  task_id: $task_id
}' | tee .agent/logs/eval/result.json
```

## 生成物の場所
- 実行ログ: `.agent/logs/`
- 評価入出力スナップショット: `.agent/logs/eval/*.json`
- 生成 Rubric（RAS）: `.agent/generated/rubrics/*.yaml`
- 整形 Artifacts（AO）: `.agent/generated/artifacts/`
- outerloop A/B ログ:
  - 個別試行: `.agent/logs/eval/ab/*.jsonl`
  - 集計: `.agent/logs/eval/ab/summary_raw.jsonl`, `.agent/logs/eval/ab/summary.json`
  - Gate 判定ログ: `.agent/logs/eval/ab/promotion.log`
- Rubric 履歴:
  - `.agent/state/rubric_history.json`
- artifacts マップ:
  - `.agent/state/artifacts_map.json`

## 失敗時のフォールバック
- checks が不成立: 最小 rubric（`no_errors_in_logs`）で評価継続
- artifacts 取得不可: 空 `logs/app.log` とデフォルト `artifacts/metrics.json` を自動生成
- いずれも `notes/evidence` に不足が明示され、UXを止めません

## 昇格（任意）
- 安定化後、`.agent/generated/rubrics/*.yaml` を `agent/registry/rubrics/` へ PR 提案
- 添付: scores/logs 抜粋/input-hash/rubric_id/template_id/artifacts ハッシュ/metrics/根拠/環境（モデル/バージョン）
- Gate/HITL 要件は `evaluation-governance.md` を参照

## 参考
- `docs/auto-refine-agents/cli-implementation-design.md`（Evaluator I/O v2 / RAS / AO）
- `docs/auto-refine-agents/evaluation-governance.md`（ガバナンス/昇格）
- `docs/auto-refine-agents/worktree-guide.md`（並列運用/分離）
