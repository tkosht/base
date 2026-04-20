# `DESIGN.md` 導入計画 Review 18

## Status

Recorded

## Date

2026-04-19

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Viewpoints

今回の review は、前回までに整理した次の品質軸に沿って確認した。

- 正本分離
- 更新責務
- 検査境界
- 発見導線
- 実装可能性
- reference sample 分離

今回の確認では、上記品質軸に対する新規の未充足は見当たらなかった。

## Findings

- 重大な指摘なし

補足:

- `DESIGN.md` の canonical 名は root のみであることが、`Decision Summary`、`Artifact Roles`、`Validation`、`Test Plan` で一致している
- `docs/design/README.md` の責務は design guidance の canonical 補助面に固定され、sync policy の正本は `docs/ai/repo-contract.md` に寄せられている
- design 系作業で root `DESIGN.md` を先に読む契約と、`Generated Repo Checklist` section の扱いは、方針ではなく machine-check 対象として記述されている
- manual review 対象は `README.md` と `CONTRIBUTING.md` の mirror に限定され、canonical surface は machine-check に残っている

## Acceptance Criteria

- `Decision Summary`、`Artifact Roles`、`Validation`、`Test Plan` の全てで、canonical 名は root の `DESIGN.md` のみと一致している
- `docs/design/README.md` の責務が「design guidance の canonical 補助面」で固定され、sync policy の正本が `docs/ai/repo-contract.md` に固定されている
- `read-first` 契約と `Generated Repo Checklist` section が、`run_checks()` と mutation test の対象として書かれている
- manual review 対象が `README.md` と `CONTRIBUTING.md` の mirror に限定され、canonical surface は machine-check の対象に残っている

## Outcome

- 現時点の計画メモは、実装担当へ渡してよい水準に達している
- 残る論点は plan の妥当性ではなく、validator と test へどう素直に実装するかである

## Handoff Notes

- 実装担当は、この計画をそのまま `validate_template.py` と `tests/test_template_contract.py` へ落とし込む段階に進めてよい
- 次の review は、計画レビューではなく実装差分レビューへ切り替えるのが自然である
