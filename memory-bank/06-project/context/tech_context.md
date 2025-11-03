# Tech Context（auto-refine-agents / CLI）

## 必須ツール（コンテナ内）
- jq / yq
- sqlite3（FTS5 有効）
- ripgrep(rg) / awk / sed
- eza / fdfind（任意）

## 原則
- Makefileへの依存は避け、`.cursor/commands/agent/*.md` に運用手順を記載
- `.agent/` は worktree 専用のランタイム（非Git）
- `agent/registry/` は共有正典（Git）。RAG対象外
- RAG対象は `docs/**.md` と `memory-bank/**.md`

## 補足
- 設定優先: `.agent/config/*` > `agent/registry/config/*.defaults.yaml` > built-in
- pull/push: `agent/registry → .agent` / `.agent → PR → agent/registry`

