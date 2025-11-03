# System Patterns（auto-refine-agents）

## 三層分離パターン（正典/ランタイム/意思決定）
- ランタイム（非Git）: `.agent/`
  - worktree ごとに独立。RAG DB（`memory/semantic/fts.db`）含む実行状態
  - `.gitignore` 対象
- 共有正典（Git）: `agent/registry/`
  - prompts / playbooks / rubrics / config(`*.defaults.yaml`)
  - RAG インデクシング対象外
- 意思決定（Git）: `memory-bank/`
  - 目的/判断/進捗・既知課題の記録（人間向け）

適用指針
- 同期: pull=`agent/registry → .agent` / push=`.agent → PR → agent/registry`
- 設定優先: `.agent/config/*` > `agent/registry/config/*.defaults.yaml` > built-in
- 運用手順: `.cursor/commands/agent/*.md` にプロンプトタスクとして記載

## RAG設計パターン
- 対象: `docs/**.md`, `memory-bank/**.md`
- 非対象: `agent/registry/**`
- SQLite FTS5 を既定、DB共有禁止（worktree毎に独立）

## 昇格ガバナンス
- Gate MUST 満たす変更のみ PR 昇格（`evaluation-governance.md`）
- 監査ログ: input-hash / rubric_id / template_id / scores / evidence / cost / latency / model

