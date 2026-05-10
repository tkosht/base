# grill-me-essential-first

- Purpose: 本質論点を先に詰め、重要論点が閉じるまで細部を `parking lot` に送る
- Use when: 設計や計画で、まず `目的 / 成功条件 / 非目標 / 制約 / 最大リスク` を固めたいとき。`本質優先で grill me`、`重要論点から詰めたい` と明示されたとき
- Skill source: `.agents/skills/grill-me-essential-first`
- Claude shim: `.claude/skills/grill-me-essential-first`
- Implementation: repo-local
- Upstream sync: なし

## Default Interaction Contract

- 最初に未解決の本質論点 `Top 5` を提示する
- `Top 5` の既定観点は `目的 / 成功条件 / 非目標 / 制約 / 最大リスク`
- 重要質問は `スコープ / 成功判定 / 実装方針 / 主要リスク / 受け入れ条件` を変えうるものと定義する
- 重要論点が残る間は細部質問を禁止し、低優先度項目は `parking lot` に送る
- 各質問は 1 件ずつにし、`なぜ今それを聞くのか` と `推奨回答` を添える
- `Top 5` を一巡したら `確定事項 / 未決定 / parking lot / 次の最重要論点` を要約する
- 要約後は `parking lot` の詳細へ自動移行する
- コードベースで答えられるものは探索で回収する

## Role Split

- `grill-me`: 全方位の深掘り用。設計木の各分岐を順に詰める。
- `grill-me-essential-first`: 本質優先の設計詰め用。スコープ、成功判定、主要リスクに効く問いから先に閉じる。
