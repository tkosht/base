# `DESIGN.md` 導入計画 Review 13

## Status

Recorded

## Date

2026-04-19

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `Generated Repo Checklist` の責務
- checklist section の自動検査境界

## Findings

### 1. 中: `Generated Repo Checklist` を canonical section と mirror のどちらで扱うかを固定した方がよい

影響する契約・関数・テスト:

- `docs/ai/repo-contract.md`
- `run_checks()`
- `tests/test_template_contract.py`
- `Generated Repo Checklist`

指摘:

- 計画では `Generated Repo Checklist` に `DESIGN.md` 更新を追加する前提がある
- 一方で別の箇所では、`README.md`、`CONTRIBUTING.md`、`docs/design/README.md` と並んで mirror 的な manual review 項目として読める表現が残っている
- このままだと、`Generated Repo Checklist` 自体が canonical contract なのか、mirror 扱いなのかで実装担当の解釈が割れやすい

合格基準:

- `Generated Repo Checklist` を canonical section として扱うのか、mirror 扱いに落とすのかを 1 つに固定する
- canonical のままなら、manual review 対象の列挙から `Generated Repo Checklist` を外す
- mirror 扱いにするなら、`repo-contract` 内の checklist ではなく別文書へ責務を移す
- 計画メモの `Decision Summary`、`Planned Changes`、`Validation`、`Test Plan` の表現が一致している

### 2. 中: checklist section 自体をどこまで machine-check するかを具体化した方がよい

影響する契約・関数・テスト:

- `docs/ai/repo-contract.md`
- `run_checks()`
- `tests/test_template_contract.py`
- `Generated Repo Checklist`

指摘:

- 現計画は `repo-contract` の checklist に `DESIGN.md` 更新対象を入れる前提になっている
- ただし、自動検査側は `repo-contract` 内に非自動同期ポリシーが残っていることを確認する方針までで、checklist section 自体を検査するかはまだ明示が弱い
- 現行の `run_checks()` は生テキストの needle 検査中心なので、実装次第では checklist section が stale でも別段落の文言で pass する余地がある

合格基準:

- 自動検査に含める場合は、`run_checks()` が `Generated Repo Checklist` section 自体に `DESIGN.md` 更新対象があることを確認する
- あわせて、`docs/design/README.md` が通常更新対象ではないことも checklist section で確認する
- `tests/test_template_contract.py` に、checklist section の該当文言を削ったとき fail する mutation test がある
- そこまで自動化しない場合は、計画から「checklist を自動検査する」と読める表現を外し、manual review に統一する

## Outcome

- 大きな方向性はかなり安定している
- 実装前に残っている論点は、`Generated Repo Checklist` の責務を canonical か mirror かで固定することと、その section 自体をどこまで machine-check するかを決めることの 2 点である

## Handoff Notes

- このメモは 13 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding と合格基準をもとに checklist section の責務と検査境界を最終調整する
