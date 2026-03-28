# Knowledge Loading Functions

- Status: Deprecated
- Load: Never
- Authority: Historical
- Canonical: `AGENTS.md`

このファイルにある `smart_knowledge_load()` / `comprehensive_knowledge_load()` 前提は、現在の運用では使いません。
新規タスクでは、短い repo-local 正本を前提にし、必要な文書だけを都度読む方式に切り替えています。

## Migration
- 旧「自動ロード」は使わず、ローカル探索で必要な事実から読む。
- 高リスク・最新性要求・外部仕様確認が必要なときだけ、公式一次情報を追加する。
- 実際のロード方針は `AGENTS.md` と `memory-bank/00-core/knowledge_access_principles_mandatory.md` を参照する。
