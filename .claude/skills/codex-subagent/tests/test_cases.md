# codex-subagent テストケース定義

回帰テスト・動作確認用のテストケース集

---

## Quick Smoke Test

最小限の動作確認（約2分）

```bash
# SINGLE モード基本動作
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only --timeout 60 --json \
  --prompt "1+1の答えを数字のみで出力してください"
```

**期待結果**: `success: true`, `output` に "2" を含む

---

## 全モードテスト

### TC-001: SINGLE モード
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only --timeout 60 --json \
  --prompt "現在の日時を表示してください。出力形式: YYYY-MM-DD HH:MM:SS"
```
**期待結果**:
- `success: true`
- `returncode: 0`
- `output`: 日時文字列
- `evaluation.heuristic.combined_score`: 3.0-5.0 範囲

### TC-002: PARALLEL モード（dedup）
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode parallel --count 2 --merge dedup --task-type analysis \
  --sandbox read-only --timeout 120 --json \
  --prompt "Pythonで最も人気のあるWebフレームワークを1つ挙げてください"
```
**期待結果**:
- `results` 配列: 2件
- `merged_output`: 空でない
- `evaluation.average_score`: 存在

### TC-003: COMPETITION モード
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition --count 2 --task-type code_review --strategy best_single \
  --sandbox read-only --timeout 180 --json \
  --prompt "以下のPythonコードのバグを指摘: def add(a, b): return a - b"
```
**期待結果**:
- `agent_id`: 選択された1件
- `combined_score`: 0-5 範囲
- `scores`: correctness, completeness, quality, efficiency 含む

### TC-004: PIPELINE モード
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-stages draft,critique --capsule-store auto \
  --sandbox read-only --timeout 240 --json \
  --prompt "Hello World を出力するPython関数を設計してください"
```
**期待結果**:
- `pipeline_run_id`: UUID形式
- `success: true`
- `stage_results`: 2件、全て `status: "ok"`
- `capsule.schema_version`: "1.1"

---

## エッジケーステスト

### TC-010: タイムアウト処理
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only --timeout 3 --json \
  --prompt "非常に長い計算を実行してください"
```
**期待結果**:
- `timed_out: true`
- `success: false`
- `error_message`: "Timeout after 3s"
- 終了コード: 2

### TC-011: --no-log オプション
```bash
# 実行前のログファイル数を記録
before=$(ls .codex/sessions/codex_exec/auto/$(date +%Y/%m/%d)/*.jsonl 2>/dev/null | wc -l)

uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only --timeout 60 --no-log --json \
  --prompt "テスト"

# 実行後のログファイル数を確認
after=$(ls .codex/sessions/codex_exec/auto/$(date +%Y/%m/%d)/*.jsonl 2>/dev/null | wc -l)
[ "$before" = "$after" ] && echo "PASS" || echo "FAIL"
```

---

## 補助ツールテスト

### TC-020: codex_query.py --list
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_query.py --list --limit 5
```
**期待結果**: テーブル形式、5件以下表示

### TC-021: codex_query.py --stats
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_query.py --stats
```
**期待結果**: Total Runs, Average Score 表示

### TC-022: codex_feedback.py --show
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_feedback.py --scope auto --show
```
**期待結果**: Run ID, Timestamp, Mode, Prompt 表示

---

## null ハンドリング確認

### TC-030: PIPELINE ログの検索
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_query.py --list --mode pipeline --limit 5
```
**期待結果**: エラーなく PIPELINE ログ表示（Score は 0.00）

### TC-031: PIPELINE ログのフィードバック表示
```bash
# pipeline モードの run_id を取得して表示
uv run python .claude/skills/codex-subagent/scripts/codex_feedback.py --scope auto \
  --run-id $(uv run python .claude/skills/codex-subagent/scripts/codex_query.py \
    --list --mode pipeline --limit 1 2>/dev/null | tail -1 | awk '{print $1}') --show
```
**期待結果**: `Heuristic Score: N/A` 表示（エラーなし）
