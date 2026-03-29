# 構成概要

## Intent

このテンプレートは、GitHub の標準機能と AI エージェント運用を同時に立ち上げるための共通運用面を提供します。

## Layering

- root: 人間と agent の入口、shared settings、GitHub governance
- `docs/`: 長文の正本
- `.claude/`, `.codex/`, `.agents/`: tool-specific settings / entrypoints
- `scripts/ci/`: template 健全性検証
- `scripts/template/`: starter overlay 適用ロジック
- `templates/`: Python / Next.js の overlay catalog
- `src/`, `tests/`, `secrets/`: generated repo 側で使う protected or product-facing paths

## Starter Strategy

- `python-minimal`: root の `src/` と `tests/` に最小サンプルを追加
- `nextjs-app`: `apps/web/` に Next.js サンプルを追加

この切り分けにより、root の control-plane を壊さずに複数 stack を配布できます。

## Knowledge Surface

- 運用中の正本は `docs/ai/`, `docs/architecture/`, `docs/standards/` に置く
- `docs/repository-template-design.md` は入力設計書として残すが、更新の中心にはしない
- `.cursor/`, `GEMINI.md`, `.codex/skills/` は互換面として残ることがある
- どこに何を書くか迷う場合は `docs/architecture/knowledge-architecture.md` を参照する

## After Template Creation

1. owner placeholder を更新する
2. `docs/architecture/overview.md` を実プロジェクト向けに書き換える
3. `docs/standards/` を stack と組織ルールに合わせて更新する
4. 必要な overlay を適用する
