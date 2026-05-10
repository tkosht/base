# `DESIGN.md` 導入計画 Review 20

## Status

Recorded

## Date

2026-04-20

## Review Target

- `DESIGN.md` 導入実装一式
- 関連する contract / validator / test / workflow 更新

## Review Viewpoints

今回の実装レビューは、これまで整理してきた次の品質軸に沿って確認した。

- 正本分離
- 更新責務
- 検査境界
- 発見導線
- 実装可能性
- reference sample 分離

## Findings

- 重大な指摘なし

補足:

- root の `DESIGN.md` を唯一の canonical 名とする契約が、文書・validator・test で一致している
- `docs/design/README.md` は design guidance の canonical な補助面として実装され、sync policy の正本は `docs/ai/repo-contract.md` に固定されている
- design 系作業で root `DESIGN.md` を先に読む契約と、`Generated Repo Checklist` section の扱いは machine-check 対象まで落ちている
- `README.md` と `CONTRIBUTING.md` は mirror として扱われ、canonical surface の契約は validator に残っている
- public sample は `DESIGN.sample.md` と `preview.html` に分離され、reference-only 注記も入っている

## Acceptance Criteria

- `DESIGN.md` の canonical 名が repo 内で root のみであり、non-root `DESIGN.md` を validator が拒否する
- `docs/design/README.md` の責務が design guidance の補助面に固定され、sync policy の正本参照が `docs/ai/repo-contract.md` に向いている
- `read-first` 契約、workflow path filter、`Generated Repo Checklist` section が `run_checks()` と mutation test の対象になっている
- design 専用略語契約が `DESIGN.md`、`docs/design/README.md`、`DESIGN.sample.md` に共通適用され、既存の共通用語契約とも矛盾していない
- manual review 対象が `README.md` と `CONTRIBUTING.md` の mirror に限定されている

## Verification

- `make doctor`: pass
- `uv run pytest -q tests/test_template_contract.py`: pass
- `make test`: pass
  - `126 passed, 4 deselected`

## Outcome

- 実装は、ここまでの review で積み上げた意思決定と整合している
- 現時点での残る論点は、計画や実装の欠陥ではなく、今後の wording 変更時に validator / test を一緒に保守する運用上の注意にある

## Handoff Notes

- 以後の review は、計画レビューではなく運用変更や追加仕様に対する差分レビューとして扱うのが自然である
- design 契約に関する prose を変更する場合は、`scripts/ci/validate_template.py` と `tests/test_template_contract.py` を同時に更新する前提で扱う
