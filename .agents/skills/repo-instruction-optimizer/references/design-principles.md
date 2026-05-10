# Design Principles

## Core Model

- 正本は 1 枚に寄せる。repo-local の不変条件は canonical doc にだけ置く。
- `CLAUDE.md`、`GEMINI.md`、Cursor rules などの tool-facing 面は thin adapter にする。
- adapter は説明だけで済ませず、正本への実 import / 実参照が効く形でそろえる。

## Context Budget

- 比較は file size ではなく `effective always-loaded bytes` を使う。
- before / after は同じ計測基準で比べる。adapter 本体だけでなく、推移的に常時読まれる正本も含める。
- 巨大な固定指示を残すより、短い canonical doc と必要時参照を優先する。

## Document Placement

- 正本には repo-local の不変条件だけを書く。
- チェックリスト、調査メモ、低頻度の運用手順は `OnDemand` に落とす。
- 旧手順は `Deprecated` として明示し、現役導線から外す。
- 互換維持だけが目的の adapter / shim は短く保ち、新しい規範を書き足さない。

## Quality-Preserving Rules

- currentness: 先にローカル主張を列挙し、その主張だけを公式一次情報で検証する。
- scoped edit: 着手前に隣接実装と対象テストを確認し、最小変更 + 最低 2 本の自前確認を残す。
- review: distinct finding ごとに分け、影響 symbol とテスト名 / 契約名を本文にそのまま書く。

## Common Failure Modes

- adapter が正本を実 import しておらず、canonical 化した規範が効かない。
- before / after の sizing が apples-to-apples になっていない。
- deprecated 手順が現役 playbook に残り、整理結果が自己矛盾する。
- 評価で負けたときに protocol を丸ごと戻してしまい、最小差分の改善則を抽出できない。
