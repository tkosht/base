# `DESIGN.md` 導入計画 Review 16

## Status

Recorded

## Date

2026-04-19

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Viewpoints

今回の review は、前回整理した次の品質軸に沿って確認した。

- 正本分離
- 更新責務
- 検査境界
- 発見導線
- 実装可能性
- reference sample 分離

今回の未充足は、主に `reference sample 分離` と `発見導線` に関わる。

## Findings

### 1. 中: sample 側に `DESIGN.md` を増やさない契約を machine-check に上げた方がよい

関連する品質軸:

- 正本分離
- reference sample 分離
- 検査境界

影響する契約・関数・テスト:

- `DESIGN.md`
- `DESIGN.sample.md`
- `run_checks()`
- `tests/test_template_contract.py`

指摘:

- 計画の中核は、root の `DESIGN.md` を canonical 名として唯一に保つことにある
- その一方で validation は、sample の存在確認と required path の追加までは書かれているが、sample 側の `DESIGN.md` 混入を禁止する検査までは書かれていない
- このままだと、後から `docs/design/samples/**/DESIGN.md` が紛れ込んでも、canonical surface の破綻として自動検知できない

合格基準:

- `Validation` に「root 以外の `DESIGN.md` を禁止する」契約を明記する
- 少なくとも `docs/design/samples/**/DESIGN.md` が存在したら `run_checks()` が fail する方針を明記する
- `tests/test_template_contract.py` に、sample 側へ `DESIGN.md` を追加した mutation で fail する test を追加すると明記する
- `Decision Summary`、`Artifact Roles`、`Validation`、`Test Plan` の 4 箇所で「canonical 名は root `DESIGN.md` のみ」が一致している

### 2. 中: design 系作業で root `DESIGN.md` を先に読む契約を、方針ではなく検査対象として閉じた方がよい

関連する品質軸:

- 発見導線
- 検査境界
- 実装可能性

影響する契約・関数・テスト:

- `docs/ai/repo-contract.md`
- `run_checks()`
- `tests/test_template_contract.py`

指摘:

- 計画本文では、UI / frontend / LP / marketing site の作業では root の `DESIGN.md` を先に読むという強い導線契約を置いている
- ただし validation と test で machine-check するのは `docs/design/README.md` の導線と補助面説明が中心で、`root DESIGN.md read-first` 自体を削ったときに fail する条件までは閉じていない
- 発見導線を品質軸に上げた以上、ここも検査対象まで揃えた方が一貫する

合格基準:

- 次のどちらかに固定する
- 強い契約を維持する場合:
- `run_checks()` が `repo-contract` 上の「design 系作業では root `DESIGN.md` を先に読む」文言を検査すると明記する
- `tests/test_template_contract.py` に、その文言を削る mutation test を追加すると明記する
- 弱い契約でよい場合:
- `Planned Changes` 側の読書順要求を、現行の machine-check 範囲に合わせて緩める
- `Planned Changes`、`Validation`、`Test Plan` の表現が一致している

## Outcome

- `docs/design/README.md` の責務分離、`Generated Repo Checklist` の canonical 扱い、mirror 文言の manual review 境界はかなり閉じている
- 残る論点は、canonical 名の一意性と read-first 導線を、plan 上の方針ではなく検査される契約として閉じることに集約される

## Handoff Notes

- 次の修正では、`DESIGN.md` の唯一性と `read first` 導線を `run_checks()` / mutation test にどう落とすかを先に決めるとよい
- 以後の review でも、新しい指摘は上記品質軸のどれに未充足があるかで説明する
