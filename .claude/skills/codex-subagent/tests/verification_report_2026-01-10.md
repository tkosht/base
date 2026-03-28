# codex-subagent 動作確認レポート

**実施日**: 2026-01-10
**環境**: codex-cli 0.79.0, Python 3.12

---

## 1. 基本モード動作確認

### 1.1 SINGLE モード
| 項目 | 結果 | 備考 |
|------|------|------|
| 基本実行 | PASS | 日時出力成功 |
| JSON出力 | PASS | success=true, returncode=0 |
| 評価スコア | PASS | combined_score=3.435 |
| ログ生成 | PASS | run-*.jsonl 生成確認 |

**テストコマンド**:
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only --timeout 60 --json \
  --prompt "現在の日時を表示してください。出力形式: YYYY-MM-DD HH:MM:SS"
```

### 1.2 PARALLEL モード
| 項目 | 結果 | 備考 |
|------|------|------|
| 並列実行 | PASS | 3件並列実行 |
| dedup マージ | PASS | 重複除去動作確認 |
| average_score | PASS | 3.3 |
| 部分タイムアウト | PASS | 1件タイムアウトでも他2件マージ |

**テストコマンド**:
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode parallel --count 3 --merge dedup --task-type analysis \
  --sandbox read-only --timeout 120 --json \
  --prompt "Pythonで最も人気のあるWebフレームワークを1つ挙げ、その理由を1文で述べてください。"
```

### 1.3 COMPETITION モード
| 項目 | 結果 | 備考 |
|------|------|------|
| 評価実行 | PASS | best_single 戦略 |
| combined_score | PASS | 3.465（0-5範囲）|
| scores オブジェクト | PASS | correctness, completeness, quality, efficiency |
| LLM評価 | PASS | 全項目5点 |
| 候補選択 | PASS | agent_1 選択 |

**テストコマンド**:
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition --count 3 --task-type code_review --strategy best_single \
  --sandbox read-only --timeout 180 --json \
  --prompt "以下のPythonコードのバグを指摘してください: def add(a, b): return a - b"
```

### 1.4 PIPELINE モード
| 項目 | 結果 | 備考 |
|------|------|------|
| pipeline_run_id | PASS | UUID形式 |
| stage_results | PASS | 3件（draft, critique, revise）|
| 全ステージ status | PASS | 全て "ok" |
| capsule 生成 | PASS | schema_version=1.1 |
| capsule_hash | PASS | SHA256 64文字 |
| 協調内容 | PASS | bool除外条件追加など改善提案反映 |

**テストコマンド**:
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-stages draft,critique,revise --capsule-store auto \
  --sandbox read-only --timeout 300 --json \
  --prompt "Pythonでフィボナッチ数列の第n項を計算する関数を設計してください。"
```

---

## 2. 補助ツール動作確認

### 2.1 codex_query.py
| 項目 | 結果 | 備考 |
|------|------|------|
| --list | PASS | テーブル形式表示 |
| --stats | PASS | 統計サマリー表示 |
| --mode フィルタ | PASS | 指定モードのみ |
| --export csv | PASS | CSV出力 |
| --export json | PASS | JSON出力 |

**実行例（--list）**:
```
Run ID     Timestamp                 Mode         Task            TO  Score    Human  LLM
------------------------------------------------------------------------------------------
c093de3d   2026-01-10T02:02:42.987   single       analysis        -   3.44     -      -
4692610c   2026-01-10T01:57:45.477   pipeline     code_gen        -   0.00     -      -
```

**実行例（--stats）**:
```
Total Runs: 57
By Mode: single: 34, pipeline: 16, parallel: 4, competition: 3
```

### 2.2 codex_feedback.py
| 項目 | 結果 | 備考 |
|------|------|------|
| --show | PASS | ログ概要表示（--scope auto 必須）|
| --score 追加 | PASS | Human Score 追加確認 |
| --run-id 指定 | PASS | 特定ログへのフィードバック |

**実行例（--show）**:
```
Run ID: 5592a678...
Mode: single
Heuristic Score: 3.435
Human Score: 4.0
```

---

## 3. エッジケース確認

### 3.1 タイムアウト処理
| 項目 | 結果 | 備考 |
|------|------|------|
| timed_out | PASS | true |
| success | PASS | false |
| error_message | PASS | "Timeout after 5s" |
| output_is_partial | PASS | true |
| ラッパー終了コード | PASS | 2（EXIT_SUBAGENT_FAILED）|

**注記**:
- **ラッパー終了コード**: `codex_exec.py` 自体の終了コード（0=成功, 2=サブエージェント失敗, 3=ラッパーエラー）
- **returncode**: ログ内の `results[].returncode` はサブプロセス（codex exec）の終了コード。タイムアウト時は 0 になることがある

### 3.2 オプション
| 項目 | 結果 | 備考 |
|------|------|------|
| --verbose | PASS | 時間・スコア・ログパス表示 |
| --no-log | PASS | ログファイル生成なし確認 |

---

## 4. 発見・修正されたバグ

### 4.1 heuristic null ハンドリング

**問題**: `evaluation.heuristic` が `null` のログで `AttributeError` 発生

**原因**: `dict.get(key, default)` はキーが存在し値が `None` の場合、`None` を返す（デフォルト値は使われない）

**影響ファイル**:
- `codex_query.py`: 131行目, 166行目
- `codex_feedback.py`: 147行目

**修正内容**:
```python
# Before
heuristic = eval_data.get("heuristic", {})

# After
heuristic = eval_data.get("heuristic") or {}
```

**影響ログ**: PIPELINE モードのログ16件（heuristic 評価なし）

---

## 5. 注意事項

1. **codex_feedback.py のデフォルト scope**: `human` がデフォルト。`auto/` 配下のログを参照するには `--scope auto` または `--scope all` が必要

2. **PARALLEL モードのタイムアウト**: 120秒では一部タイムアウトする可能性あり。複雑なタスクでは longer timeout を推奨

3. **PIPELINE モードの Heuristic Score**: 協調実行のため個別の heuristic 評価は行われない（N/A）

4. **ログに記録される内容**: ログファイル（`.jsonl`）には `prompt`, `mode`, `timeout`, `results` 等が記録されるが、実行コマンド列（`uv run python ...`）自体は記録されない。テストコマンドの検証はログ内容の照合で実施

5. **終了コードの区別**:
   - **ラッパー終了コード**: `codex_exec.py` の `sys.exit()` 値（0=成功, 2=サブエージェント失敗, 3=ラッパーエラー）
   - **returncode**: ログ内 `results[].returncode` はサブプロセス（codex exec）の終了コード

---

## 6. 推奨改善項目

1. ~~`codex_query.py` / `codex_feedback.py` の null ハンドリング修正~~ **完了**

2. `codex_feedback.py` のデフォルト scope を `all` に変更検討

3. ~~PIPELINE モード用の評価メトリクス追加検討（stage 成功率など）~~ → **--mode pipeline サポート追加で対応**

---

## 7. 追加修正（2026-01-10 追記）

### 7.1 --mode pipeline サポート追加

**問題**: `codex_query.py` の `--mode` オプションに `pipeline` が未サポート

**修正内容**:

1. **argparse choices**: `pipeline` を追加（374行目）
   ```python
   choices=["single", "parallel", "competition", "pipeline"]
   ```

2. **format_log_row**: pipeline モードの results 構造に対応（172-178行目）
   - 通常: `results[0].success`
   - pipeline: `results[0].exec.success`

**検証結果**:
| テスト | 結果 |
|--------|------|
| `--mode pipeline` フィルタ | PASS（16件表示）|
| 統計表示（By Mode） | PASS（pipeline: 16）|
| 回帰テスト single | PASS |
| 回帰テスト competition | PASS |

---

## 8. PIPELINE モード実践検証（2026-01-10 追記）

### 8.1 問題発生：タイムアウト

**タスク**: `app/sharepoint_list` の整合性チェック（ドキュメント⟷コード⟷テスト）

**初回実行**（失敗）:
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-stages draft,critique,revise \
  --timeout 360 --sandbox read-only --json \
  --prompt "app/sharepoint_list の整合性を分析してください。..."
```

| 項目 | 結果 |
|------|------|
| run_id | 95ff85ee |
| draft ステージ | タイムアウト（360秒） |
| status | retryable_error |
| 実行コマンド数 | exec=11, serena=1 |

**原因分析**:
- プロンプトが曖昧で、エージェントがファイルを1つずつ探索
- 360秒では draft ステージすら完了しない

### 8.2 解決策：プロンプト改善

**改善ポイント**:
1. **対象ファイルを明示** - 探索範囲を限定
2. **チェック項目を具体化** - 「整合性を分析」→「3点のみ評価」
3. **出力形式を指定** - YES/NO、根拠、ギャップの構造化

**改善後プロンプト**:
```
app/sharepoint_list の整合性チェック

## 対象ファイル（これらのみを対象とすること）
ドキュメント: app/sharepoint_list/README.md
コード: internal/validators.py, filters.py, operations.py
テスト: test_validators.py, test_filters.py, test_operations_select.py

## チェック項目（以下の3点のみを評価）
1. README の select_fields 仕様がコードとテストで一致しているか
2. README の filters 仕様がコードとテストで一致しているか
3. validators.py の list_url 検証ロジックがテストでカバーされているか

## 出力形式
各チェック項目について: 整合: YES/NO、根拠: ファイル名と行番号、ギャップ
```

### 8.3 再実行結果：成功

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-stages draft,critique,revise \
  --timeout 600 --sandbox read-only --json \
  --prompt "<改善後プロンプト>"
```

| 項目 | 結果 |
|------|------|
| run_id | cdf39514 |
| pipeline_run_id | 38cdb337-4c38-4153-8941-ffe7ec97c5a5 |
| success | true |
| 全ステージ status | ok |

**実行時間**:
| ステージ | 時間 |
|----------|------|
| draft | 254.8秒 |
| critique | 224.4秒 |
| revise | 264.6秒 |
| **合計** | **743.8秒** |

### 8.4 整合性チェック結果

| # | チェック項目 | 整合 | ギャップ |
|---|-------------|------|----------|
| 1 | select_fields 仕様 | YES | なし |
| 2 | filters 仕様 | YES | なし |
| 3 | list_url 検証テスト | **NO** | `test_validators.py` に `parse_list_url` の直接テストがない |

**具体的な根拠**（revise ステージ出力より）:
- チェック1: README:31-35 ↔ operations.py:346-421 ↔ test_operations_select.py:62,72,530,591
- チェック2: README:38-47 ↔ filters.py:7,70-97 ↔ test_filters.py:8,30,73,91
- チェック3: validators.py:35-64 に `parse_list_url` 定義あり、test_validators.py にテストなし

### 8.5 教訓

| 項目 | 学び |
|------|------|
| プロンプト設計 | 曖昧な指示は探索時間を浪費する。対象とチェック項目を具体的に |
| タイムアウト設定 | 複雑なタスクは各ステージ250秒以上必要。600秒推奨 |
| PIPELINE の強み | draft→critique→revise で行番号の修正など品質向上が見られた |
