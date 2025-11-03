# agent_templates_pull — 正典 → ランタイム同期

目的: 共有正典 `agent/registry/**` をローカル `.agent/**` に同期し、現在の作業ツリーで使用可能にします。

## 前提
- `agent/registry/**` に雛形が存在
- `.agent/` 初期化済み（未実施なら `agent_init.md`）

## 手順
```bash
# prompts
rsync -av --delete agent/registry/prompts/ .agent/prompts/

# playbooks（任意）
rsync -av --delete agent/registry/playbooks/ .agent/memory/playbooks/

# config 既定
rsync -av --delete agent/registry/config/ .agent/config/

# 監査
find .agent -maxdepth 2 -type d -print | sed 's/^/synced: /'
```

## 注意
- `.agent/` は worktree 専用。DBファイル（`memory/semantic/fts.db`）の共有は禁止。
- RAG 対象は `docs/**.md`, `memory-bank/**.md`（`agent/registry/**` は対象外）。

参照: `docs/auto-refine-agents/registry-guidelines.md`, `worktree-guide.md`

