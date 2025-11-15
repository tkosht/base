# auto-refine-agents MVP実装計画メモ（Phase1〜3, 2025-11-15）

## 概要

- 目的: auto-refine-agents の MVP として、以下の3フェーズを実装するための計画を固める。
  - Phase1: Evaluator I/O v2 スケルトン整備
  - Phase2: AO v0（Artifacts Orchestrator 最小版）
  - Phase3: RAS v0（Rubric Auto Synthesis 最小版）
- 詳細設計は `docs/auto-refine-agents/mvp_impl_plan_phase1-3_evaluator_ras_ao.md` に記載。

## フェーズ別の要点（サマリ）

### Phase1 — Evaluator I/O v2 スケルトン

- ゴール:
  - `agent_goal_run.md` が `evaluation-governance.md` 記載の Evaluator JSON I/O v2 に沿った入出力を生成する。
- 主な対応:
  - `input.json` に `task_id` / `goal` / `auto` / `rubric` / `artifacts` / `budget` を追加（rubric/artifacts は null/stub）。
  - `result.json` に `evidence` / `metrics` / `rubric_id` / `task_id` を追加（中身はスケルトン）。
  - ドキュメントの I/O 例と実際のJSON構造を揃える。

### Phase2 — AO v0（Artifacts Orchestrator 最小版）

- ゴール:
  - Rubric の detector が参照する artifacts を、自動で生成・初期化できるようにする。
- 主な対応:
  - `.agent/logs/app.log` と `.agent/generated/artifacts/metrics.json` を標準化し、常に存在するようにする。
  - `metrics.json` の最小スキーマ（例: `total_cost`, `latency_ms`, `calls`）を定義。
  - 必要に応じて `artifacts_map.json` を `.agent/state/` に作成（task_id → artifactsパス）。

### Phase3 — RAS v0（Rubric Auto Synthesis 最小版）

- ゴール:
  - `agent/registry/config/rubric_autogen.defaults.yaml` をもとに、Rubric を自動生成して `.agent/generated/rubrics/*.yaml` に保存する。
- 主な対応:
  - 新タスク `agent_ras_autogen.md` を作成し、defaults から最小Rubricを生成。
  - `.agent/state/rubric_history.json` に `task_id` / `rubric_id` / `goal` 等の履歴を書き込む。
  - `agent_goal_run.md` から RAS v0 と AO v0 を呼び出し、Goal → Rubric → 評価入力 までのルートを通す。

## 実装順序の推奨

1. Phase1 を先に実装し、Evaluator I/O のスキーマを固定。
2. Phase2 で artifacts の初期化を行い、Rubric の detector が破綻しない状態にする。
3. Phase3 で RAS v0 を導入し、Rubric 自動生成パスを構築する。

このメモは「どこから実装を始めるべきか」「どのドキュメントを参照すればよいか」を素早く思い出すためのサマリとして使用する。

