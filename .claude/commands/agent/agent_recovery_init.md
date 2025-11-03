# agent_recovery_init — `.agent/` 手動初期化（復旧専用）

目的: 例外的な復旧時に `.agent/` 構造を冪等に生成し、SQLite FTS5 を初期化します（通常運用はACE自動初期化）。

## 前提
- CLI: `jq`, `yq`, `sqlite3`, `rg`, `awk`, `sed`
- カレント: リポジトリルート

## 手順（冪等）
```bash
# 1) ディレクトリ生成（存在時はスキップ）
[ -d .agent ] || mkdir -p \
  .agent/state/session_history \
  .agent/generated/{rubrics,artifacts} \
  .agent/memory/{episodic,semantic/documents,playbooks} \
  .agent/prompts/{planner,executor,evaluator,analyzer} \
  .agent/config \
  .agent/logs

# 2) SQLite FTS5（未作成時のみ）
[ -f .agent/memory/semantic/fts.db ] || \
  sqlite3 .agent/memory/semantic/fts.db \
  "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"

# 3) 既定設定（未作成時のみ）
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

# 4) 監査
ls -1 .agent | sed 's/^/created: /'
```

## 注意
- 通常は各タスク先頭のACEで自動初期化されるため、本コマンドは不要です。
- worktree間で `.agent/memory/semantic/fts.db` を共有しないでください。

参照: `docs/auto-refine-agents/cli-implementation-design.md`, `quickstart_goal_only.md`, `worktree-guide.md`

