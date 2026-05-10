# `DESIGN.md` 導入計画 Review 6

## Status

Recorded

## Date

2026-04-17

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- design 専用略語ルールの canonical な置き場所
- design 略語契約と既存コミュニケーション標準の優先関係

## Findings

### 1. 中: design 専用略語ルールを `AGENTS.md` に追記しすぎない方がよい

影響する契約・文書:

- `AGENTS.md`
- `docs/standards/communication.md`
- `docs/design/README.md`

指摘:

- 計画では `AGENTS.md` と `docs/standards/communication.md` に design で頻出する略語の説明義務を追記する方針になっている
- ただし、この repo では `AGENTS.md` を短い always-on の入口に保ち、長い詳細は `docs/` に分離する方針が既にある
- design 略語の具体例や運用細則まで `AGENTS.md` に載せると、入口文書が肥大化し、repo の知識配置方針とずれやすい
- `AGENTS.md` は design 文書でも略語だけで説明しないという参照レベルに留め、具体的な略語ルールは `docs/standards/communication.md` か `docs/design/README.md` に寄せた方がよい

### 2. 中: design 専用略語契約と「1 回しか出ない語は略さない」ルールの優先関係を固定した方がよい

影響する契約・文書:

- `docs/standards/communication.md`
- `AGENTS.md`
- `scripts/ci/validate_template.py`
- `DESIGN.md`

指摘:

- 現行の communication standard には「その回答や文書で 1 回しか出ない語は略さない」というルールがある
- 一方で計画は `B2B`、`LP`、`CTA`、`UI` を正式名または平易な日本語と併記すれば許容する方向に見える
- この優先関係を明示しないと、たとえば `ユーザーインターフェース（UI）` を 1 回だけ書いたケースを pass にするか fail にするかで validator の解釈が割れる
- design 専用略語契約を入れるなら、既存ルールの例外なのか、単に初出展開を要求する追加ルールなのかを固定した方がよい

## Outcome

- public / private 分離、sample 命名、preview の扱い、workflow の実効カバレッジ条件はかなり整理された
- 実装前に残っている論点は、design 略語ルールの canonical な置き場所と、既存コミュニケーション標準との優先関係の 2 点である

## Handoff Notes

- このメモは 6 回目の review 結果だけを独立して残す
- 実装担当の AI は、この finding をもとに計画メモと関連する canonical docs の責務分担を最終調整する
