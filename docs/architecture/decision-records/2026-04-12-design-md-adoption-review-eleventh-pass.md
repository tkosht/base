# `DESIGN.md` 導入計画 Review 11

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `template-maintained` の運用意味
- 自動検査と手動確認の境界

## Findings

### 1. 中: `template-maintained` が generated repo への自動同期を意味しないことを固定した方がよい

影響する契約・文書:

- `docs/design/README.md`
- `docs/ai/repo-contract.md`
- `README.md`
- `CONTRIBUTING.md`

指摘:

- 計画では `docs/design/README.md` を template-maintained な補助面として扱う方針まで整理されている
- ただし、その意味が「template 側で更新されても既存 generated repo へは自動反映されない」ことまで含むのかは、まだ読み手依存で残る
- ここが曖昧だと、既存 generated repo の maintainer が自動同期を期待して誤解しやすい

合格基準:

- 計画または `docs/design/README.md` に、「template-maintained は generated repo への自動同期を意味しない」と明記されている
- 既存 generated repo が template 側の更新を取り込む方法を、`manual cherry-pick`、template 更新取り込み、対象外、のいずれか 1 つに固定している
- `docs/ai/repo-contract.md`、`README.md`、`CONTRIBUTING.md`、`docs/design/README.md` でこの説明が矛盾していない

### 2. 中: checklist と導線文書の方針をどこまで自動検査するかを固定した方がよい

影響する契約・関数・テスト:

- `run_checks()`
- `tests/test_template_contract.py`
- `docs/ai/repo-contract.md`
- `README.md`
- `CONTRIBUTING.md`
- `Generated Repo Checklist`

指摘:

- 計画では `docs/design/README.md` の読書導線と generated repo 側の通常更新対象をかなり丁寧に定義している
- 一方で、`README.md`、`CONTRIBUTING.md`、`Generated Repo Checklist` の「通常は更新しない」方針まで自動検査するのか、手動確認に留めるのかはまだ少し曖昧である
- ここを決めないと、計画上は契約でも実装では未監視になりやすい

合格基準:

- 次のどちらかを計画で明示的に選んでいる。未選択は不合格とする
- 方針 A: `README.md`、`CONTRIBUTING.md`、`Generated Repo Checklist` の方針も `run_checks()` と `tests/test_template_contract.py` で自動検査する
- 方針 B: そこは手動確認項目と割り切り、`Test Plan` でも手動確認だと明記する
- 選んだ方針に合わせて、`Planned Changes` と `Test Plan` の表現が一致している

## Outcome

- 重い破綻は見当たらない
- 実装前に残っている論点は、`template-maintained` の運用意味と、自動検査に含める範囲の固定である

## Handoff Notes

- このメモは 11 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding と合格基準をもとに `docs/design/README.md` の保守意味と validator の監視範囲を最終調整する
