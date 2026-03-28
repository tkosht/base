---
name: repo-instruction-optimizer
description: "このリポジトリの repo-local instruction surface を整理・最適化・評価するときに使う。Use when requests involve AGENTS.md / CLAUDE.md / GEMINI.md / Cursor rules の canonical 化、thin adapter 化、Always-On context の削減、OnDemand / Deprecated への整理、instruction 変更のレビュー、または before/after の軽量評価設計。"
---

# Repo Instruction Optimizer

## Purpose

- この repo の instruction surface を、`canonical + thin adapters + OnDemand references` の形へ整理する。
- 固定コンテキストを減らしつつ、currentness、scoped edit、review fidelity を落とさない変更へ収束させる。

## Workflow

1. `references/source-map.md` を読み、正本・adapter・互換 shim・補助文書・評価根拠の位置を確認する。
2. `references/design-principles.md` を使い、canonical 面、Always-On 面、OnDemand 面、Deprecated 面を切り分ける。
3. 変更案を作るときは、正本には repo-local の不変条件だけを残し、長い手順や低頻度手順は参照文書へ落とす。
4. adapter は「薄い説明文」ではなく、正本への実 import / 実参照が効く形にそろえる。
5. 変更後は `references/evaluation-loop.md` の軽量評価ループで、currentness、scoped edit、review task の regressions を先に潰す。
6. 勝ち筋が見えたら、要約 metrics を残しつつ heavy artifact は commit 対象から外す。

## References

- `references/source-map.md`
- `references/design-principles.md`
- `references/evaluation-loop.md`
