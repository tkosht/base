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

## 実行（Goalのみ入力）
Rubric と Artifacts は省略すると自動生成されます（Evaluator I/O v2）。
```bash
GOAL="あなたのGoal"
printf '{"goal":"%s","auto":{"rubric":true,"artifacts":true}}' "$GOAL" \
| tee .agent/logs/eval/input.json \
| jq -r '.' \
| rg -n "(ERROR|FAIL|Timeout)" - || true \
| jq -R -s '{ok:true, scores:{total:1.0}, notes:["cli-eval (skeleton)"]}' \
| tee .agent/logs/eval/result.json
```

## 生成物の場所
- 実行ログ: `.agent/logs/`
- 評価入出力スナップショット: `.agent/logs/eval/*.json`
- 生成 Rubric（RAS）: `.agent/generated/rubrics/*.yaml`
- 整形 Artifacts（AO）: `.agent/generated/artifacts/`

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
