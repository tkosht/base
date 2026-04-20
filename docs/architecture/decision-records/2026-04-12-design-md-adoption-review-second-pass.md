# `DESIGN.md` 導入計画 Review 2

## Status

Recorded

## Date

2026-04-12

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- 初回 review 指摘の反映状況
- `docs/design/` を追加したあとの検証契約の具体性
- sample 配布ポリシーの残論点

## Findings

### 1. 中: `docs/design/**` を required path に足す方針は、`run_checks()` の実装契約まで明示した方がよい

影響する契約・関数:

- `scripts/ci/validate_template.py`
- `run_checks()`
- `tests/test_template_contract.py`

指摘:

- 現在の `run_checks()` は `REQUIRED_PATHS` を具体パスとして `Path.exists()` で検査している
- そのため、`docs/design/**` を required path に追加すると書くだけでは、glob を許すのか、具体パスへ展開するのかが曖昧に残る
- `docs/design/README.md`、sample ディレクトリ、`DESIGN.sample.md`、`preview.html` を具体列挙するか、glob 専用チェックを別に追加する方針まで固定した方がよい

### 2. 中: workflow trigger の path filter は、自動検査の追加方針まで書いた方がよい

影響する契約・関数:

- `scripts/ci/validate_template.py`
- `tests/test_template_contract.py`
- `.github/workflows/template-health.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/test-all-subsystems.yml`

指摘:

- workflow を更新する計画自体は入ったが、現状の template contract 検査は workflow 内の `make doctor`、`make lint`、`make test` しか見ていない
- `DESIGN.md` と `docs/design/**` の path filter が 3 workflow に入っていることを自動で検査する旨まで計画に含めないと、この論点だけ manual review 依存に戻る
- `tests/test_template_contract.py` か `run_checks()` の workflow contract に、path filter 検査を追加する前提を明文化した方がよい

### 3. 中: `AGen I.` sample の配布スコープを固定した方がよい

影響する契約・文書:

- `docs/design/samples/agen-i-corporate-refresh/`
- sample bundle policy

指摘:

- `AGen I.` 向け sample を template 同梱物として残す方針は維持されているが、private template 前提なのか、public 配布でも同梱するのかが未記載である
- ここが曖昧なままだと、実装段階でブランド利用許諾、保守責任、sample の公開可否が再度論点になる
- sample bundle policy として、配布範囲と扱いを一段明示した方がよい

## Outcome

- 初回 review の主要論点だった sample 命名、`repo-contract` 先行更新、preview の扱いは概ね整理された
- 実装前に残っている論点は、`validate_template.py` の検査形、workflow path filter の自動検査、`AGen I.` sample の配布スコープの 3 点である

## Handoff Notes

- このメモは 2 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと検証方針を補正する
