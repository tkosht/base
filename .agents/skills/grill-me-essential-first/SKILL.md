---
name: grill-me-essential-first
description: "Interrogate a plan or design by resolving the highest-impact unknowns before details. Use when the user wants essential-first design grilling, asks to focus on core issues first, or wants scope, success criteria, constraints, and major risks clarified before detailed questions."
---

# Grill Me Essential First

## Purpose
設計や計画の詰めで、本質論点を先に閉じる。重要な未解決事項が残る間は、細部の確認を掘らない。

## Essential Gate
- 重要質問とは、`スコープ / 成功判定 / 実装方針 / 主要リスク / 受け入れ条件` を変えうる質問。
- 重要論点が残っている間は、文言調整、命名、軽微なユーザーインターフェース、局所最適化などを `parking lot` に送る。
- コードベースで答えられるものは、質問せずに探索して埋める。

## Workflow
1. 最初に、未解決の本質論点 `Top 5` を優先順で提示する。
2. `Top 5` の既定観点は `目的 / 成功条件 / 非目標 / 制約 / 最大リスク` とする。
3. 質問は常に 1 件ずつにし、各質問に `なぜ今それを聞くのか` と `推奨回答` を添える。
4. `Top 5` が閉じるまでは細部質問をしない。低優先度の詳細は `parking lot` に追加するだけで、その場では掘らない。
5. `Top 5` を一巡したら、`確定事項 / 未決定 / parking lot / 次の最重要論点` を要約する。
6. 要約後は、明示確認を待たずに `parking lot` 側の詳細論点へ自動移行する。
