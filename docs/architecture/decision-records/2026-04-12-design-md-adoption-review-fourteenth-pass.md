# `DESIGN.md` 導入計画 Review 14

## Status

Recorded

## Date

2026-04-19

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Review Viewpoints

### このフェーズで本質的に重要なこと

- 正本を一本化すること
- 更新責務を固定すること
- 自動検査と手動確認の境界を固定すること
- AI エージェントと maintainer の読書導線を壊さないこと

### 重点観点

- root `DESIGN.md`、`docs/design/README.md`、`docs/ai/repo-contract.md`、`Generated Repo Checklist` の役割が重ならず、一意に読めること
- generated repo が通常更新する文書と、template-maintained として扱う文書が明確に分かれていること
- `run_checks()` と `tests/test_template_contract.py` で守る契約と、manual review に残す契約が混ざっていないこと
- `Reading Order`、`Repository Roles`、checklist が同じメッセージを返し、design 系作業の初動で迷わないこと

### 今回のフェーズで特に重い論点

- `DESIGN.md` の内容詳細より、`DESIGN.md` 導入を repo-wide の運用契約として閉じられているか
- とくに `docs/design/README.md` を canonical な補助面に上げた以上、そこに残す mirror policy をどう扱うか

## Findings

### 1. 中: `docs/design/README.md` に残す mirror policy の扱いを固定した方がよい

影響する契約・関数・テスト:

- `docs/design/README.md`
- `docs/ai/repo-contract.md`
- `run_checks()`
- `tests/test_template_contract.py`

指摘:

- 計画では `docs/design/README.md` を canonical な補助面として `PRIMARY_DOCS` に含める前提まで整理されている
- 一方で、`template-maintained` / 非自動同期ポリシーの正本は `docs/ai/repo-contract.md` に固定し、`docs/design/README.md` 側は mirror として持つ前提になっている
- さらに validation では、`docs/design/README.md` に展開した mirror 文言は機械検査の対象外とする方針になっている
- このままだと、canonical な補助面に stale な運用説明が残っても自動では検知されない

合格基準:

- 次のどちらかに固定する
- `docs/design/README.md` の非自動同期ポリシー記述を最小化し、`docs/ai/repo-contract.md` 参照 1 文に縮める
- または mirror 記述を残すなら、`run_checks()` と `tests/test_template_contract.py` の整合検査対象に含める
- `docs/design/README.md` の責務を 1 文で固定する
- 例: 「この文書は design guidance の canonical 補助面であり、sync policy の正本ではない」
- `Decision Summary`、`Supporting Docs`、`Validation`、`Test Plan` の表現が一致している

## Outcome

- `Generated Repo Checklist` の canonical 扱い、workflow path filter の実効カバレッジ、design 略語ルールの適用範囲はかなり閉じている
- 残る本質論点は、canonical な補助面である `docs/design/README.md` に mirror policy をどこまで載せるか、その扱いをどう固定するかである

## Handoff Notes

- このメモは 14 回目の review 結果と、現時点の review 観点整理を独立して残す
- 実装担当の AI は、`docs/design/README.md` の責務を「design guidance の補助正本」までに留めるのか、mirror policy まで machine-check 対象に上げるのかを先に決めるとよい
