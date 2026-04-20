# `DESIGN.md` 導入計画 Review 5

## Status

Recorded

## Date

2026-04-12

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- `DESIGN.md` 向け略語契約の置き場所
- workflow path filter 契約の機械判定性

## Findings

### 1. 中: `DESIGN.md` 向け略語契約は validator だけでなく canonical docs にも反映した方がよい

影響する契約・文書:

- `docs/standards/communication.md`
- `AGENTS.md`
- `scripts/ci/validate_template.py`
- `DESIGN.md`

指摘:

- 計画では `DESIGN.md` 向けに design 専用の略語契約を追加する方針だが、現状の略語ルールの canonical は `docs/standards/communication.md` と `AGENTS.md` 側にある
- validator だけで `B2B`、`LP`、`CTA`、`UI` の説明義務を増やすと、文書契約にない hidden policy を実装が強制する形になる
- design 専用略語契約を導入するなら、`validate_template.py` だけでなく communication standard 側にも同じ趣旨を反映した方がよい

### 2. 中: workflow path filter 契約の「同等条件」は許容パターンを列挙した方がよい

影響する契約・文書:

- `.github/workflows/template-health.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/test-all-subsystems.yml`
- `scripts/ci/validate_template.py`

指摘:

- 計画では `docs/design/**` を `docs/**` または同等条件で拾うことを契約にしているが、この「同等条件」は機械判定にはまだ曖昧である
- 実装担当が `run_checks()` に落とすには、`docs/**`、`**`、または path filter 自体を置かない場合を許容するのか、のように許容パターンを固定する必要がある
- 実効カバレッジ基準に寄せる方向性自体は妥当なので、そこで止めずに判定可能な条件集合まで明文化した方がよい

## Outcome

- public / private 分離、sample 命名、preview の扱い、`run_checks()` に寄せた検証方針はかなり整理された
- 実装前に残っている論点は、design 専用略語契約の canonical 化と、workflow path filter 契約の許容パターン明文化の 2 点である

## Handoff Notes

- このメモは 5 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと関連する canonical docs を最終調整する
