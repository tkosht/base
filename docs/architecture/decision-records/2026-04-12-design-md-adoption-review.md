# `DESIGN.md` 導入計画 Review

## Status

Recorded

## Date

2026-04-12

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Scope

- root の `DESIGN.md` を canonical にする方針の妥当性
- `docs/design/` の追加が knowledge surface と検証導線へ与える影響
- sample 配置と `preview.html` 運用の妥当性

## Findings

### 1. 高: sample 側に同名の `DESIGN.md` を増やさない

影響する契約・文書:

- root の canonical `DESIGN.md`
- `docs/design/samples/**`
- `docs/ai/repo-contract.md`

指摘:

- `docs/design/samples/**/DESIGN.md` のように sample 側も同名にすると、repo 内検索や agent の単純探索で root の正本と混同しやすい
- root だけを `DESIGN.md` とし、sample は `DESIGN.sample.md` や `reference-design.md` など、非 canonical と分かる名前に寄せる方がよい

### 2. 高: 検証導線を `template-health` だけで閉じない

影響する契約・文書:

- `scripts/ci/validate_template.py`
- `tests/test_template_contract.py`
- `.github/workflows/template-health.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/test-all-subsystems.yml`
- `docs/architecture/base-harness-set.toml`
- `docs/architecture/base-harness-set.md`

指摘:

- root `DESIGN.md` の追加は `scripts/ci/validate_template.py` と `tests/test_template_contract.py` だけでなく、workflow trigger 側も `ci.yml` と `test-all-subsystems.yml` まで含めて追従させる必要がある
- `docs/design/**` を template の常設面に含めるなら、template contract だけでなく base harness の正本にも反映する必要がある

### 3. 中: checklist と reading order の正本は `docs/ai/repo-contract.md` を先に更新する

影響する契約・文書:

- `docs/ai/repo-contract.md`
- `README.md`
- `CONTRIBUTING.md`

指摘:

- `README.md` と `CONTRIBUTING.md` だけに `DESIGN.md` 更新を足しても、generated repo の正本チェックリストと読書順に `DESIGN.md` が現れない
- `docs/ai/repo-contract.md` の `Reading Order`、`Repository Roles`、`Generated Repo Checklist` に `DESIGN.md` を追加したうえで、README と contributing 文書へ展開する方が筋がよい

### 4. 中: `preview.html` には陳腐化対策を入れる

影響する契約・文書:

- `docs/design/samples/**/preview.html`
- sample の `DESIGN` 文書

指摘:

- `preview.html` を手作業の static artifact に留める判断は v1 として許容できるが、存在確認だけでは `DESIGN` 文書との乖離を防げない
- preview には `reference-only` の明示、source note、reviewed date、または同期ルールのいずれかを持たせる方がよい

## Outcome

- root の `DESIGN.md` を canonical にする判断自体は維持してよい
- 実装着手前に閉じるべき主要論点は、sample 命名、検証導線、`repo-contract` への昇格、preview の鮮度管理の 4 点である

## Handoff Notes

- このメモは review 結果だけを独立して残すためのものであり、計画本文の修正案は含めない
- 実装担当の AI は、この finding をもとに計画メモと関連文書を更新する
