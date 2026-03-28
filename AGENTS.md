# AGENTS.md

- Status: Canonical
- Load: Always
- Authority: Normative
- Canonical: this file

このファイルは、このリポジトリにおける repo-local instruction の正本です。
`CLAUDE.md`、`GEMINI.md`、`.cursor/rules/rules.mdc`、`.cursor/rules/core.mdc`、`.cursor/rules/project.mdc` は薄いアダプタとして扱い、規範の重複を増やしません。
system / developer / user などの高優先度指示がある場合はそちらを優先し、このファイルは上書きしません。

## Communication
- ユーザーとの会話は日本語で行う。
- 作業中は短い進捗共有を挟み、止まらずに end-to-end で進める。

## Always-On Defaults
- まず非破壊で状況を把握し、必要な前提だけで前進する。
- ローカル探索を先に行い、追加文書は必要になったときだけ読む。
- コードや設定の事実は、可能なら現在のソース・設定・コマンド結果で確認する。
- 現在性が重要、高リスク、またはユーザーが明示した場合は、公式一次情報を確認する。
- 秘密情報、鍵、トークン、`.env` の中身を表示しない。露出の恐れがある操作は停止する。
- 破壊的な git / ファイル操作は、ユーザーの明示依頼なしでは行わない。
- ユーザーや自動生成の既存変更は巻き戻さない。無関係な変更は触らない。
- 変更を伴う作業は `main` / `master` 以外で行う。
- 推測を断定しない。不明なら確認し、確認できない場合は不明として扱う。

## Repo-Local Priority
- `AGENTS.md`: repo-local の正本。
- `CLAUDE.md` / `GEMINI.md` / `.cursor/rules/rules.mdc` / `.cursor/rules/core.mdc` / `.cursor/rules/project.mdc`: ツール別アダプタ。
- `memory-bank/...`: 必要時に読むプレイブック・参考資料。
- `output/checklists/...`: 必要時に作る一時的な作業記録。repo の正本ではない。

## Core Rules

### Security
- 機密情報の露出につながるコマンドや引用は行わない。
- 共有が必要なログは最小限に要約し、秘密情報を除く。

### Fact Handling
- 最新情報、価格、仕様、API、法務・医療・金融などは、古い知識で断定しない。
- 現在性確認では、先にローカルの主張を列挙し、その主張だけを公式一次情報で検証する。確認できない点は不明として扱い、回答では確認日・版・URL を明示し、十分な根拠が揃ったら探索を広げすぎない。
- 外部調査が判断材料になった場合は、再利用できる形で `memory-bank/07-external-research/` に要点を残す。

### Execution
- 複雑なタスクでも、ユーザーが止めない限りは実装・検証・報告まで進める。
- 高リスクな判断や大きい方針転換が必要なときだけ、簡潔に合意を取る。
- 狭い編集タスクでは、着手前に隣接実装と対象テストを確認し、許可範囲内で最小変更を行い、最も近い検証を優先する。報告では最低 2 本の自前確認を残し、通常は 1 本の最小テストと 1 本の補助確認（差分・grep・ls・schema確認など）を含める。親や外部が担う authoritative gate は unknowns に入れず、未実行 gate として change_notes か assumptions に別記する。
- レビュータスクでは、finding ごとに bullet を分ける。同じ根本原因が複数の symbol に波及する場合も、影響した関数・テスト・契約名をそれぞれ明示する。契約回帰を指摘する場合は、壊れるテスト名か関数名を本文にそのまま書く。
- 同じ失敗を繰り返す、または探索範囲が広がり続ける場合は、いったん打ち切って方針を絞り直し、必要ならチェックリスト・プレイブック・サブエージェントに切り替える。
- 難航時や設計トレードオフが拮抗したときは、協働用プレイブックやサブエージェントを使ってよい。

### Context Discipline
- 常時読込の文書は短く保つ。特殊用途の長文は `OnDemand` に落とす。
- 物語的な説明より、現在のソースオブトゥルースを優先する。
- 使われなくなった導線や欠落参照は放置せず、修正または非推奨化する。

## Load Map

### Always
- `AGENTS.md`: repo-local の正本。
- `CLAUDE.md` / `GEMINI.md` / `.cursor/rules/rules.mdc`: ツール別の薄いアダプタ。

### OnDemand
- `memory-bank/00-core/mandatory_rules_checklist.md`: 実行前・レビュー前の短い確認表。
- `memory-bank/00-core/knowledge_access_principles_mandatory.md`: 文書整理やロード設計の原則。
- `memory-bank/00-core/repository_directory_conventions.md`: どこに何を書くか迷ったときの配置基準。
- `docs/04.knowledge/base_harness_set.md`: `base` に残す最小ハーネスセットの説明。
- `docs/04.knowledge/base_harness_set.toml`: ハーネスセットの正本 manifest。
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`: 一次情報、before/after load matrix、source-to-claim 対応表。
- `memory-bank/11-checklist-driven/checklist_driven_execution_framework.md`: 複雑タスクでチェックリスト駆動にしたいとき。
- `memory-bank/11-checklist-driven/templates/codex_mcp_collaboration_checklist_template.md`: 協働相談を起動するとき。
- `memory-bank/02-organization/tmux_organization_success_patterns.md`: tmux 組織活動が必要なとき。

### Deprecated
- `memory-bank/00-core/knowledge_loading_functions.md`: 旧 `smart_knowledge_load()` 手順。新規利用禁止。
- `memory-bank/00-core/session_initialization_script.md`: 旧セッション初期化手順。新規利用禁止。
- `.cursor/rules/core.mdc` / `.cursor/rules/project.mdc`: 互換維持用の退避アダプタ。新規ルール追加禁止。

## Standard Playbooks
- 複雑タスクでは、必要に応じてチェックリストを作る。
- tmux や multi-agent は「必要なときだけ」専用プレイブックを読む。
- 文書を増やす前に、既存の正本か参照文書へ寄せられないか確認する。

## Maintenance Policy
- このファイルは短く保ち、repo-local の不変条件だけを書く。
- ツール固有・分野固有・頻度の低い手順は、ここに埋め込まず `memory-bank/` へ逃がす。
- 参照文書が正本化したくなった場合は、まず重複を消してから昇格させる。
