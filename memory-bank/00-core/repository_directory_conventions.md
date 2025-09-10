# Repository Directory Conventions (Meaning & Placement Rules)

タグ: `directory-conventions`, `placement-policy`, `knowledge-architecture`

## 1. Canonical Rules
- `AGENTS.md`: 規約カノニカル。強制力ある運用ルールと参照（テンプレ/フレーム/手順）の指示を集約。
- `memory-bank/`: 再利用知識の保管庫（AI最適・検索最適・構造化）。テンプレ/フレームワーク/パターン/学びを体系化。
- `docs/`: エージェントの成果物（納品/配布/参照される最終物）。人間向けかは不問、成果として提示するもの。
- `checklists/`: 進捗運用の“現場用”チェックリスト（Issue/PR/タスク単位）。高頻度更新。完了後は学びを memory-bank へ要約反映。
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
- `memory-bank/06-project/context|progress/`: プロジェクト固有の文脈/進捗の“学び”を要点化して保存
- `memory-bank/03-patterns|04-quality|09-meta`: パターン・品質フレーム・コマンド等の再利用知識

## 4. codex_mcp 協働相談テンプレ配置規約
- テンプレ（カノニカル）: `memory-bank/11-checklist-driven/templates/codex_mcp_collaboration_checklist_template.md`
- 実タスク用（運用実体）: `checklists/<date|issue>_codex_mcp_<topic>_checklist.md`
- 収束後の学び: `memory-bank/06-project/progress/` または `memory-bank/03-patterns/` に Problem→Approach→Outcome→Next で要点記録

## 5. 命名規約
- テンプレ: `<theme>_checklist_template.md`
- 実タスク用: `<date|issue>_<topic>_checklist.md`

## 6. 運用の流れ（例: codex_mcp）
1) テンプレを複製して `checklists/` に作成
2) 進行中は `checklists/` を更新
3) 解決/収束後、学びを `memory-bank/06-project/progress/` 等へ要点記録

