# `DESIGN.md` 導入計画 Review 3

## Status

Recorded

## Date

2026-04-12

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- public / private 分離後の計画の妥当性
- `DESIGN.md` を canonical surface に昇格したときの検証契約
- public sample と root starter の役割分担

## Findings

### 1. 中: `DESIGN.md` を canonical surface に昇格させるなら `PRIMARY_DOCS` にも加える方がよい

影響する契約・関数:

- `scripts/ci/validate_template.py`
- `PRIMARY_DOCS`
- `_check_primary_terminology()`

指摘:

- 現在の `validate_template.py` では、略語展開と `ADR` 禁止の検査は `PRIMARY_DOCS` にだけ掛かっている
- 計画では `DESIGN.md` を canonical surface に昇格させるが、`REQUIRED_PATHS` 追加だけでは repo-wide の用語契約から外れたままになる
- `DESIGN.md` を `PRIMARY_DOCS` に加えるか、同等の用語チェックを別途掛ける方針まで計画に含めた方がよい

### 2. 中: public template に残す generic sample と root starter の役割差を明確にした方がよい

影響する契約・文書:

- root `DESIGN.md`
- `docs/design/samples/starter-b2b-corporate/`
- `docs/design/README.md`

指摘:

- `AGen I.` sample を private へ分離した結果、public 側には root starter と generic sample の 2 つが残る
- どちらもブランド非依存の B2B / AI 向けだと、reference sample が starter の焼き直しになりやすく、knowledge surface だけが増える
- root は最小契約、sample は完成例や応用例、という差分軸を明示し、両者の責務を分けた方がよい

### 3. 中: `private companion overlay` は既存の overlay 機構と衝突しないよう定義を補足した方がよい

影響する契約・文書:

- `docs/architecture/overview.md`
- `scripts/template/apply_overlay.py`
- `templates/manifest.yaml`
- private companion overlay の説明

指摘:

- この repo では overlay が `templates/manifest.yaml` と `scripts/template/apply_overlay.py` で管理される具体機構を指している
- そのため `private companion overlay` という表現だけだと、public repo 側の overlay catalog に載るものと誤解されやすい
- この repo の `templates/` や `manifest.yaml` には含めない別配布物であることを計画に明記した方がよい

## Outcome

- sample の public / private 分離、workflow path filter 自動検査、concrete path 化は概ね整理された
- 実装前に残っている論点は、`DESIGN.md` の用語検査面、generic sample と root starter の責務分担、private companion overlay の定義明確化の 3 点である

## Evidence

- `https://github.com/tkosht/base` は 2026-04-12 時点で `Public template` 表示だった

## Handoff Notes

- このメモは 3 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと文書境界を補正する
