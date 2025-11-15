# agent_full_cycle シミュレーションと改善メモ（2025-11-15）

## 概要

- 対象: `.cursor/commands/agent/agent_full_cycle.md`（Goal-only → 摂動 → A/B → Gate → PR）のフルサイクル
- ゴール: auto-refine-agents の設計意図（評価ガバナンス / Gate MUST / 三層分離）に沿っているかを、実行ログベースで確認し、問題点を洗い出す。
- 実行環境: Codex CLI / bash, `jq`, `rg`, `sqlite3` 利用

## 実行シナリオ

### シナリオ1: MAX_ITERS=0（outerloop 無効）

- コマンド:
  - `rm -rf .agent`
  - `export GOAL="agent_full_cycle評価用チェックリスト作成 (MAX_ITERS0)"`
  - `MAX_ITERS=0 awk ... agent_full_cycle.md | bash`
- 観測:
  - `.agent/logs/eval/input.json` の `goal` が上記 GOAL になっている（後述修正後の確認）。
  - `eval_perturb_suite` がスタブ的に `ok:true` で通過。
  - A/B / promote / PR は実行されるが、`MAX_ITERS=0` 判定はループ条件でなく Gate 条件側で扱うべきという論点が残る。

### シナリオ2: MAX_ITERS=1, AB_MIN_N=999（Gate MUST 不合格）

- コマンド:
  - `rm -rf .agent`
  - `export GOAL="agent_full_cycle評価用チェックリスト作成 (GateFail2)"`
  - `export AB_MIN_N=999`
  - `export MAX_ITERS=1`
  - `awk ... agent_full_cycle.md | bash`
- 観測（改善後）:
  - `outerloop_promote` ログ:
    - `NG: AB反復不足 (min_n=5 < 999)`
  - `agent_full_cycle` ログ:
    - `NG: promotion gate not satisfied within MAX_ITERS=1`
  - パイプライン終了コード: `1`
  - `.agent/logs/eval/input.json` の `goal` は `"agent_full_cycle評価用チェックリスト作成 (GateFail2)"`。

## 発見した主な課題と対応（今回実装したもの）

### 1. GOAL が外側から伝搬せず、ログ再現性が低い

- 課題:
  - `agent_goal_run.md` 内で `GOAL="あなたのGoal"` と再代入しており、外の `export GOAL=...` が反映されない。
- 対応:
  - `.claude/commands/agent/agent_goal_run.md` を修正:
    - `GOAL="${GOAL:-あなたのGoal}"` に変更。
  - 結果:
    - 上記シナリオ2で `.agent/logs/eval/input.json` の `goal` に環境変数 GOAL が正しく記録されることを確認。

### 2. Rubric 未生成時に agent_templates_push_pr が失敗する

- 課題:
  - RAS 未実装で `.agent/generated/rubrics/*.yaml` が存在しない状態でも、
    `agent_templates_push_pr.md` が無条件に `cp .agent/generated/rubrics/*.yaml ...` を実行し、`cp: cannot stat` で失敗していた。
- 対応:
  - `.claude/commands/agent/agent_templates_push_pr.md` を修正:
    - `nullglob` + 配列展開で Rubric ファイル有無を判定。
    - 0件の場合は
      - `INFO: .agent/generated/rubrics に昇格対象Rubricが無いため、今回のPR昇格はスキップします。`
      - を出力して **正常終了** するように変更。
  - 結果:
    - Rubric 未生成でも `agent_full_cycle` 全体がエラーで止まらず、MVP スケルトン段階でもフルルートを回せるようになった。

### 3. Gate MUST 不合格時でも agent_full_cycle の終了コードが 0 になる

- 課題:
  - `outerloop_promote` の Gate MUST（例: `AB_MIN_N` 未達）で `exit 1` しても、
    `agent_full_cycle.md` 全体の終了コードは 0 のままで、自動化から合否を判別できない。
- 対応:
  - `.claude/commands/agent/agent_full_cycle.md` を修正:
    - ループ前に `PROMOTE_OK=0` を導入。
    - `outerloop_promote` が成功したときだけ `PROMOTE_OK=1` に設定し、`agent_templates_push_pr` を呼ぶ。
    - ループ終了後に
      - `if [ "$MAX_ITERS" -gt 0 ] && [ "$PROMOTE_OK" -ne 1 ]; then exit 1; fi`
      - で Gate 未達を明示的にエラーとして伝播。
  - 結果:
    - シナリオ2で `EXIT_CODE=1` となり、Gate MUST 不合格を上位から検出可能に。
    - `MAX_ITERS=0` の場合は Gate チェックをスキップし、終了コード 0 を維持。

## 今後の改善候補（未実装）

- Evaluator I/O を `evaluation-governance.md` の JSON 仕様により近づける（`task_id` / `rubric` / `artifacts` / `evidence` / `metrics` の追加）。
- outerloop の skeleton モード時は「PROMOTE OK」を出さず、昇格スキップを明示的にログに残すようにする。
- `agent_full_cycle` の最後に knowledge_recorder タスクを呼び出し、今回のような実行メモを自動で `memory-bank/` に送り込むフローを検討。

## 関連ファイル

- コマンド:
  - `.cursor/commands/agent/agent_full_cycle.md`
  - `.cursor/commands/agent/agent_goal_run.md`
  - `.cursor/commands/agent/agent_templates_push_pr.md`
  - `.cursor/commands/agent/outerloop_abtest.md`
  - `.cursor/commands/agent/outerloop_promote.md`
- ドキュメント:
  - `docs/auto-refine-agents/quickstart_goal_only.md`
  - `docs/auto-refine-agents/evaluation-governance.md`
  - `docs/auto-refine-agents/architecture_summary.md`

