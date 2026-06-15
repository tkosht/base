---
name: tmux-agent-review-loop
description: "Use when reviewing work performed by another agent running in a tmux pane, handing off review findings through files, monitoring the pane, requesting fixes, and repeating review/fix/verify cycles until convergence or a user decision is required."
allowed-tools:
  - Bash(tmux:*)
  - Bash(git:*)
  - Bash(make:*)
  - Bash(uv run python:*)
  - Bash(uv run pytest:*)
  - Read
  - Write
  - Glob
metadata:
  version: 0.1.0
  owner: codex
  maturity: draft
  tags: [skill, tmux, review-loop, handoff, agent-collaboration]
---

# Tmux Agent Review Loop

## Purpose

tmux pane 上の別 agent が実施した作業を、親 agent が reviewer / coordinator としてレビューし、レビュー結果をファイル連携し、修正・検証・再レビューを収束まで回す。
ユーザーが進捗を監視するための既存 interactive Codex pane は実行者との対話面として保護し、親 reviewer が非対話 worker や `codex exec` の実行場所へ置き換えない。

## Use When

- ユーザーが「tmux pane にレビュー結果を連携」「pane 側の実装をレビュー」「修正後に再レビュー」「収束するまで回して」と依頼したとき。
- PR ではなく、同じ workspace 上の別 agent / Cursor / Codex pane が実装者になっているとき。
- 長文 paste が途中で切れる、または pane の入力状態確認が必要なとき。

## Required Output

- `target_pane`: 連携先 pane id、確認した状態、pane role。
- `review_artifact`: レビュー結果ファイルの path。
- `findings`: implementable / needs_user_decision / resolved / non_issue の分類。
- `prior_findings_closure`: `Prior Findings Closure Table` による前 round / 既知 finding の閉鎖状況。
- `failure_hypotheses`: `Failure Hypothesis Table` による高リスク仮説、確認 source refs、negative evidence。
- `handoff`: 送信前確認、入力クリア要否、送信コマンド、送信後確認、subagent / worker が必要な場合の実行者への依頼内容。
- `loop_state`: round、converged、stop_reason。
- `verification`: 実行または確認した gate、`git status`、残リスク。
- `nonconverged_stop_reasons`: target pane 未確定は `target_pane_unresolved`、handoff 未確認は `handoff_unconfirmed`、親 agent の自己実装は `role_boundary_violation`、target pane の未送信入力を安全に扱えない場合は `target_pane_input_dirty`、target pane の終了・再起動・lifecycle 変更は `target_pane_lifecycle_violation`、target pane が親 reviewer 自身または親 transcript を表示している場合は `self_handoff_blocked`。

## Workflow

1. 最新依頼を固定する。
   - 「レビュー」「レビュー連携」「実装」「git add」などの active plan を 1 文で確認してから動く。
   - `Implement the plan` は直前の plan だけを実行する。古い plan を復活させない。

2. 対象 pane と repo 状態を読む。
   - `git status --short --branch` で既存変更、staged/unstaged を確認する。
   - `tmux list-panes`、`tmux display-message` の `cursor_y` / `pane_height`、現在画面だけの `tmux capture-pane` で target pane、入力欄、作業中状態を確認する。
   - target pane が親 reviewer 自身の会話 pane ではないことを確認する。必要に応じて `controller_recent_markers` を helper に渡し、送信先が親 reviewer の直近作業ログを表示しているだけなら `self_handoff_blocked` として止める。
   - `.agents/skills/tmux-agent-review-loop/scripts/tmux_handoff_state.py` の helper が使える場合は、目視推測より `classify_current_input()` と `next_handoff_action()` の分類を優先する。
   - Codex TUI で任意の `› <text>` 行の下に `gpt-... · <path>` の status 行が見えるだけなら `idle_codex_surface` として扱い、送信済み transcript か idle prompt かを断定しない。ユーザーが「対象 pane は待機状態」と明示した場合は `user_confirmed_idle=True` を helper に渡せるが、cursor 近傍が normal unrelated text の場合は `stale_or_unrelated_input` として止める。
   - 直近の通知が composer に残る場合は `pending_handoff_notice` として追跡し、`Working` / 応答開始 / file read がなければ `C-m` を 1 回だけ再送する。再送済みなら `handoff_enter_retry_sent` として blocker にする。
   - Codex が起動していない pane をユーザーが自由に使ってよいと明示した場合は、`start_codex_then_send` として `codex` を起動し、Codex TUI 表示を確認してから file-based handoff を送る。
   - target pane を `interactive-executor`、`worker-owned`、`shell-only` のいずれかに分類する。ユーザーが進捗確認に使う既存 Codex pane は `interactive-executor` とし、親 reviewer が worker 起動や非対話実行で消費しない。
   - target pane を一意に確認できない場合は、レビューや実装修正へ進まず `target_pane_unresolved` で non-converged として停止する。
   - 詳細は `references/tmux_handoff_protocol.md` に従う。

3. レビューする。
   - 対象ファイル、差分、pane の完了報告、検証ログを根拠に findings first で書く。
   - findings は `implementable`、`needs_user_decision`、`resolved`、`non_issue` に分類する。
   - `Prior Findings Closure Table` に、ユーザー指摘、前 round の finding、明示 review artifact、既知の material finding をすべて載せる。再発見できないことは解消根拠ではない。
   - `Failure Hypothesis Table` で、semantic output、既存実装との差分、集計・重複排除・境界条件、ユーザー承認が必要な判断を高リスク仮説として確認する。
   - `no material findings requires negative evidence`: finding なしにする場合も、高リスク仮説ごとの negative evidence と source refs を artifact に残す。
   - `parent reducer must audit no-finding leaves`: target pane / 実行者の「合格」「修正完了」「9 点以上」は evidence ではなく input として扱い、親 reviewer が source refs で監査する。
   - `validators do not close semantic findings`: gate 通過だけで出力意味、設計契約、業務ルールの finding を閉じない。
   - `existing implementation output semantics are protected`: 既存実装の出力意味を変える、または別意味に読める文書化をする場合は、source-refed approval か明示 agreement override を要求する。
   - ユーザー意思決定が必要な要件レベルの論点があれば loop を止め、実装 pane へ判断を委譲しない。

4. レビュー結果をファイル化する。
   - 長文を tmux に直接 paste しない。
   - 親 reviewer は review artifact を file handoff する。target pane が受け持つ修正を親が自己実装しない。
   - 既定は `/tmp/<topic>_review_round<N>.md`。長期記録が必要な場合だけ `output/reviews/` など合意済み場所を使う。
   - 形式は `references/review_artifact_template.md` を使う。

5. pane へ連携する。
   - target pane input-clear boundary: Codex TUI、editor、または状態不明の target pane に、入力クリア目的で `C-c`、`C-u`、Escape、Backspace、削除キーを送らない。未送信入力がある場合はユーザー所有の入力として扱い、`target_pane_input_dirty` で non-converged にして停止する。
   - target pane dirty-input classification: dirty input は現在の編集可能 prompt / composition area、つまり current editable prompt の実入力だけで判定する。`capture-pane` 履歴内の placeholder、空 prompt の表示、過去送信済みの `› <submitted prompt>` のような transcript / last-submitted prompt 表示は、それだけでは dirty input ではない。
   - 判定が不確実なら、末尾の狭い capture や pane status を追加確認する。pane が実際には入力空なら、dirty-input 不確実性だけを理由に file handoff を skip しない。
   - shell prompt と確定でき、かつユーザーがその pane の入力クリアを明示した場合だけ、最小の入力クリアを行う。Codex TUI prompt では `C-c` が TUI 終了になり得るため使わない。
   - 送信前に target pane id と親 reviewer の会話 pane が異なることを再確認する。target が親自身なら送信せず、review artifact に `self_handoff_blocked` と記録して正しい pane を確認する。
   - `interactive-executor` では、ユーザー明示承認または target agent からの明確な依頼がない限り `C-c` / `C-u` を送らない。作業中状態があれば blocker として報告する。現在入力欄に送信可能な文があるなら `sendable_current_input` とし、消さずに `C-m` を 1 回送る。
   - 短い 1 行通知だけを `load-buffer`、`paste-buffer`、`send-keys C-m` の順に送る。
   - `Ctrl+J` は Enter ではなく改行として扱われることがあるため使わない。
   - subagent / worker が必要な場合、親 reviewer が新規 pane / window / session や `codex exec` を直接起動しない。レビュー artifact に「target pane の実行者が既存 Codex 会話を維持したまま、必要な worker を `codex-subagent` leaf task として構成する」指示を含める。
   - 送信後に `capture-pane` で positive acknowledgement を確認する。完了報告は、`Working`、応答開始、file read、または再確認後に期待通知が composer から消えたことを観測するまで行わない。数秒待っても期待通知が composer に残り、`Working` / 応答開始 / file read のいずれも見えない場合だけ、`C-m` を 1 回だけ再送して再確認する。
   - pane 側の受理を確認できない場合は、`handoff_unconfirmed` で non-converged として停止する。
   - target pane の Codex / shell / editor lifecycle はユーザー所有として扱う。ユーザー明示なしに `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、再起動、resume / fork を送らない。

6. 収束まで loop する。
   - pane 完了後、差分、指定 gate、`git status --short` を確認する。
   - 前 round の implementable finding が残れば次 round の artifact を作成して再連携する。
   - prior finding が `fixed` / `not_applicable` / `resolved` / `non_issue` / `needs_user_decision` のいずれにも分類できない場合は収束不能とする。
   - no finding round でも `Failure Hypothesis Table` に negative evidence がない場合は収束不能とする。
   - material finding がなく、必要 gate が通り、差分状態が期待どおりなら `converged` とする。
   - 要件判断、scope 超過、権限不足、pane 操作不能、gate failure の根本判断が必要な場合は stop_reason を明記してユーザーに戻す。

## Guardrails

- reviewer は、ユーザーが明示しない限り、対象成果物を自分で修正しない。
- tmux review-loop role boundary: 親 agent は reviewer / coordinator に留まり、target pane が受け持つ修正を自己実装しない。自己実装した場合は `role_boundary_violation` の material finding として扱い、converged にしない。
- ユーザー監視用の既存 interactive Codex pane を disposable worker として扱わない。そこへ `codex exec` を投入したり、対話セッションを shell に戻す操作をしない。
- subagent / worker が必要な場合、親 reviewer が直接起動せず、target pane の実行者に `codex-subagent` leaf task としての作成と監督を依頼する。
- target pane lifecycle boundary: target pane は user-owned runtime surface として扱う。親 agent が後片付けのつもりで Codex TUI、shell、editor、または tmux pane を終了・再起動してはいけない。終了・再起動が必要に見える場合はユーザー確認に戻す。
- target pane input-clear boundary: target pane の prompt 入力も user-owned state。Codex TUI / editor / unknown prompt に対する `C-c` / `C-u` は入力クリアではなく lifecycle や user input mutation になり得るため、ユーザー明示なしに送らない。
- target pane dirty-input classification: dirty input は現在の編集可能 prompt / composition area、つまり current editable prompt にある実入力、または prompt area の途中 paste だけを指す。placeholder、空 prompt affordance、過去送信済みの `› ...` transcript / last-submitted prompt 表示は non-dirty とする。不確実なら狭い capture / status を追加し、入力空の pane への handoff を誤って skip しない。
- 任意の `› <text>` 行と status 行を `sendable_current_input` や stale 入力と誤判定しない。`idle_codex_surface` の場合は `C-m` だけを送らず、file-based handoff 通知を送って受理確認する。ただし `pending_handoff_notice` が composer に残り、positive acknowledgement がなければ status 行を送信済み transcript の証拠にせず、`C-m` を 1 回だけ送って再確認する。
- Codex が起動していない pane をユーザーが自由に使ってよいと明示した場合は、handoff 前に `codex` を起動する。`codex` が PATH にない、または Codex TUI が起動しない場合は blocker として報告し、親 reviewer が代替 worker を勝手に起動しない。
- `target_pane_unresolved`、`handoff_unconfirmed`、`role_boundary_violation`、`target_pane_input_dirty`、`target_pane_lifecycle_violation`、`self_handoff_blocked` のいずれかが残る round は non-converged とする。
- 実行者の自己採点や validator 通過だけで review loop を閉じない。`Prior Findings Closure Table` と `Failure Hypothesis Table` の証拠不足は stop_reason にする。
- tmux 連携だけを求められた時に、文書編集や `git add` を実行しない。
- 長文 paste ではなくファイル連携を使う。
- 送信前確認、`C-m` 送信、送信後確認を省略しない。
- `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、target pane の resume / fork / 再起動は、ユーザーが明示した時だけ行う。Codex TUI / editor / unknown prompt の入力クリアとして `C-c` / `C-u` を送ることも同じく禁止する。
- 無関係な既存変更は stage / revert しない。
- 要件レベルの意思決定を実装 pane に任せない。

## References

- `references/tmux_handoff_protocol.md`
- `references/review_loop_protocol.md`
- `references/review_artifact_template.md`
