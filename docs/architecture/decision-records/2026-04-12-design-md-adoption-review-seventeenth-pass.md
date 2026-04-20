# `DESIGN.md` 導入計画 Review 17

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

今回の未充足は、主に `正本分離`、`検査境界`、`実装可能性` に関わる。

## Findings

### 1. 低: `root 以外の DESIGN.md` を禁止する検査スコープを固定した方がよい

関連する品質軸:

- 正本分離
- 検査境界
- 実装可能性

影響する契約・関数・テスト:

- `DESIGN.md`
- `run_checks()`
- `tests/test_template_contract.py`

指摘:

- 計画では canonical 名としての `DESIGN.md` は root の 1 枚だけに固定すると明言されている
- その一方で validation では、「root 以外の `DESIGN.md` を禁止」と書いた直後に、`docs/design/samples/**/DESIGN.md` を最低ラインの例として示している
- この書き方だと、実装担当によっては sample 配下だけを検査すればよいと読める
- repo-wide の canonical 名一意性を守りたいなら、禁止対象の探索範囲を plan 上で固定した方がよい

合格基準:

- `Validation` に、`DESIGN.md` の禁止スコープを `repo 内の root 以外すべて` と明記する、または許容例外があるならその場所を列挙する
- `run_checks()` の想定実装が、sample 配下限定ではなく、そのスコープどおりに探索すると読める
- `tests/test_template_contract.py` の mutation test も、そのスコープどおりの fail 条件を確認すると明記する
- `Decision Summary`、`Artifact Roles`、`Validation`、`Test Plan` の表現が一致している

## Outcome

- `docs/design/README.md` の責務分離、`Generated Repo Checklist` の canonical 扱い、`read-first` 導線の machine-check 化は概ね閉じている
- 残る論点は、canonical 名としての `DESIGN.md` の一意性を、どの範囲で検査するかを固定することに絞られる

## Handoff Notes

- 次の修正では、`root 以外の DESIGN.md` を禁止する探索範囲を先に決めるとよい
- 以後の review でも、新しい指摘は上記品質軸のどれに未充足があるかで説明する
