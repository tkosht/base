# `DESIGN.md` 導入計画 Review 10

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `docs/design/README.md` の読書導線に対する合格基準
- `docs/design/README.md` の保守責務に対する合格基準

## Findings

### 1. 中: `docs/design/README.md` の導線を validator と test で守る基準を固定した方がよい

影響する契約・関数・テスト:

- `docs/ai/repo-contract.md`
- `run_checks()`
- `tests/test_template_contract.py`
- `docs/design/README.md`

指摘:

- `docs/design/README.md` を canonical な補助面に上げるなら、読書導線も壊れにくい契約として固定した方がよい
- `repo-contract` に書くだけでは将来の削除を防げないため、validator と test でも守る必要がある

合格基準:

- `docs/ai/repo-contract.md` の `Reading Order`、または design 系作業時の追加読書順に `docs/design/README.md` が明記されている
- 同ファイルの `Repository Roles` に、`docs/design/README.md` が root `DESIGN.md` を支える canonical な補助面だと明記されている
- `scripts/ci/validate_template.py` の `run_checks()` が、`repo-contract` から `docs/design/README.md` の導線が消えた場合に fail する
- `tests/test_template_contract.py` に、`repo-contract` から当該導線を削った場合に fail する test がある
- 計画メモの `Planned Changes` と `Test Plan` の両方で、この導線が検査対象だと読める

### 2. 中: `docs/design/README.md` の保守責務を、選択肢込みで固定した方がよい

影響する契約・文書:

- `docs/ai/repo-contract.md`
- `README.md`
- `CONTRIBUTING.md`
- `Generated Repo Checklist`
- `docs/design/README.md`

指摘:

- `docs/design/README.md` を canonical な補助面に上げると、generated repo 側で誰がいつ見直すかを曖昧にできなくなる
- 更新対象なのか template-maintained 文書なのかが未固定だと、root `DESIGN.md` だけ更新されて補助面が stale になる余地が残る

合格基準:

- 次のどちらかを計画で明示的に選ぶ。未選択は不合格とする
- 方針 A: `docs/design/README.md` は template-maintained であり、generated repo では通常更新しない
- 方針 B: `docs/design/README.md` は generated repo 側でも review / update 対象に含める
- 選んだ方針が `docs/ai/repo-contract.md`、`README.md`、`CONTRIBUTING.md`、`Generated Repo Checklist`、`docs/design/README.md` 自身で矛盾なく一致している
- root `DESIGN.md` と `docs/design/README.md` の同期責務が 1 文で固定されている
- 方針 A を選ぶ場合は、checklist から `docs/design/README.md` を外し、「通常は更新しない」と明記する
- 方針 B を選ぶ場合は、checklist に `docs/design/README.md` の review / update を追加し、いつ見直すかを明記する

## Outcome

- finding ごとの合格基準を、文書更新だけでなく validator と test の観点まで含めて明確化した
- 実務上は、`root DESIGN.md = プロジェクト固有の更新対象`、`docs/design/README.md = template-maintained な補助面` とする方が保守コストは低い

## Handoff Notes

- このメモは 10 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding と合格基準をもとに `repo-contract`、checklist、validator、test の責務分担を最終調整する
