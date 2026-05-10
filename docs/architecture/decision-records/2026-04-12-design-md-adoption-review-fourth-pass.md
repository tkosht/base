# `DESIGN.md` 導入計画 Review 4

## Status

Recorded

## Date

2026-04-12

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- 用語契約まで含めた `DESIGN.md` 昇格方針
- workflow path filter 契約の妥当性
- 議論メモと最終判断の一貫性

## Findings

### 1. 中: `DESIGN.md` 用の用語契約を具体化した方がよい

影響する契約・関数:

- `scripts/ci/validate_template.py`
- `PRIMARY_DOCS`
- `TERM_EXPANSIONS`
- `_check_primary_terminology()`

指摘:

- 計画では `DESIGN.md` を `PRIMARY_DOCS` 相当の用語契約に含めるとしているが、現行の `TERM_EXPANSIONS` は `TDD`、`CI`、`MCP`、`CLI`、`OAuth` しか対象にしていない
- design 文書側で出やすい `B2B`、`LP`、`CTA`、`UI` などをどう扱うかを決めないと、「契約に入れた」と「実際に検査できる」がずれる
- `DESIGN.md` に対してどの略語契約を適用するか、既存の `TERM_EXPANSIONS` を広げるのか、design 専用ルールを別に持つのかまで固定した方がよい

### 2. 中: workflow path filter 契約は実効カバレッジ基準に寄せた方がよい

影響する契約・文書:

- `.github/workflows/template-health.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/test-all-subsystems.yml`
- `scripts/ci/validate_template.py`

指摘:

- 現状の 3 workflow はすでに `docs/**` を path filter に含んでいるため、`docs/design/**` を literal に追加しなくても挙動上は変更を拾える
- ここで `docs/design/**` の文字列一致を必須化すると、実効カバレッジは同じでも設定だけ冗長化しやすい
- 契約は `DESIGN.md` の明示追加と、`docs/design/**` 変更が `docs/**` または同等条件で拾えること、のように実効基準へ寄せた方が壊れにくい

### 3. 低: 議論メモと最終判断の食い違いに注記を入れた方がよい

影響する文書:

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

指摘:

- 前段の discussion notes では `AGen I.` sample を generated repo に同梱したい前提が残っている一方、最終判断では public repo から外して private 側へ分離している
- 別 AI が流し読みすると、古い前提を現行方針と誤読する余地がある
- discussion notes の該当箇所に `superseded` や `later revised` の注記を入れて、最終判断で上書きされた前提だと分かるようにした方が安全である

## Outcome

- public / private 分離、starter と sample の役割差、`run_checks()` に寄せた検証方針はかなり整理された
- 実装前に残っている論点は、`DESIGN.md` 向け用語契約の具体化、workflow path filter の実効基準化、discussion notes への注記の 3 点である

## Handoff Notes

- このメモは 4 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと検証契約を最終調整する
