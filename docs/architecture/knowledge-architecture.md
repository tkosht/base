# 知識配置

## Purpose

この文書は、このテンプレートで長く残す知識をどこに置くかを定義します。正本を増やしすぎず、必要な情報へ最短でたどり着ける状態を保つことが目的です。

## Canonical Surfaces

- `README.md`: 人間向けの入口
- `AGENTS.md`: repo-local instruction の短い正本
- `CLAUDE.md`: Claude Code 向けの薄いアダプタ
- `DESIGN.md`: generated repo の visual contract の正本
- `docs/ai/`: AI エージェント運用の詳細
- `docs/design/README.md`: root `DESIGN.md` を支える design guidance の補助面
- `docs/architecture/`: 構造、知識配置、ハーネス一覧、設計判断メモ
- `docs/standards/`: 実装、テスト、セキュリティ、レビュー、コミュニケーションの標準

## Placement Rules

- 人間と AI の共通運用契約は `docs/ai/` に置く。
- 見た目の正本は root の `DESIGN.md` に置き、sample では canonical 名の `DESIGN.md` を増やさない。
- design guidance の補助面と reference-only sample は `docs/design/` に置く。
- 構造上の判断、長く残す設計理由、ハーネス一覧は `docs/architecture/` に置く。
- 実装時の共通ルールは `docs/standards/` に置く。
- 既存の正本へ追記できる内容なら、新しい文書を増やさない。
- 一時的な作業メモ、長いログ、試行錯誤の途中経過は正本に昇格させない。

## Decision Records

- 長期に残す判断理由は `docs/architecture/decision-records/` に設計判断メモとして残す。
- 判断メモは「何を変えたか」ではなく、「なぜその配置や方針を採ったか」を短く残す。

## Frozen Input Documents

- `docs/repository-template-design.md` は入力設計書として凍結する。
- 新しい判断はこの文書に追記せず、運用中の正本か設計判断メモに反映する。

## Retired Surfaces

- 旧 knowledge surface はこのテンプレートの live surface から外す。
- 旧 knowledge surface は `docs/architecture/` と `docs/ai/` に置き換える。
- 旧文書の詳細は必要なら git history でたどる。
