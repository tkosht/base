# Knowledge Access Principles

- Status: Reference
- Load: OnDemand
- Authority: Operational
- Canonical: `AGENTS.md`

この文書は、知識ロードと導線設計の原則を簡潔にまとめた参照ページです。
`smart_knowledge_load()` のような旧フローは採らず、短い正本 + 必要時参照を前提にします。

## Principles
- 最適化は「削ること」ではなく「短い正本と明確な導線へ整理すること」。
- repo-wide の不変条件は `AGENTS.md` に集約し、特殊手順は `memory-bank/` へ分離する。
- 技術事実は narrative 文書より、現在の設定・コード・テスト・コマンド結果を優先する。
- 使われない長文や欠落参照は、常時読込から外して非推奨化する。

## Load Policy
- `Always`: `AGENTS.md` と薄いツールアダプタ。
- `OnDemand`: チェックリスト、tmux、協働、レビュー、配置規約などのプレイブック。
- `Never`: `Deprecated` と明示した旧手順。互換導線として残すだけで、新規利用しない。

## When Simplifying Docs
- 重複した規範は増やさず、正本へのポインタに置き換える。
- 欠落した参照先をでっち上げず、現存する正本へ張り替えるか非推奨化する。
- 1 つの変更で複数ツール面が壊れないよう、`AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、Cursor ルールの整合を一緒に見る。

## Related
- `memory-bank/00-core/mandatory_rules_checklist.md`
- `memory-bank/00-core/repository_directory_conventions.md`
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`
