# auto-refine-agents MVP Phase1〜3 実装進捗メモ（2025-11-15）

## 実装サマリ

- Phase1: Evaluator I/O v2 スケルトン
  - `.cursor/commands/agent/agent_goal_run.md`: Evaluator I/O v2 形式で `.agent/logs/eval/input.json` / `result.json` を生成するよう拡張。
    - input.json: `task_id`, `goal`, `auto{rubric,artifacts,weights}`, `rubric:null`, `artifacts:null`, `budget.max_cost` を出力。
    - result.json: `ok`, `scores.total`, `notes`, `evidence{failed_checks,raw}`, `metrics{cost,latency_ms}`, `rubric_id`, `task_id` を出力（評価ロジックはスケルトン）。
  - `docs/auto-refine-agents/quickstart_goal_only.md` / `docs/auto-refine-agents/cli-implementation-design.md`:
    - 上記 v2 I/O スキーマに合わせて JSON 例を更新。
  - `agent_quickstart.md` / `agent_full_cycle.md`:
    - `agent_goal_run.md` のコードブロック実行パターンは維持しており、`ok` / `scores.total` の利用が壊れていないことを手動確認。

- Phase2: AO v0（Artifacts Orchestrator 最小版）
  - 新規: `.cursor/commands/agent/agent_ao_run.md`
    - ACE 初期化後に `.agent/logs` / `.agent/generated/artifacts` / `.agent/state` を作成。
    - `.agent/logs/app.log` を `: >` で存在保証（空ファイルとして初期化）。
    - `.agent/generated/artifacts/metrics.json` が無い or 空の場合に `{"total_cost":0,"latency_ms":0,"calls":0}` で初期化。
    - `TASK_ID` が設定されている場合のみ、`.agent/state/artifacts_map.json` に `task_id → {app_log,metrics}` を `jq` でマージ（キー付きオブジェクト）。
  - `.cursor/commands/agent/eval_perturb_suite.md`:
    - 事前のログ/メトリクス初期化を `agent_ao_run.md` 呼び出しに置き換え、AO v0 を再利用。
  - `agent/registry/rubrics/code_quality_v1.yaml`:
    - `no_errors_in_logs` / `budget_within_limit` の detector が `.agent/logs/` / `.agent/generated/artifacts/metrics.json` を参照しており、AO v0 の出力パスと整合していることを確認（コード変更なし）。

- Phase3: RAS v0（Rubric Auto Synthesis 最小版）
  - 新規: `.cursor/commands/agent/agent_ras_autogen.md`
    - 入力: `GOAL`（環境変数 or `.agent/logs/eval/input.json.goal`）、`agent/registry/config/rubric_autogen.defaults.yaml`。
    - `TASK_ID` 解決: 環境変数 `TASK_ID` 優先 → `input.json.task_id` → fallback で `date +%s` ベース。
    - yq 利用可能な環境:
      - defaults を JSON 化し、`objectives_default` / `checks_catalog` / `thresholds` から Rubric YAML を生成。
      - `objectives_default` は `name/weight` の配列に変換。
      - `checks_catalog` は各エントリに対し `name/detector/expect` をコピーし、weight は `1.0 / checks数` で均等割り当て。
      - メタデータ: `metadata.goal` に GOAL スナップショット、`metadata.source` に `rubric_autogen.defaults.yaml` を設定。
    - yq 不在環境（現在の CI 環境）:
      - 設計書の例に準拠した固定 Rubric を `.agent/generated/rubrics/<task_id>.yaml` に出力（objectives / checks / thresholds は設計どおり）。
      - `metadata.goal` は空文字、`metadata.source` は `rubric_autogen.defaults.yaml`。
    - `.agent/state/rubric_history.json`:
      - `[{task_id,rubric_id,source,goal,created_at}, ...]` 形式の配列として管理。
      - 既存ファイルがあれば配列に append、新規の場合は 1要素配列として生成。
  - `.cursor/commands/agent/agent_goal_run.md` の統合フロー変更:
    - ACE 初期化 → `TASK_ID` / `GOAL` 決定 → Evaluator I/O v2 形式で `input.json` 書き出し →
      `agent_ras_autogen` 呼び出し（Rubric YAML + rubric_history.json） →
      `agent_ao_run` 呼び出し（app.log / metrics.json / artifacts_map 初期化） →
      スケルトン Evaluator で `result.json` 生成。
    - `result.json.rubric_id` は `autogen_code_quality_v1@1` に固定し、RAS v0 が出力する Rubric と整合。

- Phase4 相当: outerloop × Evaluator v2 / RAS / AO 連携の下準備
  - `.cursor/commands/agent/outerloop_abtest.md`:
    - 各テンプレート×反復ごとに一意な `TASK_ID` を生成（`ab-<template>-<i>-<timestamp>-<RANDOM>`）し、環境変数 `TASK_ID` / `GOAL` / `TEMPLATE_ID` を設定。
    - その状態で `agent_goal_run.md` の bash ブロックを呼び出し、Evaluator I/O v2 / RAS v0 / AO v0 を一括実行。
    - 各試行終了後、`.agent/logs/eval/result.json` から
      `template_id, iteration, task_id, ok, scores, metrics, rubric_id` を抽出し、
      `.agent/logs/eval/ab/<template>.jsonl` および `summary_raw.jsonl` に1行JSONとして追記。
    - `summary.json` 集計ロジックは `scores.total` / `metrics.cost` の平均に基づく既存形式を維持しており、
      今後 Evaluator が実スコア/コストを返すようになってもそのまま利用可能。
  - `.cursor/commands/agent/outerloop_promote.md`:
    - Gate 判定ロジック自体は変更していないが、
      `summary.json` の元データが Evaluator v2 結果（RAS/AO を通過した result.json）に変わった。
      現時点では still skeleton（scores=1.0, cost=0）だが、構造的には v2 ベースに移行済み。
  - `.cursor/commands/agent/agent_goal_run.md` / `.cursor/commands/agent/agent_ao_run.md` / `.cursor/commands/agent/agent_ras_autogen.md`:
    - `TASK_ID` を `export` し、サブタスク（RAS/AO）が同一 `TASK_ID` を参照できるように調整。
    - AO v0 が `TASK_ID` を取得できるようになったことで、
      `.agent/state/artifacts_map.json` に `task_id → {app_log,metrics}` のマップが蓄積されるようになった。

## 既知の制約・今後の改善余地

- 評価ロジック:
  - 現状の Evaluator は `rg` によるログスキャンのみ実行し、`result.json.ok` / `scores.total` は固定（常に `true` / `1.0`）。Rubric 内容や checks の実行は未実装。
  - outerloop（`outerloop_abtest` / `outerloop_promote`）は v2 I/O / RAS / AO とまだ統合しておらず、スコアも固定のまま。

- RAS v0:
  - yq 不在環境では defaults を直接読めないため、Rubric 本体は設計書ベースの固定 YAML で生成している（`metadata.goal` も空）。本番環境では yq を前提とした動的生成に寄せるべき。
  - checks の weight 割り当ては v0 では単純化（均等 or 設計固定）しており、実行履歴ベースの最適化は未実装（Phase4 以降）。

- AO v0:
  - `.agent/state/artifacts_map.json` は `TASK_ID` が環境変数で明示されている場合のみ更新（現状 `agent_goal_run` からの呼び出しでは設定済みなので1:1で記録される）。
  - 標準 artifacts のパス整合は `code_quality_v1.yaml` とは一致しているが、`rubric_autogen.defaults.yaml` の detector とはパスが異なる（logs/ / artifacts/）。この整合は今後のリファイン対象。
  - 今回、RAS v0 の生成 Rubric に対しては detector を `.agent/logs/` / `.agent/generated/artifacts/metrics.json` および `.total_cost` に正規化したため、
    RAS 生成 Rubric と AO v0 / code_quality_v1.yaml の参照パスは整合した。
    一方で defaults 自体の記述（logs/ / artifacts/metrics.json / .cost）はそのままなので、
    正典側をどこまで書き換えるかは別途検討が必要。

## 簡易検証ログ（ローカル手動）

- Phase1:
  - `awk ... agent_goal_run.md | bash` 実行後:
    - `.agent/logs/eval/input.json` が v2 スキーマどおり（`task_id,goal,auto, ...`）。
    - `.agent/logs/eval/result.json` が v2 スキーマどおり（`ok,scores.total,notes,evidence,metrics,rubric_id,task_id`）。
  - `agent_quickstart.md` / `agent_full_cycle.md` の `ok` / `scores.total` 利用は継続動作。

- Phase2:
  - `awk ... agent_ao_run.md | bash` 実行により:
    - `.agent/logs/app.log` / `.agent/generated/artifacts/metrics.json` が生成され、後者は `{"total_cost":0,"latency_ms":0,"calls":0}`。
  - `awk ... eval_perturb_suite.md | bash` 実行により:
    - AO v0 経由で標準 artifacts が初期化され、`tests/perturbation_suite.sh` 不在時も `perturb.json` に `{"ok":true,...}` が出力されることを確認。

- Phase3:
  - `awk ... agent_goal_run.md | bash` 実行後:
    - `.agent/logs/eval/input.json` / `result.json` が v2 スキーマで更新されていることに加え、
    - `.agent/generated/rubrics/<task_id>.yaml` が生成され、`id: autogen_code_quality_v1` / `version: 1` / objectives / checks / thresholds が正しく構造化されていることを確認。
    - `.agent/state/rubric_history.json` に `task_id` / `rubric_id: autogen_code_quality_v1@1` / `source` / `goal` / `created_at` が追記されていることを確認。
  - `agent_full_cycle.md` 経由でのフルサイクル実行:
    - Inner-Loop（agent_goal_run）→ 摂動スイート（eval_perturb_suite）→ outerloop_abtest → outerloop_promote → agent_templates_push_pr の一連の流れが通ることを確認。
    - `summary_raw.jsonl` の各行は Evaluator v2 result.json 由来の `scores` / `metrics` / `rubric_id` を含んでおり、
      `summary.json` はそれらの平均値に基づき `id,n,s_avg,c_avg` を出力。
    - `.agent/state/artifacts_map.json` は各 `task_id`（Goal 実行 + AB 各試行）に対して `.agent/logs/app.log` / `.agent/generated/artifacts/metrics.json` を指すマップとして更新されている。
