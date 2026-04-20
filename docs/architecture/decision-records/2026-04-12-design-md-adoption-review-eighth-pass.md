# `DESIGN.md` 導入計画 Review 8

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `docs/design/README.md` の normative / reference の位置づけ
- design 系略語チェックの実装方針と適用対象の書き分け

## Findings

### 1. 中: `docs/design/README.md` に共通用語契約を掛けるかどうかを固定した方がよい

影響する契約・関数・文書:

- `docs/design/README.md`
- `docs/standards/communication.md`
- `scripts/ci/validate_template.py`
- `PRIMARY_DOCS`
- `_check_primary_terminology()`
- `run_checks()`

指摘:

- 計画では `docs/design/README.md` を canonical な補助面として使い、design 文書向けルールの参照先にもしている
- 一方で現行 validator の共通用語契約は `PRIMARY_DOCS` に対してだけ掛かるため、今回の計画どおり `PRIMARY_DOCS` に root `DESIGN.md` だけを足すと、`docs/design/README.md` には design 専用チェックしか掛からない
- その結果、`ADR` 禁止や `TDD`、`CI`、`MCP`、`CLI`、`OAuth` のような既存の共通契約から `docs/design/README.md` だけ外れる
- `docs/design/README.md` も `PRIMARY_DOCS` に含めるのか、あるいは reference doc と割り切って design 専用検査だけにするのかを計画で固定した方がよい

### 2. 中: design 系略語チェックの実装方針を、対象文書が一読で分かる形にそろえた方がよい

影響する契約・関数・文書:

- `scripts/ci/validate_template.py`
- `run_checks()`
- `tests/test_template_contract.py`
- `DESIGN.md`
- `docs/design/README.md`
- `docs/design/samples/**/DESIGN.sample.md`

指摘:

- 計画全体では design 系文書全体に同じ略語契約を掛ける方針になっている
- ただし validation の実装方針では、`DESIGN_TERM_EXPANSIONS` 相当を「`DESIGN.md` にだけ追加適用する」と読める記述が残っている
- この 1 文だけ読むと、root `DESIGN.md` 専用のチェックなのか、design 系文書共通の追加チェックなのかが分かれやすい
- 実装担当の読み違いを防ぐため、既存 `TERM_EXPANSIONS` とは別の design 専用 checker を作り、root `DESIGN.md`、`docs/design/README.md`、public sample の `DESIGN.sample.md` に共通適用する、と明示した方がよい

## Outcome

- 前回までの主要論点だった検査スコープと pass / fail 代表例はかなり整理された
- 実装前に残っている論点は、`docs/design/README.md` を共通用語契約の対象へ含めるかどうかと、design 系略語チェックの適用対象を誤読できない形で固定することの 2 点である

## Handoff Notes

- このメモは 8 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに `docs/design/README.md` の位置づけと design 系略語 checker の責務範囲を最終調整する
