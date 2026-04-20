# `DESIGN.md` 導入計画 Review 12

## Status

Recorded

## Date

2026-04-18

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `template-maintained` / 非自動同期ポリシーの正本
- `manual cherry-pick` の位置づけ

## Findings

### 1. 中: `template-maintained` / 非自動同期ポリシーの正本を 1 箇所に固定した方がよい

影響する契約・関数・文書:

- `docs/ai/repo-contract.md`
- `docs/design/README.md`
- `run_checks()`
- `tests/test_template_contract.py`
- `README.md`
- `CONTRIBUTING.md`

指摘:

- 計画では `template-maintained` と非自動同期の方針をかなり整理できている
- ただし、この方針の正本が `docs/ai/repo-contract.md` なのか `docs/design/README.md` なのかは、まだ少し読み分かれが残る
- ここが曖昧だと、canonical contract 自体が drift しやすく、validator で何を守るべきかもぶれやすい

合格基準:

- `template-maintained` / 非自動同期ポリシーの正本を `docs/ai/repo-contract.md` か `docs/design/README.md` のどちらか 1 箇所に固定する
- その正本には、generated repo へ自動同期しないことと、採用する取り込み方針が明記されている
- `run_checks()` が、その正本から当該方針が消えた場合に fail する
- `tests/test_template_contract.py` に、その正本の該当文言を削る mutation test がある
- `README.md` と `CONTRIBUTING.md` を mirror として手動確認対象に留める場合は、`Test Plan` でもその扱いが明記されている

### 2. 中: `manual cherry-pick` を唯一方式にするか例示に留めるかを固定した方がよい

影響する契約・文書:

- `docs/ai/repo-contract.md`
- `docs/design/README.md`
- `README.md`
- `CONTRIBUTING.md`
- `Test Plan`

指摘:

- 現計画は `manual cherry-pick` をかなり具体的に書いており、読み手によっては唯一の取り込み方式だと受け取りやすい
- ただし、実際に固定したい policy は「手動取り込み」であって、`git cherry-pick` はその一例に留める方が壊れにくい可能性がある
- もし本当に唯一方式にするなら、その前提条件まで書かないと運用契約としては強すぎる

合格基準:

- 方針を `手動取り込み` に上げ、`manual cherry-pick` は例として書く、または `manual cherry-pick` を唯一方式として維持するなら前提条件を書く
- `manual cherry-pick` を唯一方式として維持する場合は、少なくとも次を明記する
- template 側 commit を特定できること
- maintainer がその commit を取得できること
- 差分適用に失敗した場合の扱い
- `docs/ai/repo-contract.md`、`docs/design/README.md`、`README.md`、`CONTRIBUTING.md` で表現が一致している
- `Test Plan` の手動確認項目に、その整合確認が含まれている

## Outcome

- 大きな方向性はかなり安定している
- 実装前に残っている論点は、非自動同期ポリシーの正本を 1 箇所に寄せることと、`manual cherry-pick` を policy にするか example にするかを固定することの 2 点である

## Handoff Notes

- このメモは 12 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding と合格基準をもとに非自動同期ポリシーの正本と、手動取り込み方式の表現を最終調整する
