# Architecture Overview

## Intent

このテンプレートは、GitHub の standard repository features と AI agent workflows を同時に立ち上げるための control-plane を提供します。

## Layering

- root: 人間と agent の入口、shared settings、GitHub governance
- `docs/`: 長文の source of truth
- `.claude/`, `.codex/`, `.agents/`: tool-specific settings / entrypoints
- `scripts/ci/`: template 健全性検証
- `scripts/template/`: starter overlay 適用ロジック
- `templates/`: Python / Next.js の overlay catalog
- `src/`, `tests/`, `secrets/`: generated repo 側で使う protected or product-facing paths

## Starter Strategy

- `python-minimal`: root の `src/` と `tests/` に最小サンプルを追加
- `nextjs-app`: `apps/web/` に Next.js サンプルを追加

この切り分けにより、root の control-plane を壊さずに複数 stack を配布できます。

## Compatibility Surface

`memory-bank/`, `docs/04.knowledge/`, `.cursor/`, `GEMINI.md`, `.codex/skills/` は互換や移行のために残ることがあります。新しい設計では、追加の正本は `docs/ai/`, `docs/architecture/`, `docs/standards/` に置きます。

## After Template Creation

1. owner placeholder を更新する
2. `docs/architecture/overview.md` を実プロジェクト向けに書き換える
3. `docs/standards/` を stack と組織ルールに合わせて更新する
4. 必要な overlay を適用する
