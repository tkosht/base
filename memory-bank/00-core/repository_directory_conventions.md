# Repository Directory Conventions (Meaning & Placement Rules)

- Status: Reference
- Load: OnDemand
- Authority: Operational
- Canonical: `AGENTS.md`

タグ: `directory-conventions`, `placement-policy`, `knowledge-architecture`

## 1. Canonical Rules
- `AGENTS.md`: 規約カノニカル。強制力ある運用ルールと参照（テンプレ/フレーム/手順）の指示を集約。
- `memory-bank/`: 再利用知識の保管庫（AI最適・検索最適・構造化）。テンプレ/フレームワーク/パターン/学びを体系化。
- `docs/`: エージェントの成果物（納品/配布/参照される最終物）。人間向けかは不問、成果として提示するもの。
- `output/checklists/`: 一時的な進捗運用チェックリスト置き場。repo の正本ではなく、完了後は学びだけを `memory-bank/` に要約反映する。
- `output/`: 実行時の生成物・一時成果。納品確定物ではない。

## 2. Judgment Matrix (memory-bank vs docs)
- 目的
  - 内部運用・再利用・AI最適参照 → `memory-bank/`
  - 成果として提示・配布・公開（最終物） → `docs/`
- 安定度/更新頻度
  - 長期安定・低頻度更新 → `memory-bank/`
  - 時点の成果として確定させたい → `docs/`
- 消費主体/経路
  - エージェントの Micro/Fast プローブで常時参照 → `memory-bank/`
  - ステークホルダーへの提示/配布 → `docs/`
- 粒度/汎用性
  - 汎用テンプレ/パターン/フレームワーク → `memory-bank/`
  - プロジェクト/イテレーション固有の最終まとめ → `docs/`

## 3. Subtree Conventions (主要例)
- `memory-bank/11-checklist-driven/templates/`: 汎用チェックリストの雛形置き場（使い回し前提・変更頻度低）
- `memory-bank/03-patterns`: パターン・運用上の学び
- `memory-bank/07-external-research`: 外部一次情報の要点と source-to-claim 対応

## 4. codex_mcp 協働相談テンプレ配置規約
- テンプレ（カノニカル）: `memory-bank/11-checklist-driven/templates/codex_mcp_collaboration_checklist_template.md`
- 実タスク用（運用実体）: `output/checklists/<date|issue>_codex_mcp_<topic>_checklist.md`
- 収束後の学び: `memory-bank/03-patterns/` など再利用しやすい場所へ Problem→Approach→Outcome→Next で要点記録

## 5. 命名規約
- テンプレ: `<theme>_checklist_template.md`
- 実タスク用: `<date|issue>_<topic>_checklist.md`

## 6. 運用の流れ（例: codex_mcp）
1) テンプレを複製して `output/checklists/` に作成
2) 進行中は `output/checklists/` を更新
3) 解決/収束後、学びを `memory-bank/03-patterns/` 等へ要点記録
