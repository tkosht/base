# agent_init — `.agent/` 遅延初期化（ACE）

目的: worktree 毎に独立した `.agent/` 構造を冪等に生成し、SQLite FTS5 を初期化します。

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

## 出力
- `.agent/**` 一式
- `.agent/memory/semantic/fts.db`

## 注意
- `.agent/` は Git 管理外（`.gitignore` 必須）
- RAG DB の共有は禁止（worktree 毎に独立）

参照: `docs/auto-refine-agents/cli-implementation-design.md`, `quickstart_goal_only.md`, `worktree-guide.md`

