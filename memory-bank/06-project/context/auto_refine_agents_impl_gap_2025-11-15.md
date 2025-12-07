# auto-refine-agents 実装状況と設計乖離メモ（2025-11-15）

本メモは、docs/auto-refine-agents 配下の設計と `.cursor/commands/agent/*.md`（CLI実装）の現状を比較し、どこまで実装されていて、どこがスケルトン/未実装かを整理するためのものです。

## 1. 評価パイプライン全体像（設計のおさらい）

- 参照ドキュメント:
  - `docs/auto-refine-agents/architecture_summary.md`
  - `docs/auto-refine-agents/architecture.md`
  - `docs/auto-refine-agents/cli-implementation-design.md`
  - `docs/auto-refine-agents/evaluation-governance.md`
- 設計レベルのポイント:
  - Inner-Loop:
    - Goal 正規化 → プランナー → ACE → 実行者 → 評価者 → リファイナ → ACE へフィードバック。
    - 評価者は Rubric + Artifacts に基づきスコアリング（既定は AutoRubric）。
  - RAS（Rubric Auto Synthesis）:
    - 入力: goal / tests / logs / metrics / 履歴。
    - 出力: rubric YAML（id/version/objectives/checks/thresholds）。
    - 乾式検証で不成立チェックを自動除外。
    - 実行履歴から weights / thresholds を漸進調整。
    - 保存: `.agent/generated/rubrics/*.yaml` + `.agent/state/rubric_history.json`。
  - AO（Artifacts Orchestrator）:
    - 標準 artifacts を `logs/app.log`, `artifacts/metrics.json` に統一。
    - 必要に応じて最小メトリクスを自動生成。
    - RAS が参照する `checks` と `artifacts` の整合を維持。
  - Evaluator I/O v2:
    - 入力: `{"task_id","goal","auto":{"rubric":true,"artifacts":true,"weights":"learned|uniform"},"rubric":null,"artifacts":null,"budget":null}`。
    - 出力: `{"ok","scores","notes","evidence","metrics","rubric_id"}`。
  - outerloop:
    - `outerloop_abtest` でテンプレ A/B スコア＋コストを収集。
    - `outerloop_promote` が Gate MUST（spec/robustness/cost/ホールドアウト/HITL）で昇格可否を判定。
    - Gate 合格時のみ `.agent/generated/rubrics/*.yaml` → `agent/registry/rubrics/` に昇格（PR）。

## 2. 現行 CLI 実装の状況（2025-11-15 時点）

対象ファイル（抜粋）:

- 実行タスク:
  - `.cursor/commands/agent/agent_goal_run.md`
  - `.cursor/commands/agent/agent_quickstart.md`
  - `.cursor/commands/agent/agent_full_cycle.md`
  - `.cursor/commands/agent/eval_perturb_suite.md`
  - `.cursor/commands/agent/outerloop_abtest.md`
  - `.cursor/commands/agent/outerloop_promote.md`
  - `.cursor/commands/agent/agent_templates_pull.md`
  - `.cursor/commands/agent/agent_templates_push_pr.md`
- 正典レジストリ:
  - `agent/registry/rubrics/code_quality_v1.yaml`
  - `agent/registry/config/rubric_autogen.defaults.yaml`
  - `agent/registry/prompts/templates.yaml`

### 2-1. Inner-Loop 評価（agent_goal_run）

- 実装:
  - ACE 自動初期化で `.agent/{state,generated,memory,prompts,config,logs}` を生成。
  - `GOAL="${GOAL:-あなたのGoal}"` で環境変数 GOAL を伝搬（2025-11-15 修正）。
  - `printf '{"goal":"%s","auto":{"rubric":true,"artifacts":true}}' "$GOAL"` を `input.json` に保存。
  - `rg` で ERROR/FAIL/Timeout をスキャンし、結果を無視した上で、
    `jq -R -s '{ok:true, scores:{total:1.0}, notes:["cli-eval (skeleton)"]}'` で常に `ok:true` を返す。
- 評価:
  - Evaluator JSON I/O v2 の「構造」はまだ反映されておらず、`task_id` / `rubric` / `artifacts` / `budget` / `evidence` / `metrics` などは未出力。
  - RAS/AO は「auto:{rubric,artifacts} フラグ」までで止まっており、実際の Rubric 生成や artifacts 整合は未実装。

### 2-2. 摂動ロバスト性スイート（eval_perturb_suite）

- 実装:
  - `.agent/logs/app.log`, `.agent/generated/artifacts/metrics.json` を初期化。
  - `tests/perturbation_suite.sh` があれば実行し exit code を評価、無い場合は `WARN` を出しつつ `ok:true` スタブを `perturb.json` に書く。
- 評価:
  - Rubric の `perturbation_robust` チェックに対応するテスト呼び出し口は用意されている。
  - ただし実際のテストスクリプトや AO 連携（エラーログ集約など）は各プロジェクト側の責務として残っており、auto-refine-agents 側にはまだ最小の枠だけが存在。

### 2-3. outerloop A/B（outerloop_abtest）

- 実装:
  - `TEMPLATES`（既定は `planner.default.v1 planner.candidate.v2`）、`AB_N`（既定 5）で繰り返し実行。
  - 各試行で `{"goal","template_id","auto":{"rubric":true,"artifacts":true},"iteration"}` を生成。
  - その後のパイプラインで `rg` を通したうえで、
    `{"ok":true,"scores":{"total":1.0},"metrics":{"cost":0},...}` に固定するスケルトン評価を実施。
  - 最後に `summary.json` として `id,n,s_avg,c_avg` を集計。
- 評価:
  - Evaluator v2 につなぎ変え可能な構造ではあるが、現状の `scores` / `metrics` は完全に固定値で、A/B の意味をなしていない。
  - RAS が生成した Rubric を使っているわけではなく、`auto:{rubric:true}` フラグも未使用。

### 2-4. outerloop Gate（outerloop_promote）

- 実装:
  - `summary.json` と `perturb.json` を読み込み、以下を Gate MUST としてチェック:
    - 摂動ロバスト性 (`PERT.ok == true`)。
    - `N_MIN >= AB_MIN_N`（反復数十分）。
    - 比較対象 >=2 件。
    - `DELTA >= MIN_DELTA`（スコア差）。
    - `BEST_COST <= MAX_COST`（コスト SLO）。
  - `SKELETON`（全 `s_avg==1.0`）の場合は `MIN_DELTA` を 0.0 に下げるのみで、昇格自体は止めていない。
  - 合格時に `.agent/state/current_template_id` を更新し、`PROMOTE OK` をログに出力。
- 評価:
  - Gate ロジック自体は `evaluation-governance.md` の方向性に近いが、入力となる `s_avg` / `c_avg` がスケルトン（全て 1.0 / 0）であり、「評価を改善するループ」にはまだなっていない。
  - RAS の出力（Rubric）や実際の Evaluator 結果とは未接続。

### 2-5. レジストリ / RAS 設定（agent/registry）

- `agent/registry/rubrics/code_quality_v1.yaml`:
  - spec/robustness/cost/reliability の四つの objective と、`no_errors_in_logs` / `spec_tests_pass` / `perturbation_robust` / `budget_within_limit` の checks を定義。
  - detector のコマンドには `.agent/logs/` や `.agent/generated/artifacts/metrics.json` を参照するものが含まれる。
- `agent/registry/config/rubric_autogen.defaults.yaml`:
  - RAS 用の既定設定（`objectives_default`, `checks_catalog`, `thresholds`, `refine.weights`, `refine.dry_run_prune`）を定義。
- 評価:
  - RAS が参照するべき「正典 Rubric」と「Autogen 設定」は用意されているが、
  - これらを読む CLI 実装（rubric を自動生成して `.agent/generated/rubrics/*.yaml` に書き出す処理）は現時点で存在しない。

## 3. 設計と実装の乖離の整理

### 3-1. RAS（Rubric Auto Synthesis）

- 設計:
  - goal / tests / logs / metrics / 履歴から Rubric を自動生成・更新し、`generated/rubrics` と `rubric_history.json` に保存。
- 現状:
  - `agent/registry/config/rubric_autogen.defaults.yaml` は存在するものの、これを読む RAS 実装は無い。
  - `.agent/generated/rubrics/` は `eval_perturb_suite`・`outerloop` からは未使用（rubrics 生成は手動 or 将来拡張前提）。
- 乖離:
  - 「評価を動的に生成し、その評価自体も改善する」というコア思想が、実装にはまだ反映されていない。

### 3-2. AO（Artifacts Orchestrator）

- 設計:
  - `logs/app.log`, `artifacts/metrics.json` を基準に artifacts を集約・生成し、Rubric `checks` と整合を維持。
- 現状:
  - `eval_perturb_suite` が `.agent/logs/app.log` と `.agent/generated/artifacts/metrics.json` を初期化する程度。
  - AO 固有の整合ロジック（artifacts_map.json 生成など）は未実装。

### 3-3. Evaluator JSON I/O

- 設計:
  - v2 では `task_id` / `goal` / `auto` / `rubric` / `artifacts` / `budget` を入力、`scores` / `evidence` / `metrics` / `rubric_id` を出力。
- 現状:
  - `agent_goal_run` 等では簡略版 `{goal,auto}` → `{ok,scores.total,notes}` のみ。
  - `task_id` / `rubric` / `artifacts` / `budget` / `evidence` / `metrics` はログに出ていない。

### 3-4. outerloop（A/B + Gate + 昇格）

- 設計:
  - RAS + Evaluator による「実際の改善度」を基にテンプレを昇格。
- 現状:
  - A/B はスコア固定、Gate は `summary.json` を使って計算するが、元のスコアがダミー。
  - skeleton 判定は MIN_DELTA 調整にしか使われていない。
- 乖離:
  - outerloop が「テンプレ改善ループ」ではなく「将来ここに改善ループが繋がる枠」として残っている段階。

### 3-5. Middle-Loop / 履歴管理

- 設計:
  - `.agent/state/rubric_history.json` や execution_history で「どの Rubric / テンプレがどう改善したか」を蓄積。
- 現状:
  - `.agent/state/session_history` はディレクトリのみ存在（中身は未実装）。
  - `rubric_history.json` 等の履歴ファイルは現時点で生成されていない。

## 4. 今後の実装計画（ラフな段階構成）

※ここでは方向性のみ列挙し、詳細タスク分解は別メモ・チェックリストで行う前提。

1. Evaluator I/O v2 のスケルトン整備
   - `agent_goal_run` / Quickstart の I/O を `evaluation-governance.md` の JSON スキーマに揃える。
   - `task_id`, `rubric`（stub）, `artifacts`（既定パス）, `budget`（stub）を `input.json` に含める。
   - `result.json` に `evidence` / `metrics` / `rubric_id` / `task_id` を stub として追加。
2. AO v0（Artifcats Orchestrator 最小版）
   - `.agent/logs/app.log`, `.agent/generated/artifacts/metrics.json` の生成と、簡単な `artifacts_map.json` を実装。
   - Rubric の `checks.detector` で参照するパスと実際の artifacts パスの整合検査を入れる。
3. RAS v0（Rubric Autogen 最小版）
   - `agent/registry/config/rubric_autogen.defaults.yaml` を読み込み、
     `goal` と `checks_catalog` を元に「最小 Rubric」を `.agent/generated/rubrics/<task_id>.yaml` に生成する処理を追加。
   - 失敗チェックの dry-run 評価（detector コマンドの試行）と不成立チェックの自動除外だけでも形にする。
4. outerloop の Evaluator 連携
   - `outerloop_abtest` が v2 Evaluator（RAS 生成 Rubric + AO artifacts）を叩いて `scores.total` / `metrics.cost` を埋めるようにする。
   - skeleton モード（Evaluator をまだ繋いでいない場合）は「昇格 NO-OP」にするか、state と exit code で区別できるようにする。
5. Middle-Loop / 履歴
   - `rubric_history.json` に「どの goal / task_id に対して、どの Rubric（ハッシュ）が使われ、どのようなスコアだったか」を追記する処理を追加。
   - outerloop_promote で昇格した場合、その差分（before/after の失敗分布）を履歴に残す。

このメモは「設計 vs 実装のギャップのスナップショット」として位置づけ、実装が進んだら追記/更新する。

