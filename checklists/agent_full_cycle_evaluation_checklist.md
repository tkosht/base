# agent_full_cycle フルサイクル評価チェックリスト（auto-refine-agents）

本ドキュメントは `.cursor/commands/agent/agent_full_cycle.md` が auto-refine-agents の設計意図に沿って動作しているかを、手動テストで検証するためのチェックリストです。

## 目的 / 範囲

- 目的:
  - Goal のみを入力として Inner-Loop を起動し、摂動ロバスト性スイート → テンプレ A/B 比較 → 昇格判定 → PR 用エビデンス収集までの「改善プロセスループ」が通しで実行できることを確認する。
- 範囲:
  - `.cursor/commands/agent/agent_goal_run.md`
  - `.cursor/commands/agent/eval_perturb_suite.md`
  - `.cursor/commands/agent/outerloop_abtest.md`
  - `.cursor/commands/agent/outerloop_promote.md`
  - `.cursor/commands/agent/agent_templates_push_pr.md`
- 対象スコープ:
  - MVP スケルトン実装（Evaluator I/O v2 の仮実装）での動作確認
  - RAS/AO 実装完了後に有効となる追加ゲート（将来用）を先に定義しておく

## 前提 / 環境

- CLI ツール:
  - `bash`, `awk`, `sed`, `jq`, `rg`, `sqlite3`（必須）
  - `yq`（あれば Gate 関連の設定優先順位を確認可能）
- 作業ブランチ:
  - `feature/agent-full-cycle-eval` など、`main/master` 以外で実施する。
- ディレクトリ:
  - リポジトリルートで実行する（`docs/auto-refine-agents/**` と `.cursor/commands/agent/**` が存在すること）。
- ランタイム状態:
  - `.agent/` が既に存在する場合は、バックアップしてから開始するか、専用 worktree を用意する。

## 不変条件（評価中に必ず守る）

- `.agent/` は現在の worktree 専用とし、他の worktree から共有しない。
- `agent/registry/**` への変更は常に Git でトラッキングし、PR ベースで昇格する。
- 評価ログとエビデンス（`.agent/logs/**`, `.agent/generated/**`）を削除する前に必要な情報を記録する。
- Integration/E2E レベルでモックを挟まず、実際の CLI コマンドで評価する。

## シナリオ一覧

- [ ] シナリオ A: Goal-only + 摂動スモークテスト（`MAX_ITERS=0`）
- [ ] シナリオ B: A/B 集計 + Gate MUST（outerloop の単体確認）
- [ ] シナリオ C: フルサイクル（outerloop + PR 昇格）※RAS/AO 実装後

---

## シナリオ A: Goal-only + 摂動スモークテスト（MAX_ITERS=0）

MVP スケルトンとして、Inner-Loop 最短経路 + 摂動スイートまでがエラーなく通ることを確認する。

### 実施項目

- [ ] 作業ブランチ `feature/agent-full-cycle-eval` を作成しチェックアウトする。
- [ ] 依存ツールの存在確認  
      `jq --version`, `rg --version`, `sqlite3 --version` を実行してバイナリがあることを確認する。
- [ ] `.agent/` が存在する場合は、`mv .agent .agent.bak_YYYYMMDD-HHMM` などで退避する。
- [ ] 任意のテスト用 Goal を決めて環境変数に設定する。  
      例: `export GOAL="agent_full_cycle のE2E動作確認"`
- [ ] outerloop を無効化した状態で `agent_full_cycle` を実行する。
  ```bash
  export MAX_ITERS=0
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' \
    ./.cursor/commands/agent/agent_full_cycle.md | bash
  ```

### 受け入れ基準

- [ ] コマンドが非ゼロ終了コードを返さず完了する。
- [ ] `.agent/` 配下に以下のディレクトリが生成されている。  
      `state/`, `generated/{rubrics,artifacts}`, `memory/{episodic,semantic/documents,playbooks}`, `prompts/{planner,executor,evaluator,analyzer}`, `config/`, `logs/`
- [ ] `.agent/logs/eval/input.json` が存在し、`jq -r '.goal'` の結果が設定した `GOAL` と一致する。
- [ ] `.agent/logs/eval/result.json` が存在し、`jq '.ok'` の結果が `true` になっている（スケルトン評価）。
- [ ] `.agent/logs/eval/perturb.json` が存在し、`jq '.ok'` の結果が `true` になっている。  
      `tests/perturbation_suite.sh` が存在しない場合でも、スタブとして `ok:true` が記録されている。
- [ ] `.agent/logs/eval/ab/` は存在しないか空である（`MAX_ITERS=0` により outerloop が実行されていない）。

### ロールバック / 後処理

- [ ] `.agent/` の内容を簡潔にレビューし、必要に応じて `pr_evidence/` などに抜粋を保存する。
- [ ] `.agent/` を残すか、`rm -rf .agent` でクリーンアップするかを決定する（次シナリオで再利用する場合は残す）。

---

## シナリオ B: A/B 集計 + Gate MUST（outerloop の単体確認）

outerloop の A/B 集計と昇格判定ロジックが、`docs/auto-refine-agents/evaluation-governance.md` の Gate MUST と整合しているかを確認する。`agent_full_cycle` から切り離して、`.cursor/commands/agent/outerloop_abtest.md` と `.cursor/commands/agent/outerloop_promote.md` を直接呼び出す。

### 実施項目

- [ ] シナリオ A と同様の ACE 初期化状態（`.agent/**`）を用意するか、必要に応じて再度 `agent_goal_run.md` を実行する。
- [ ] 評価対象テンプレート ID を環境変数 `TEMPLATES` で明示する。  
      例: `export TEMPLATES="planner.default.v1 planner.candidate.v2"`
- [ ] `AB_N` を小さめの値（例: 3）に設定して A/B テストを実行する。
  ```bash
  export AB_N=3
  export GOAL="${GOAL:-outerloop smoke}"
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' \
      ./.cursor/commands/agent/outerloop_abtest.md | bash
  ```
- [ ] `.agent/logs/eval/ab/summary_raw.jsonl` と `.agent/logs/eval/ab/summary.json` が生成されていることを確認する。
- [ ] Gate 関連のしきい値を環境変数または `.agent/config/loop_config.yaml` で設定する。  
      例: `AB_MIN_N=3`, `MIN_DELTA=0.0`, `MAX_COST=`（未設定）。
- [ ] 昇格判定を実行する。
  ```bash
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' \
    ./.cursor/commands/agent/outerloop_promote.md | bash
  ```

### 受け入れ基準

- [ ] `.agent/logs/eval/ab/summary.json` の各エントリに `id`, `n`, `s_avg`, `c_avg` が含まれている。
- [ ] `jq 'map(.n) | min' .agent/logs/eval/ab/summary.json` の結果が `AB_MIN_N` 以上になっている。
- [ ] `.agent/logs/eval/perturb.json` の `ok` が `true` でない場合、`outerloop_promote` が非ゼロ終了コードで終了し、「perturbation suite failed」のメッセージが出力される。
- [ ] `MIN_DELTA` を `0.0` にした場合、スケルトン評価（全ての `s_avg` が 1.0）でも Gate MUST を通過し、`.agent/state/current_template_id` が生成される。
- [ ] `MIN_DELTA` を `0.02` などに変更し、`summary.json` を適宜編集してスコア差を小さくした場合、Gate MUST が NG となり終了コードが非ゼロになる。

### ロールバック / 後処理

- [ ] `current_template_id` に書き込まれたテンプレート ID を確認し、昇格候補として妥当かをメモに残す。
- [ ] 必要に応じて `.agent/logs/eval/ab/**` を `pr_evidence/` などにコピーする。

---

## シナリオ C: フルサイクル（outerloop + PR 昇格）

RAS/AO が実装され、`.agent/generated/rubrics/*.yaml` が自動生成される状態を前提とした将来用シナリオ。`agent_full_cycle` 一発で Goal → 摂動スイート → A/B → Gate MUST → `agent/registry/**` への昇格PR用差分が揃うことを確認する。

### 実施項目（設計）

- [ ] `.agent/generated/rubrics/*.yaml` が最低 1 件以上生成されるタスク（Inner-Loop 完了形）を用意する。
- [ ] `agent/registry/rubrics/` に既存の正典 Rubric が存在するか確認し、必要に応じて初期ファイルを作成する。
- [ ] `MAX_ITERS`（例: 2）と Gate 関連しきい値を `loop_config.yaml` か環境変数で設定する。
- [ ] `agent_full_cycle` を `MAX_ITERS>=1` で実行する。
- [ ] 実行後、`agent/registry/rubrics/` 差分が存在し、`git status` で昇格候補が見えることを確認する。
- [ ] `agent_templates_push_pr.md` の手順に従い、昇格 Rubric を含む PR を作成する。

### 受け入れ基準（将来の完了条件）

- [ ] `agent_full_cycle` 実行が非ゼロ終了コードで止まることなく完了する。
- [ ] `.agent/logs/**` と `.agent/generated/**` から Gate MUST を満たす監査エビデンスが収集できる。
- [ ] `agent/registry/rubrics/` の差分が、`.agent/generated/rubrics/*.yaml` と対応している。
- [ ] PR 説明文に、`evaluation-governance.md` の Gate MUST 項目（spec/robustness/cost/ホールドアウト/HITL）が網羅されている。

---

## メモ / リンク

- 設計背景: `docs/auto-refine-agents/quickstart_goal_only.md`, `docs/auto-refine-agents/evaluation-governance.md`, `docs/auto-refine-agents/architecture_summary.md`
- ランタイム/正典/意思決定の分離: `memory-bank/06-project/context/system_patterns.md`
- コマンド本体: `.cursor/commands/agent/agent_full_cycle.md` 他
