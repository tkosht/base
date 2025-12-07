# MVP実装計画（Phase1〜3: Evaluator I/O v2 / AO v0 / RAS v0）

本ドキュメントは、auto-refine-agents の MVP として **Phase1〜3（Evaluator I/O v2 スケルトン / AO v0 / RAS v0）** を実装するための詳細な計画・設計を記述する。  
目的は「後続セッションで、迷いなく一貫した方針で実装できるレベルの設計書」とすること。

---

## 0. スコープとゴール

### 0-1. MVPで実現したい状態（Phase1〜3）

- Goal:
  - ユーザが **Goal だけを指定** すると、
    1. Evaluator I/O v2 形式で評価入力/出力が生成され（JSON構造は将来版と互換）、
    2. AO が最低限の artifacts（`logs/app.log`, `artifacts/metrics.json`）を整備し、
    3. RAS が既定設定と環境から **Rubric YAML を自動生成** して `.agent/generated/rubrics/*.yaml` に保存する。
- 非Goal:
  - 本フェーズでは「評価ロジックそのもの」と「Rubric/weightsの自動学習」は **簡易/スタブでよい**。
  - outerloop（A/B + promote）の本格連携は Phase4 以降。

### 0-2. 設計上の前提

- Inner-Loop / Middle-Loop / Outer-Loop のアーキテクチャは `architecture.md` / `architecture_summary.md` / `cli-implementation-design.md` に準拠。
- 三層分離:
  - ランタイム: `.agent/**`
  - 正典: `agent/registry/**`
  - 意思決定/履歴: `memory-bank/**`
- CLIベース:
  - 実装は POSIX shell + `jq` / `yq` / `rg` / `awk` / `sed` / `sqlite3` に限定（ゼロスクリプト方針）。

---

## 1. Phase1 — Evaluator I/O v2 スケルトン

### 1-1. 目的

- `evaluation-governance.md` / `cli-implementation-design.md` に記載の **Evaluator JSON I/O v2** と実装を整合させる。
- まだ「本物の評価」は行わなくてもよいが、**入力/出力の JSON 形は将来版と互換**にしておく。

### 1-2. 対象ファイル

- 実装:
  - `.cursor/commands/agent/agent_goal_run.md`
- ドキュメント:
  - `docs/auto-refine-agents/quickstart_goal_only.md`
  - `docs/auto-refine-agents/cli-implementation-design.md`（該当する Evaluator I/O 例）

### 1-3. 入力JSON（`.agent/logs/eval/input.json`）の設計

現状は `{"goal","auto"}` のみだが、以下の形に拡張する。

```jsonc
{
  "task_id": "string",                 // UUIDでなくても良いが、一意性を持たせる
  "goal": "string",                    // GOAL（環境変数から）
  "auto": {
    "rubric": true,
    "artifacts": true,
    "weights": "learned"               // rubric_autogen.defaults.yaml の refine.weights を反映
  },
  "rubric": null,                      // v2: nullなら RAS が自動生成
  "artifacts": null,                   // v2: nullなら AO が標準セットを用意
  "budget": {
    "max_cost": 0                      // MVP段階では0固定 or 環境変数から注入
  }
}
```

実装方針:

- `agent_goal_run.md` 内で:
  - `TASK_ID="${TASK_ID:-$(date +%s)-$RANDOM}"` のように簡易 `task_id` を生成。
  - `REFINE_WEIGHTS` は `agent/registry/config/rubric_autogen.defaults.yaml` を `yq` で読んで既定値を取得（失敗時は `"learned"` にフォールバック）。
  - 上記 JSON を `printf` + `jq` で構築し、`tee .agent/logs/eval/input.json` で記録。
- `quickstart_goal_only.md` / `cli-implementation-design.md` は、上記構造に合わせて例を更新。

### 1-4. 出力JSON（`.agent/logs/eval/result.json`）の設計

MVPでは評価はスケルトンだが、キー構造を将来版と揃える。

```jsonc
{
  "ok": true,
  "scores": {
    "total": 1.0
  },
  "notes": ["cli-eval (skeleton)"],
  "evidence": {
    "failed_checks": [],
    "raw": {}
  },
  "metrics": {
    "cost": 0,
    "latency_ms": 0
  },
  "rubric_id": "skeleton_v0@0",   // MVPではダミー（RAS v0導入後は置き換え）
  "task_id": "<input.task_id>"
}
```

実装方針:

- `agent_goal_run.md` のパイプライン内で、`TASK_ID` を `jq` に渡し `task_id` を埋める。
- `scores` 追加の拡張（例: spec_compliance など）は Phase1 では見送り、`total` のみでよい。
- `rubric_id` は Phase3 で RAS v0 に差し替える前提で、当面は固定 `"skeleton_v0@0"`。

### 1-5. 検証観点（Phase1完了条件）

- `agent_goal_run` 実行後、`.agent/logs/eval/input.json` / `result.json` の JSON が:
  - `jq` でパース可能であること。
  - 上記キーセットをすべて含んでいること。
- `quickstart_goal_only.md` / `cli-implementation-design.md` のサンプルと実際の JSON 構造が一致。
- 既存の利用者（`agent_quickstart` / `agent_full_cycle`）が破綻しないこと（既存コードは主に `ok` / `scores.total` のみ参照）。

---

## 2. Phase2 — AO v0（Artifacts Orchestrator 最小版）

### 2-1. 目的

- Rubric の `checks.detector` が期待する artifacts を **自動的に用意** し、最低限 `code_quality_v1.yaml` の detector が動く状態にする。
- まだ高度な整合ロジックは不要だが、以下の2点は保証する:
  - `.agent/logs/app.log` が常に存在する。
  - `.agent/generated/artifacts/metrics.json` が JSON として有効で、Rubric の `budget_within_limit` チェックが評価可能。

### 2-2. 対象ファイル

- 実装:
  - `.cursor/commands/agent/eval_perturb_suite.md`
  - （新規）`.cursor/commands/agent/agent_ao_run.md`（名前は後で調整可）
- 正典:
  - `agent/registry/rubrics/code_quality_v1.yaml`（detector の参照パス確認）

### 2-3. AO v0 の役割定義

AO v0 では、以下だけを行う:

1. **標準 artifacts ファイルの存在保証**
   - `.agent/logs/app.log`（空で良い）
   - `.agent/generated/artifacts/metrics.json`
2. **metrics.json の最小スキーマ**
   - 例:
     ```json
     {
       "total_cost": 0,
       "latency_ms": 0,
       "calls": 0
     }
     ```
   - `code_quality_v1.yaml` では `jq '.total_cost'` を参照しているため、このキーを必須とする。
3. （オプション）`artifacts_map.json` の準備
   - `.agent/state/artifacts_map.json` に `task_id` → `{"app_log":"...", "metrics":"..."}` のマップを保存。
   - Phase2 では読み出しロジックまでは必須ではない（Phase3以降で使用）。

### 2-4. 実装案

- `agent_ao_run.md`（新設）:
  - ACE 初期化後に:
    - `mkdir -p .agent/logs .agent/generated/artifacts .agent/state`
    - `: > .agent/logs/app.log`
    - `if [ ! -s .agent/generated/artifacts/metrics.json ]; then printf '{"total_cost":0,"latency_ms":0,"calls":0}\n' > ...; fi`
    - `TASK_ID` があれば `.agent/state/artifacts_map.json` に append（`jq` でマージ）。
- `eval_perturb_suite.md`:
  - すでに `.agent/logs/app.log` と `.agent/generated/artifacts/metrics.json` を初期化しているが、AO v0 に処理を委譲する形にリファクタ可能。
  - MVP段階では重複していてもよいが、長期的には `agent_ao_run` を再利用する。

### 2-5. 検証観点（Phase2完了条件）

- `agent_goal_run` → `agent_ao_run` を実行後:
  - `.agent/logs/app.log` が存在し、`wc -l` などで扱える。
  - `.agent/generated/artifacts/metrics.json` が JSON かつ `jq '.total_cost'` で値が取得できる。
  - `agent/registry/rubrics/code_quality_v1.yaml` の `budget_within_limit` detector が **とりあえず実行可能**（値は0だがエラーにならない）。

---

## 3. Phase3 — RAS v0（Rubric Auto Synthesis 最小版）

### 3-1. 目的

- `agent/registry/config/rubric_autogen.defaults.yaml` をもとに、最低限の Rubric を **自動生成** し、`.agent/generated/rubrics/*.yaml` に保存する。
- まだ高度な最適化は行わないが、「GoalからRubricが生まれる」ルートを一度通す。

### 3-2. 対象ファイル

- 実装:
  - （新規）`.cursor/commands/agent/agent_ras_autogen.md`
  - `.cursor/commands/agent/agent_goal_run.md`（RAS 呼び出しを追加）
- 正典:
  - `agent/registry/config/rubric_autogen.defaults.yaml`
  - `agent/registry/rubrics/code_quality_v1.yaml`（構造を参考）

### 3-3. RAS v0 の挙動仕様

入力:

- `GOAL`（環境変数 / `input.json.goal` から）
- `rubric_autogen.defaults.yaml`

出力:

- `.agent/generated/rubrics/<task_id>.yaml`（YAML）
- `.agent/state/rubric_history.json` の1エントリ

生成される Rubric のイメージ:

```yaml
id: "autogen_code_quality_v1"
version: 1
objectives:
  - name: spec_compliance
    weight: 0.4
  - name: robustness
    weight: 0.3
  - name: cost_efficiency
    weight: 0.2
  - name: runtime_reliability
    weight: 0.1
checks:
  # rubric_autogen.defaults.yaml の checks_catalog から直接生成（v0ではGoal条件でのフィルタはしない）
  - name: no_errors_in_logs
    detector: "rg -n '(ERROR|FAIL|Timeout)' logs/ | wc -l"
    expect: "== 0"
    weight: 0.4
  - name: spec_tests_pass
    detector: "bash tests/spec_run.sh"
    expect: "exit_code == 0"
    weight: 0.3
  - name: budget_within_limit
    detector: "jq '.cost' artifacts/metrics.json"
    expect: "<= budget.max_cost"
    weight: 0.3
thresholds:
  pass_score: 0.9
metadata:
  goal: "<GOALのスナップショット>"
  source: "rubric_autogen.defaults.yaml"
```

※ weight の合計や checks の選択ロジックは v0 ではシンプルで良い（defaults をそのまま使う）。

### 3-4. RAS v0 の内部処理フロー

1. `agent/registry/config/rubric_autogen.defaults.yaml` を `yq` で読み込み。
2. `objectives_default` / `checks_catalog` / `thresholds` をそれぞれ Bash 配列/JSONに展開。
3. v0では Goal ベースのフィルタリングは行わず、catalogの定義をそのまま checks に投影。
4. `TASK_ID` と `GOAL` を埋めた YAML を組み立て、`.agent/generated/rubrics/<task_id>.yaml` に書き出し。
5. `.agent/state/rubric_history.json` に以下のエントリを `jq` で append:
   ```jsonc
   {
     "task_id": "<task_id>",
     "rubric_id": "autogen_code_quality_v1@1",
     "source": "rubric_autogen.defaults.yaml",
     "goal": "<GOAL>",
     "created_at": "2025-11-15T12:34:56Z"
   }
   ```

### 3-5. agent_goal_run との連携

Phase3 の時点で、`agent_goal_run` は次のような流れとする:

1. ACE 初期化。
2. `TASK_ID` / `GOAL` を確定し、Evaluator I/O v2 形式の `input.json` を生成。
3. RAS v0（`agent_ras_autogen`）を呼び出し、`.agent/generated/rubrics/<task_id>.yaml` を生成。
4. AO v0（`agent_ao_run`）を呼び出し、標準 artifacts をセットアップ。
5. （評価ロジックはまだ簡易だが）`result.json` に `rubric_id` / `task_id` を含めたスケルトン結果を書き出す。

**重要:** Phase3の時点では「Rubricを実際に使った評価ロジック」はまだ簡易でよい。Outerloop連携や weight/threshold の最適化は Phase4以降で扱う。

### 3-6. 検証観点（Phase3完了条件）

- `agent_goal_run` 実行後に:
  - `.agent/generated/rubrics/<task_id>.yaml` が生成され、`yq` / `jq -n 'input|...'` 等で構造を確認できる。
  - `.agent/state/rubric_history.json` に対応するエントリが追加されている。
  - `result.json.rubric_id` が生成した Rubric の ID と整合する（当面は固定でもよい）。

---

## 4. 実行順序と作業単位の提案

別セッションで実装する際は、次のような順序と作業単位で進めると安全。

1. Phase1:
   - Step1-1: `agent_goal_run.md` の input/output JSON を拡張（スケルトンのまま）。
   - Step1-2: `quickstart_goal_only.md` / `cli-implementation-design.md` の I/O 例を更新。
   - Step1-3: `agent_quickstart` / `agent_full_cycle` との互換性確認。
2. Phase2:
   - Step2-1: `agent_ao_run.md` を追加し、標準 artifacts を初期化する処理を実装。
   - Step2-2: `eval_perturb_suite.md` から AO 呼び出しを再利用するかどうかを検討（MVPでは重複可）。
   - Step2-3: Rubric の detector（`code_quality_v1.yaml`）が AO v0 の出力と整合しているかを確認。
3. Phase3:
   - Step3-1: `agent_ras_autogen.md` を追加し、rubric_autogen.defaults.yaml から Rubric v0 を生成。
   - Step3-2: `agent_goal_run.md` から RAS v0 と AO v0 を呼び出すようにフローを組み立て。
   - Step3-3: `rubric_history.json` のフォーマットと append ロジックを実装。

上記を一通り終えた時点で、

- 「Goal → Evaluator I/O v2 形式での評価入力/出力 → AOによる標準artifacts整備 → RASによるRubric生成」

という MVP 内ループが成立する。

---

## 5. 関連メモ / 参照

- ギャップ整理メモ:
  - `memory-bank/06-project/context/auto_refine_agents_impl_gap_2025-11-15.md`
- 正典:
  - `agent/registry/rubrics/code_quality_v1.yaml`
  - `agent/registry/config/rubric_autogen.defaults.yaml`
- CLIタスク:
  - `.cursor/commands/agent/agent_goal_run.md`
  - `.cursor/commands/agent/eval_perturb_suite.md`
  - `.cursor/commands/agent/agent_full_cycle.md`

