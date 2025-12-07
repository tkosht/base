# agent_templates_pull — 正典 → ランタイム同期

目的: 共有正典 `agent/registry/**` をローカル `.agent/**` に同期し、現在の作業ツリーで使用可能にします。

## 前提
- `agent/registry/**` に雛形が存在

## 手順
```bash
# 安全実行
set -euo pipefail
# ACE自動初期化（遅延・冪等）
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml

# prompts
rsync -av --delete agent/registry/prompts/ .agent/prompts/

# playbooks（任意）
rsync -av --delete agent/registry/playbooks/ .agent/memory/playbooks/

# config 既定
rsync -av --ignore-existing agent/registry/config/ .agent/config/

# 監査
find .agent -maxdepth 2 -type d -print | sed 's/^/synced: /'
```

## 注意
- `.agent/` は worktree 専用。DBファイル（`memory/semantic/fts.db`）の共有は禁止。
- RAG 対象は `docs/**.md`, `memory-bank/**.md`（`agent/registry/**` は対象外）。

参照: `docs/auto-refine-agents/registry-guidelines.md`, `worktree-guide.md`

