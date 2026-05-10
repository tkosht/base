# `DESIGN.md` 導入計画 Review 15

## Status

Recorded

## Date

2026-04-19

## Review Target

- `docs/architecture/decision-records/2026-04-12-design-md-adoption-plan.md`

## Purpose

このメモは、「review を止める条件」ではなく、このフェーズで担保すべき品質を明文化するための補助レビュー結果です。

以後の review では、個別指摘を増やすこと自体を目的にせず、下記の品質軸のどれに未充足があるかで判定します。

## このフェーズで担保すべき品質

### 1. 正本分離の品質

狙い:

- `root DESIGN.md`
- `docs/design/README.md`
- `docs/ai/repo-contract.md`
- `Generated Repo Checklist`

の役割が重ならず、どこが正本でどこが補助面かを一意に読めること。

担保条件:

- 各 artifact に「正本 / 補助面 / mirror / reference-only」のいずれかが明示されている
- sync policy の正本が 1 箇所に固定されている
- canonical な文書に mirror policy を残す場合は、責務が 1 文で制限されている

### 2. 更新責務の品質

狙い:

- generated repo で通常更新する文書と、template-maintained な文書が混ざらないこと。

担保条件:

- root `DESIGN.md` が generated repo の通常更新対象として固定されている
- `docs/design/README.md` が template-maintained 補助面として固定されている
- `template-maintained` が「自動同期」を意味しないことが正本に明記されている
- 手動取り込み方針が `repo-contract` に定義されている

### 3. 検査境界の品質

狙い:

- `run_checks()` と `tests/test_template_contract.py` が守る契約と、manual review に残す文言が混ざらないこと。

担保条件:

- machine-check 対象が `Validation` と `Test Plan` の両方で一致している
- manual review 対象が `README.md` / `CONTRIBUTING.md` の mirror に限定されている
- canonical section を manual review 扱いに落としていない
- mutation test の対象が section 単位で読める

### 4. 発見導線の品質

狙い:

- AI エージェントと maintainer が design 系作業の初動で迷わないこと。

担保条件:

- `repo-contract` の `Reading Order` に design 系作業時の追加読書先がある
- `Repository Roles` に `docs/design/README.md` の役割がある
- 必要なら「design 系作業では root `DESIGN.md` を先に読む」契約が machine-check 対象に含まれる

### 5. 実装可能性の品質

狙い:

- plan の記述が、既存の `validate_template.py` / `tests/test_template_contract.py` の構造に無理なく落ちること。

担保条件:

- glob 前提ではなく concrete path 前提で required path を表現している
- validator で判定可能な条件だけを machine-check に上げている
- `run_checks()` の needle 検査で取り違えやすい箇所は section 単位や責務文言単位で固定している
- hidden policy を validator にだけ持ち込んでいない

### 6. reference sample 分離の品質

狙い:

- sample が canonical surface を汚染せず、agent が root 正本を取り違えないこと。

担保条件:

- sample 名は `DESIGN.sample.md` に固定されている
- repo 内に複数の `DESIGN.md` を置かない
- sample は `reference-only`、root は canonical であることが明示されている
- `preview.html` に source note、reviewed date、同期ルール注記がある

## Artifact Quality Matrix

| Artifact | 主責務 | 区分 | 通常更新主体 | 検証方法 | fail 条件の例 |
| --- | --- | --- | --- | --- | --- |
| `DESIGN.md` | generated repo の visual contract 正本 | canonical | generated repo | machine-check | required path 欠落、workflow trigger 欠落、design 用語契約欠落 |
| `docs/design/README.md` | design guidance の補助正本 | canonical supplement | template | machine-check | 補助面責務の文言消失、`repo-contract` 参照消失、design 文書用語契約 drift |
| `docs/ai/repo-contract.md` | sync policy、読書順、checklist の正本 | canonical | template | machine-check | 読書導線消失、手動取り込み方針消失、checklist section drift |
| `Generated Repo Checklist` | generated repo 初期更新の canonical section | canonical section | template | machine-check | root `DESIGN.md` 更新対象の記述消失、`docs/design/README.md` 非更新方針消失 |
| `README.md` | 人間向け mirror 導線 | mirror | template / maintainer | manual review | `repo-contract` と説明不一致 |
| `CONTRIBUTING.md` | 人間向け mirror 導線 | mirror | template / maintainer | manual review | `repo-contract` と説明不一致 |
| `DESIGN.sample.md` | reference sample | reference-only | template | machine-check | sample 名 drift、略語契約 drift、root 正本との混同 |
| `preview.html` | sample の curated static artifact | reference-only | template | static check | `reference-only`、source note、reviewed date、同期注記の欠落 |

## Review Outcome

- 以後の review では、新しい指摘を出す場合も、まず上記 6 品質のどれに関わる未充足かを示す
- `plan` の wording 差分そのものではなく、「正本分離」「更新責務」「検査境界」「発見導線」「実装可能性」「sample 分離」のどこが壊れるかで判断する
- これにより、局所的な合格基準の追加ではなく、このフェーズで担保すべき品質に対する網羅性で review できる

## Handoff Notes

- 次回以降の review では、finding ごとに上の品質軸を 1 つ以上明記して紐付ける
- 新しい指摘が出る場合は、既存の品質軸で説明できるかを先に確認し、説明できない場合だけ品質軸自体の不足として扱う
