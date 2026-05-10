---
name: codex-subagent
description: "Auto-trigger when the user asks to run a Codex exec subagent (single/parallel/competition) for code generation, review, analysis, or documentation, or when adjusting codex-subagent wrapper policy (logging/TTY/timeout/profile guardrails)."
allowed-tools:
  - Bash(codex:*)
  - Bash(uv run python:*)
  - Bash(timeout:*)
  - Read
  - Write
  - Glob
metadata:
  version: 0.4.0
  owner: codex
  maturity: draft
  tags: [skill, codex, subagent, codex-exec, orchestrator]
---

## Overview
codex-subagent は `codex exec` を「サブエージェント」として複数回実行し、結果を選別/統合/協調するための実行オーケストレーターです。

- 実体: `.agents/skills/codex-subagent/scripts/codex_exec.py`（実行）、`codex_query.py`（ログ検索）、`codex_feedback.py`（人間評価）
- 既定サンドボックス: `read-only`（安全・再現性優先）
- ログ: `.codex/sessions/codex_exec/{human|auto}/YYYY/MM/DD/run-*.jsonl`（TTY で自動分類）
- v2 pipeline: `schema_version: "2.0"` の spec、checkpoint state、`--resume-run`、`depends_on` DAG、stage ごとの `role` / `write_roots` / `max_attempts` に対応
- manager-leaf team: `team_policy: "manager_leaf_v1"` を指定すると DAG と `node_kind: "manager" | "leaf"` が必須になり、manager node は read-only / no-write / non-executor に制限される

## Quick Start
```bash
# SINGLE: 1回実行（小さく速い）
uv run python .agents/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only \
  --model gpt-5.3-codex --prompt "$PROMPT"

# PARALLEL: N回実行→マージ（情報収集・列挙）
uv run python .agents/skills/codex-subagent/scripts/codex_exec.py \
  --mode parallel --count 3 --merge dedup --task-type analysis \
  --sandbox read-only --json --prompt "$PROMPT"

# COMPETITION: N回実行→評価→最良選択（品質重視）
uv run python .agents/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition --count 3 --task-type code_review --strategy best_single \
  --judge-mode hybrid \
  --sandbox read-only --json --prompt "$PROMPT"

# PIPELINE v2: spec 駆動 / checkpoint / branch-join
uv run python .agents/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-spec "$SPEC" --max-parallel-stages 2 \
  --capsule-store auto --sandbox read-only --json --prompt "$PROMPT"

# Resume from checkpoint
uv run python .agents/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --resume-run .codex/sessions/codex_exec/human/artifacts/<run-id>/state.json \
  --json --prompt "$PROMPT"
```

## Execution Modes
- `single`: 1回だけ `codex exec` を実行し、そのまま出力。
- `parallel`: 同一プロンプトを `--count N` 回並列実行し、`--merge` で統合。
- `competition`: 同一プロンプトを `--count N` 回実行し、`--task-type` と `--strategy` で候補を絞り、`--judge-mode hybrid` なら pairwise judge で最終選定する。
- `pipeline`: `schema_version: "2.0"` の spec を受け取り、checkpoint/resume、stage ごとの権限、`depends_on` DAG、legacy linear pipeline を扱う。

代表的なパラメータ:
- `--task-type`: `code_gen|code_review|analysis|documentation`
- `--model`: `codex exec --model` に渡すモデル名（例: `gpt-5.3-codex-spark`）
- `--merge`: `concat|dedup|priority|consensus`（parallel）
- `--strategy`: `best_single|voting|hybrid|conservative`（competition）
- `--judge-mode`: `heuristic|hybrid`（competition）
- `--resume-run`: `state.json` または `run_id`
- `--max-parallel-stages`: graph pipeline の同時実行上限

## Context Engineering
- プロンプトは「1タスク=1プロンプト」を原則とし、出力形式（箇条書き/JSON/ファイル一覧など）を明示。
- 事実ベースで記述し、根拠はファイルパス・ログ・コマンドのいずれかで示す（根拠が出せない内容は「不明」）。
- `--profile fast/very-fast` は既定で使わない。使う場合はタスクを極小化し、推測を禁止する前置きを含める（`codex_exec.py` が警告とガードレールを注入）。

## 運用ノウハウ（実践から得た学び）

### タスク設計
- 大きいタスクは分割し、`--mode single` で短い実行を複数回回すほうが安定（例: docs↔code / tests↔code / docs↔tests を別々に評価）。
- ただし **single は既定でフィードバックループ（draft→critique→revise）を自動で回さない**。必要なら以下のどちらかで補う:
  - **multi‑single**: DRAFTのみ→CRITIQUEのみ→REVISEのみの3回実行で擬似ループを構成。
  - **pipeline**: 後述の JSON 形式と capsule 制約を満たす前提で使用（失敗時は single に切替）。
- 親エージェント側で「ファイルパス＋行番号のエビデンス」を抽出し、サブエージェントには「コマンド実行禁止・エビデンスのみ」を渡すとタイムアウトと逸脱が減る。
- `competition`/`pipeline` は重くなりやすい。広範囲レビューは single + 段階分割が最短。

### プロンプト設計（成功率向上の鍵）

**失敗パターン**（タイムアウト）:
```
repo 全体の整合性を分析してください。
対象: いろいろ
```
→ エージェントがファイルを1つずつ探索してタイムアウト

**成功パターン**:
```
## 対象ファイル（これらのみを対象とすること）
- AGENTS.md
- docs/architecture/knowledge-architecture.md
- docs/architecture/base-harness-set.md
- docs/architecture/base-harness-set.toml
- tests/test_base_harness_set.py

## チェック項目（以下の3点のみを評価）
1. AGENTS の参照先が知識配置と一致しているか
2. retain / exclude の説明が summary と manifest で一致しているか
3. 検証テストが keep-set を正しく表現しているか

## 出力形式
各チェック項目: 整合: YES/NO、根拠: ファイル名と行番号、ギャップ
```

**ポイント**:
1. **対象ファイルを明示**（「これらのみ」で範囲限定）
2. **チェック項目を具体化**（曖昧な「分析」を避ける）
3. **出力形式を指定**（構造化で品質向上、収束が速い）

### 推奨プロンプト例（multi‑single / pipeline）

**multi‑single（DRAFTのみ）**
```
DRAFTのみ。仕様を1文で要約。
制約: 推測禁止。不明は「不明」。
```

**multi‑single（CRITIQUEのみ）**
```
CRITIQUEのみ。DRAFTの問題点を2つ。理由を1文ずつ。
入力DRAFT: <ここに前段出力>
```

**multi‑single（REVISEのみ）**
```
REVISEのみ。DRAFTとCRITIQUEを踏まえて1文で改善。
入力DRAFT: <ここに前段出力>
入力CRITIQUE: <ここに前段出力>
```

**pipeline（JSON stage_result）**
```
Return JSON ONLY. capsule_patch で /draft を object で更新すること。
例:
{
  "schema_version": "1.1",
  "stage_id": "draft",
  "status": "ok",
  "output_is_partial": false,
  "capsule_patch": [
    {"op":"replace","path":"/draft","value":{"summary":"...","details":["..."]}}
  ]
}
```

**pipeline（JSON: critique / revise 例）**
```
{
  "schema_version": "1.1",
  "stage_id": "critique",
  "status": "ok",
  "output_is_partial": false,
  "capsule_patch": [
    {"op":"replace","path":"/critique","value":{"summary":"...","issues":["...","..."]}}
  ]
}
```
```
{
  "schema_version": "1.1",
  "stage_id": "revise",
  "status": "ok",
  "output_is_partial": false,
  "capsule_patch": [
    {"op":"replace","path":"/revise","value":{"summary":"...","changes":["..."]}}
  ]
}
```

### PIPELINE モードの活用
- draft→critique→revise で品質向上（critique で行番号修正、根拠追加など）
- 構造化された出力形式を指定すると効果的
- 複雑なタスクは 600 秒タイムアウト推奨
- 新規 spec は `schema_version: "2.0"` を明示し、必要なら `depends_on` で branch/join を表現する
- `role`, `write_roots`, `max_attempts`, `input_keys` を stage ごとに明示すると、review / verify / reducer の逸脱を抑えやすい
- graph で writer stage を使う場合は `write_roots` を明示する。parallel branch は isolated workspace 上で走り、同じファイルを変更した branch は conflict failure になる
- harness-autoptimizer など manager-leaf team が必要な実行では `team_policy: "manager_leaf_v1"` を指定し、manager node は分解・割当・進行管理・sanitized result 集約だけを行う。repair / review / verify などの実作業は leaf node に割り当てる
- pipeline mode の `workdir` は repo 内だけを許可し、absolute path でも isolated workspace 配下へ remap される。repo 外 path は拒否される
- 失敗後は checkpoint state から `--resume-run` で再開できる
- `--resume-run <run_id>` は現在の `--log-dir` / `--log-scope` 配下を優先し、見つからない場合だけ default log root を探索する
- **注意**: pipeline は各ステージが **JSON の stage_result** を返し、**capsule の `draft/critique/revise` は object 型**でなければならない。文字列で上書きするとスキーマ違反で失敗する。
- 例（patch で object を更新）:
  - `{"op":"replace","path":"/critique","value":{"summary":"...","issues":["..."]}}`
- `--pipeline-stages` は legacy shorthand として維持するが、新規 pipeline は `--pipeline-spec` を優先する

### プロファイル・タイムアウト
- `--profile very-fast` は gpt-5.2-codex で reasoning effort `minimal` が未対応となり 400 エラーが発生した（2026-01-10 の実行ログで確認）。このモデルでは避けるか、必要なら `--profile fast` を小タスクで事前検証する。
- タイムアウト時は `--json` 出力の `timed_out=true` / `output_is_partial=true` を確認し、結果を採用せずプロンプト縮小で再実行する。

## Result Handling
- `codex_exec.py --json` ではモードごとに JSON を返す（例: `single` は `{output, stderr, success, returncode, timed_out, timeout_seconds, output_is_partial, error_message, evaluation...}`）。
- タイムアウト時は `success=false` / `timed_out=true` / `error_message="Timeout after <N>s"` となる。`output`/`stderr` は取得できた範囲で保持され、`output_is_partial=true` として扱う（`.agents/skills/codex-subagent/scripts/codex_exec.py` はプロセスグループを終了して残留を回避）。
- `codex exec` が非0終了した場合は stdout は保持され、stderr は `stderr` に入り、`error_message` にも反映される（`--json` で確認）。
- `competition` のログは候補全件を保存し、`selected=true` の1件が最終採用案（デバッグ/再現性のため）。
- `competition` は `selection` に heuristic winner と pairwise judge の根拠を残す。
- `pipeline` の JSON 出力は `{pipeline_run_id, success, stage_results, capsule, capsule_hash, capsule_store, capsule_path, evaluation}` を返す。
- `evaluation.retry_policy_followed` は stage log の attempt 記録から導出され、証拠が足りない場合は `false` になる。
- pipeline stage log には `role`, `attempt`, `write_roots`, `changed_files`, `unauthorized_files`, `checkpoint state` に必要な情報が残る。
- **終了コードの区別**:
  - **ラッパー終了コード**（`codex_exec.py` の `sys.exit()` 値）: `0=全成功`, `2=サブエージェント失敗`, `3=ラッパー内部エラー`
  - **returncode**（`results[].returncode`）: サブプロセス（codex exec）の終了コード。タイムアウト時は `0` になることがある
  - `parallel` は候補のいずれかが失敗した時点でラッパー終了コード `2`
- ログ保存時は `prompt` と `output` を一定長でトランケートする（ログ肥大化回避）。本体の stdout はトランケートしない。

## Timeout Guidance
- 既定 `--timeout` は 360 秒。
- **PIPELINE モードは 600 秒推奨**（各ステージ約250秒必要、合計700秒以上かかることもある）。
- read_file などツール使用が多い場合は 360 秒以上を明示する。
- 外側の `timeout_ms` は `--timeout` より大きく設定する（外側タイムアウトで run-*.jsonl が残らないことを確認済み）。

**実測データ（2026-01-10）**:
| ステージ | 時間 |
|----------|------|
| draft | 254.8秒 |
| critique | 224.4秒 |
| revise | 264.6秒 |
| **合計** | **743.8秒** |

## Auxiliary Tools（補助ツール）

### codex_query.py（ログ検索・分析）
```bash
# 最新10件をリスト
uv run python .agents/skills/codex-subagent/scripts/codex_query.py --list --limit 10

# 統計サマリー
uv run python .agents/skills/codex-subagent/scripts/codex_query.py --stats

# モードでフィルタ
uv run python .agents/skills/codex-subagent/scripts/codex_query.py --list --mode pipeline
```

**注意点**:
- `--mode pipeline` でフィルタ可能
- pipeline モードは heuristic 評価なし（Score は 0.00 表示）
- `--scope auto|human|all` でログディレクトリを選択

### codex_feedback.py（人間フィードバック）
```bash
# ログ概要表示（auto/ 配下）
uv run python .agents/skills/codex-subagent/scripts/codex_feedback.py --scope auto --show

# スコア追加
uv run python .agents/skills/codex-subagent/scripts/codex_feedback.py --scope auto --score 4.5 --notes "Good"
```

**注意点**:
- デフォルト scope は `human`
- auto/ 配下のログ参照は `--scope auto` または `--scope all` 必要
- インタラクティブモード: `--interactive`

## Guardrails
- 機密情報や認証情報を扱わない
- 破壊的コマンドは避ける
- 既定は `--sandbox read-only`（書き込みが必要な場合は親エージェント側で実施）
- ログ分類は既定で自動（TTY 判定）。必要なら `--log-scope human|auto` で上書きする
- 指示と矛盾/不明点がある場合は、最小の確認質問で先に潰す
- pipeline JSON 逸脱防止: `references/pipeline_json_guardrails.md` を必読
- 安定テンプレ: `references/pipeline_prompt_guarded_template.md` と `references/pipeline_spec_guarded_min.json` を優先
- 動的ステージ運用: `references/pipeline_dynamic_stage_rules.md` と `references/pipeline_prompt_dynamic_template.md` と `references/pipeline_spec_dynamic_safe.json`
- 動的ステージのテスト実行: `references/pipeline_dynamic_test_run_template.md`

---

*Updated on 2026-01-10: Added prompt design best practices, PIPELINE timeout guidance (600s recommended), auxiliary tools section, and exit code clarification based on practical verification.*
