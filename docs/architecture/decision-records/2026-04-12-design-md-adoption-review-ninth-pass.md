# `DESIGN.md` 導入計画 Review 9

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `docs/design/README.md` の発見導線
- design 関連 test 追加の責務範囲

## Findings

### 1. 中: `docs/design/README.md` を canonical 補助面に上げるなら、`repo-contract` の読書導線にも明示した方がよい

影響する契約・文書:

- `docs/ai/repo-contract.md`
- `Reading Order`
- `Repository Roles`
- `docs/design/README.md`

指摘:

- 計画では `docs/design/README.md` を reference doc ではなく canonical な補助面として扱い、`PRIMARY_DOCS` に含める前提まで進んでいる
- 一方で、`docs/ai/repo-contract.md` の更新項目として明示されているのは root `DESIGN.md` の読書順や役割追加が中心で、`docs/design/README.md` 自体の発見導線はまだ弱い
- このままだと、validator 上は重要文書でも、agent の読書順では見つけにくい補助文書のまま残る
- `Reading Order` に design 系作業時の追加読書順として入れるか、少なくとも `Repository Roles` に役割を明記した方がよい

### 2. 中: design 関連 test 追加の範囲を、`Planned Changes` 側でも明示した方がよい

影響する契約・関数・テスト:

- `tests/test_template_contract.py`
- `run_checks()`
- `_check_primary_terminology()`
- design 専用 checker

指摘:

- `Test Plan` では、design 略語チェック、`docs/design/README.md` の `PRIMARY_DOCS` 扱い、代表的な pass / fail 例まで確認する前提になっている
- ただし `Planned Changes` で明示されている `tests/test_template_contract.py` 追加は、required path 欠落と workflow path filter 欠落の 2 系統までに読める
- 現在の test file は `run_checks()` に対する明示的な mutation test を積む構成なので、計画上も design 用語契約と `docs/design/README.md` の共通用語契約まで test 追加対象に含めると書いた方が実装担当は迷いにくい
- 追加 test の責務範囲を `Planned Changes` と `Test Plan` の両方でそろえた方がよい

## Outcome

- 前回までの主要論点だった design 系文書の検査スコープと略語契約の優先関係はかなり整理された
- 実装前に残っている論点は、`docs/design/README.md` の発見導線を `repo-contract` にどう織り込むかと、design 関連 test 追加の責務範囲を `Planned Changes` でも明示するかの 2 点である

## Handoff Notes

- このメモは 9 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに `repo-contract` 側の導線と `tests/test_template_contract.py` の追加対象を最終調整する
