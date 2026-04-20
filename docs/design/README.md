# Design Guidance

この文書は root の `DESIGN.md` を支える design guidance の canonical な補助面です。

同期ポリシーの正本は `docs/ai/repo-contract.md` です。

## Canonical Surface

- root の `DESIGN.md` が generated repo の visual contract の正本
- sample は `docs/design/samples/**/DESIGN.sample.md` と `preview.html` を対にした reference-only artifact
- repo 内で canonical 名の `DESIGN.md` を使うのは root だけ

## How To Use

- design 系作業では、まず root の `DESIGN.md` を読む
- sample は root の `DESIGN.md` を書くときの参考に使い、そのまま正本として流用しない
- 値は曖昧語ではなく、色、余白、font stack、component state を具体値で書く
- 公開 sample の `preview.html` には `reference-only`、source note、reviewed date、sync note を明記する

## Sample Layout

- `docs/design/samples/starter-b2b-corporate/DESIGN.sample.md`
- `docs/design/samples/starter-b2b-corporate/preview.html`

sample は generic starter に限定し、ブランド固有の design sample は public template へ同梱しません。
