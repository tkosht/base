# tmux Handoff Protocol

## Goal

tmux pane 上の別 agent にレビュー結果や作業依頼を確実に渡す。長文 paste の欠落、未送信入力の残留、Enter 未送信、誤 pane 送信、target pane の誤終了を防ぐ。

tmux review-loop role boundary: 親 agent は reviewer / coordinator に留まり、target pane が受け持つ修正を自己実装しない。

target pane lifecycle boundary: target pane は user-owned runtime surface として扱う。親 reviewer はユーザー明示なしに `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、再起動、resume / fork を送らない。後片付けが必要に見えても、pane の維持・終了判断はユーザーに戻す。

target pane input-clear boundary: target pane の prompt 入力も user-owned state として扱う。Codex TUI、editor、または状態不明の target pane に入力クリア目的で `C-c`、`C-u`、Escape、Backspace、削除キーを送らない。未送信入力を安全に扱えない場合は `target_pane_input_dirty` で停止する。

target pane dirty-input classification: dirty input は現在の編集可能 prompt / composition area、つまり current editable prompt にある実入力、または prompt area の途中 paste だけで判定する。`capture-pane` 履歴の placeholder、空 prompt affordance、過去送信済みの `› <submitted prompt>` のような transcript / last-submitted prompt 表示は、それだけでは non-dirty とする。不確実なら末尾の狭い capture や pane status を追加確認し、入力空の pane への file handoff を dirty-input 不確実性だけで skip しない。

## Preflight

必ず送信前に pane 一覧と対象 pane の末尾を確認する。

```bash
tmux list-panes -F '#{pane_index}: #{pane_id} #{pane_current_command} #{pane_title} #{pane_current_path}'
tmux display-message -p -t %0 'pane_height=#{pane_height} cursor_y=#{cursor_y} pane_in_mode=#{pane_in_mode} current_command=#{pane_current_command}'
tmux capture-pane -t %0 -p -S -40
```

確認すること:

- pane id がユーザー指定と一致している。
- `pane_current_command` と `pane_current_path` が想定と大きくずれていない。
- target pane が親 reviewer 自身の会話 pane ではないか。必要に応じて helper に `controller_recent_markers` を渡し、親の transcript が見える pane なら `self_handoff_blocked` とする。
- 入力欄に未送信文が残っていないか。`capture-pane` の scrollback に残る `› ...`、過去の user message、直前に送信済みの handoff 文、または Codex の idle prompt 例を未送信入力と誤認しない。
- dirty input 判定を現在の編集可能 prompt / composition area、つまり current editable prompt に限定しているか。履歴上の `› ...` transcript や placeholder だけを未送信入力と誤認しない。
- Codex TUI で任意の `› <text>` 行の下に `gpt-... · <path>` の status 行が見えるだけなら `idle_codex_surface` として扱い、送信済み transcript か idle prompt かを断定しない。
- 直近で貼った通知を `pending_handoff_notice` として追跡している場合、その通知が composer に残り、`Working` / 応答開始 / file read の positive acknowledgement がなければ status 行は送信済み transcript の証拠ではない。
- `Working`、テスト実行、エディタ操作中など、割り込みが危険な状態ではないか。
- pane を閉じる、再起動する、resume する権限がユーザーから明示されているか。明示がなければ lifecycle 操作は禁止。
- Codex TUI / editor / unknown prompt の入力欄を消す権限がユーザーから明示されているか。明示がなければ `C-c` / `C-u` などの入力クリア操作は禁止。

target pane を一意に確認できない場合は、レビュー本文の作成や対象成果物の修正へ進まず、`target_pane_unresolved` で non-converged として停止する。

## Current Input Detection

未送信入力の判定は、scrollback ではなく現在画面と cursor 近傍を優先する。helper が使える場合は `.agents/skills/tmux-agent-review-loop/scripts/tmux_handoff_state.py` の `classify_current_input()` と `next_handoff_action()` を使う。

分類と対応:

- `idle_empty`: 現在入力欄が空。1 行 handoff を `load-buffer`、`paste-buffer`、`send-keys C-m` で送る。
- `idle_codex_surface`: 任意の `› <text>` 行と status 行が見えるが、それだけでは未送信入力ではない。`C-m` だけを送らず、1 行 handoff を file-based handoff として送る。
- `pending_handoff_notice`: 期待した直近 handoff 通知が composer に残り、positive acknowledgement がない。`tmux send-keys -t <pane> C-m` を 1 回だけ送って再 capture する。`handoff_enter_retry_sent` が true でも残る場合は blocker として止める。
- `sendable_current_input`: 現在入力欄に送信可能な文がある。`C-u` で消さず、まず `tmux send-keys -t <pane> C-m` を 1 回送る。送信後に再 capture し、必要なら handoff を続ける。
- `stale_or_unrelated_input`: 現在入力欄に現在タスクと無関係な文がある。`interactive-executor` では勝手に消さず、ユーザーまたは target agent の置換承認がない限り止める。
- `busy_or_running`: `Working`、テスト実行、エディタ操作中など。割り込みせず止める。
- `self_handoff_blocked`: target pane が親 reviewer 自身、または親 transcript を表示している。送信せず、正しい pane を確認する。
- `start_codex_then_send`: pane が shell-only などで Codex が起動しておらず、ユーザーが pane 利用を許可している。`codex` を起動し、Codex TUI の表示を確認してから 1 行 handoff を送る。`codex` が PATH にない場合は blocker として報告し、親が代替 worker を勝手に起動しない。

検証用 helper:

```bash
uv run pytest -q tests/harness_autoptimizer/test_tmux_handoff_state.py
```

このテストは、任意の `› <text>` と status 行の組み合わせを `sendable_current_input` ではなく `idle_codex_surface` と判定し、`user_confirmed_idle=True` でも cursor 近傍が normal unrelated text の場合は止め、期待通知が composer に残る場合だけ `pending_handoff_notice` から `C-m` 再送を要求する。

## Pane Role Classification

送信前に target pane の役割を分類する。

- `interactive-executor`: ユーザーが進捗を監視し、親 reviewer が会話を維持する既存 Codex pane。非対話 `codex exec` の実行場所にしない。
- `worker-owned`: target pane の実行者が明示的に作った補助 pane。標準の worker 単位ではなく、ユーザーが pane worker を明示した場合だけ扱う。
- `shell-only`: Codex 対話ではない shell pane。ユーザーが実行面として指定していない限り、長時間 worker 用に転用しない。

`interactive-executor` は人間が見ている進捗面である。親 reviewer はこの pane を消費して subagent や worker を起動せず、必要な場合は review artifact や短い handoff で target pane の実行者に worker 作成を依頼する。

## Clear Existing Input

入力欄に未送信文が残っている、途中 paste が切れている、`Conversation interrupted` 後の入力が残っている場合は、まず target の種類とユーザー明示許可を確認する。安全に消せない入力は親 reviewer が消さない。

```bash
tmux capture-pane -t %0 -p -S -12
```

target pane が Codex TUI、editor、または状態不明なら、親 reviewer は入力を消さない。`C-c` は Codex TUI を終了させ得る。`C-u` や Escape / Backspace / 削除キーも user-owned input mutation になり得る。未送信入力がある場合は `target_pane_input_dirty` として non-converged にし、ユーザーへ「入力を消してよいか」または「target pane 側で送信/破棄するか」を確認する。

target pane が shell prompt と確定でき、かつユーザーがその pane の入力クリアを明示した場合だけ、最小操作で入力欄を消す。Codex TUI prompt に `C-c` / `C-u` を送って「クリア」とみなしてはいけない。

Codex TUI の `› <submitted prompt>` が過去送信済み prompt の表示として capture に残っているだけなら、現在の prompt は dirty ではない。現在の編集可能 prompt、つまり current editable prompt に文字がある、または paste 中断片が残っている場合だけ dirty とする。

## File-Based Handoff

Cursor 経由や長文の tmux paste は途中で切れることがある。レビュー本文は共有ファイルに書き、pane へは短い 1 行通知だけを送る。

推奨:

- 一時連携: `/tmp/<topic>_review_round<N>.md`
- 長期記録が必要: 合意済みの `output/reviews/<topic>_review_round<N>.md`

通知例:

```text
レビュー結果ファイル: /tmp/<topic>_review_round1.md を確認し、指摘対応後に指定 gate と git status を確認してください。
```

subagent / worker が必要な場合も、親 reviewer が新規 pane / window / session や `codex exec` を直接起動しない。通知や review artifact には、target pane の実行者が既存 Codex 会話を維持したまま `codex-subagent` leaf task として worker を構成し、結果を報告するよう明記する。

## Send Sequence

送信は必ず `load-buffer`、`paste-buffer`、`send-keys C-m` の順で行う。`Ctrl+J` は改行になることがあるため使わない。`Enter` という named key だけに依存しない。送信直前にも target pane id が親 reviewer 自身ではないことを確認する。

`/tmp/<topic>_handoff_notice.txt` は `Write` tool で事前に作る。内容は短い 1 行にする。

```bash
tmux load-buffer -b tmux-agent-review-handoff /tmp/<topic>_handoff_notice.txt
tmux paste-buffer -t %0 -b tmux-agent-review-handoff
tmux send-keys -t %0 C-m
```

## Post-Send Verification

送信後に必ず確認する。

```bash
tmux capture-pane -t %0 -p -S -25
tmux display-message -p -t %0 'pane_dead=#{pane_dead} pane_in_mode=#{pane_in_mode} current_command=#{pane_current_command}'
```

成功の目安:

- 入力欄に通知文が残っていない。
- 相手が `Working` になった。
- 相手がファイルを読む、作業方針を述べる、またはコマンド実行に入った。
- paste 直後に送信が効かないことがあるため、数秒待っても期待通知が composer に残り、`Working` / 応答開始 / file read のいずれも見えない場合だけ、`C-m` を 1 回だけ再送する。再送後も期待通知が残る場合は `handoff_enter_retry_sent` の状態で blocker として報告し、追加送信しない。期待通知が composer に見え、その下に status 行があるだけの画面は送信済み transcript の証拠ではない。

未送信に見える場合:

- まず `capture-pane` で本当に入力欄に残っているか確認する。
- 残っているなら `tmux send-keys -t %0 C-m` を 1 回だけ送る。
- scrollback 上の `› ...` だけなら未送信扱いしない。現在入力欄に現在タスクと無関係な文が残っているなら、`interactive-executor` では勝手に消さず `stale_or_unrelated_input` として報告する。
- それでも送れない場合は追加入力せず、pane 状態と blocker を報告する。

handoff の受理を確認できない場合は、作業を自己実装で代替せず、`handoff_unconfirmed` で non-converged として停止する。親 reviewer は review artifact を file handoff し、target pane の修正を自己実装した場合は `role_boundary_violation` として扱う。

## Target Pane Lifecycle

handoff 後や target pane の完了後も、親 reviewer は pane を cleanup しない。以下はユーザー明示なしに禁止する。

- `C-d`、`exit`、`quit`、Codex TUI の終了操作。
- Codex TUI / editor / unknown prompt への入力クリア目的の `C-c`、`C-u`、Escape、Backspace、削除キー。
- `tmux kill-pane`、pane respawn、pane rename を含む lifecycle 変更。
- Codex session の resume / fork / restart。
- 「こちらが起動したから閉じてよい」という推測による終了。

誤って lifecycle 操作をした場合は、`target_pane_lifecycle_violation` として non-converged にし、確認済み事実、復旧手段、未確認リスクを分けて報告する。

## Anti-Patterns

- 長いレビュー本文を直接 paste する。
- 送信前に pane 状態を見ない。
- 入力欄に古い途中入力があるまま追加入力する。
- `Ctrl+J` で送信したつもりになる。
- `Enter` named key だけで送信確認を省く。
- paste だけで完了扱いにする。
- `capture-pane` の古い履歴を見て、現在入力欄の状態と誤認する。
- 既存の `interactive-executor` Codex pane に `codex exec` を投入し、対話セッションを shell に戻す。
- 親 reviewer が target pane の代わりに subagent / worker pane を作成する。
- `codex-subagent` で足りる worker を tmux pane / window / session として作るよう依頼する。
- Codex TUI の placeholder、空 prompt 表示、過去送信済みの `› ...` transcript を未送信入力と誤認して handoff を skip する。
- 任意の `› <text>` 行と status 行が見える `idle_codex_surface` に対して、`C-m` だけを送れば handoff になると誤認する。
- paste 後の送信受理確認をせず、通知文が composer に残ったまま成功扱いにする。
- target pane 未確定、handoff 未確認、または親 reviewer の自己実装を残したまま converged とする。
- Codex TUI prompt に残った未送信入力を `C-c` / `C-u` で消そうとする。
- 未送信入力があるのに `target_pane_input_dirty` で止まらず、親が入力欄を上書きする。
- target pane をユーザー明示なしに `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、再起動、resume / fork する。
