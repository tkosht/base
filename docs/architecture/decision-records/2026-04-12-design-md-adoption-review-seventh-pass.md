# `DESIGN.md` 導入計画 Review 7

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- design 系文書への略語契約の適用範囲
- 略語検証ルールの pass / fail 条件の具体化

## Findings

### 1. 中: design 専用略語ルールの置き場所と検証スクリプトの適用範囲をそろえた方がよい

影響する契約・文書:

- `docs/standards/communication.md`
- `docs/design/README.md`
- `DESIGN.md`
- `docs/design/samples/**/DESIGN.sample.md`
- `scripts/ci/validate_template.py`

指摘:

- 計画では design 系の略語ルールの canonical な詳細を `docs/standards/communication.md` と `docs/design/README.md` に置く前提になっている
- 一方で、検証スクリプトの計画は root の `DESIGN.md` 向けの `DESIGN_TERM_EXPANSIONS` 相当だけを想定しているように読める
- このままだと、`docs/design/README.md` や public sample の `DESIGN.sample.md` が canonical ルールからずれても自動検知されない
- `DESIGN.md` だけを検査対象にするのか、design 系文書全体を検査対象にするのかを計画内で固定した方がよい

### 2. 中: 略語ルールの pass / fail 条件を、実装しやすい例まで落とした方がよい

影響する契約・文書:

- `docs/standards/communication.md`
- `scripts/ci/validate_template.py`
- `DESIGN.md`

指摘:

- 計画では「1 回しか出ない語は略さない」を優先し、`ユーザーインターフェース（UI）` を 1 回だけ書いたケースを fail にする方針は見えている
- ただし、反対側の pass 例がまだ不足しており、たとえば `ユーザーインターフェース（UI）` を初出で書いた後に再度 `UI` を使うケースをどう扱うかが明示されていない
- 現行の検証スクリプトは全文に対する比較的単純な語検出ベースなので、合格例まで例示しないと実装担当ごとに判定が割れやすい
- 単発使用は fail、複数回利用で初出展開ありは pass、のように代表例を計画へ明示した方がよい

## Outcome

- 大きな論点はかなり整理されている
- 実装前に残っている論点は、design 系文書の検査スコープと、略語ルールの具体的な合否例の固定である

## Handoff Notes

- このメモは 7 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと検証スクリプトの責務範囲を最終調整する
