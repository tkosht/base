# tmux-agent-review-loop

- Purpose: tmux pane 上の別 agent の作業を、親 agent が reviewer / coordinator としてレビュー、ファイル連携、修正依頼、再レビューまで回す
- Use when: tmux pane へのレビュー連携、pane 側実装の再レビュー、修正後確認、収束までの review/fix/verify loop が必要なとき
- Skill source: `.agents/skills/tmux-agent-review-loop`
- Claude shim: `.claude/skills/tmux-agent-review-loop`
- Codex compatibility shim: `.codex/skills/tmux-agent-review-loop`
- Key outputs: `target_pane`、`review_artifact`、finding classification、handoff confirmation、target pane lifecycle preservation、`loop_state`、verification summary
- Notes: 長文は直接 paste せず review artifact をファイル化する。pane 連携は `C-m` 送信後の `tmux capture-pane` で `Working`、実行ログ、または応答開始を確認し、入力欄に残る場合は `C-m` を 1 回だけ再送して再確認する
- Handoff helper: `.agents/skills/tmux-agent-review-loop/scripts/tmux_handoff_state.py` は `idle_codex_surface`、`pending_handoff_notice`、`sendable_current_input`、`self_handoff_blocked`、`start_codex_then_send` を分類する。任意の `› <text>` と status 行だけでは未送信入力とみなさず、`pending_handoff_notice` が残る場合だけ `C-m` 再送を 1 回に制限する。`controller_recent_markers` で親 transcript への自己 handoff を防ぎ、`user_confirmed_idle` は cursor 近傍が空 / status / prompt-like の時だけ補助 evidence として使う
- Review gatekeeping: `Prior Findings Closure Table` と `Failure Hypothesis Table` を使い、no material findings requires negative evidence、parent reducer must audit no-finding leaves、validators do not close semantic findings、existing implementation output semantics are protected を守る。実行者の自己採点や gate 通過だけで収束扱いにしない
- tmux review-loop role boundary: 親 agent は reviewer / coordinator に留まり、review artifact を file handoff する。target pane 未確定は `target_pane_unresolved`、handoff 未確認は `handoff_unconfirmed`、親の自己実装は `role_boundary_violation`、target pane が親自身または親 transcript を表示している場合は `self_handoff_blocked` として non-converged にする
- target pane lifecycle boundary: target pane は user-owned runtime surface。親 agent はユーザー明示なしに `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、再起動、resume / fork をしない。違反は `target_pane_lifecycle_violation` として non-converged にする
- target pane input-clear boundary: target pane の prompt 入力も user-owned state。Codex TUI / editor / unknown prompt に入力クリア目的で `C-c` / `C-u` を送らない。未送信入力を安全に扱えない場合は `target_pane_input_dirty`、その操作で TUI 終了など lifecycle 変更が起きた場合は `target_pane_lifecycle_violation` として non-converged にする
- target pane dirty-input classification: dirty input は現在の編集可能 prompt / composition area、つまり current editable prompt の実入力、または prompt area の途中 paste だけ。placeholder、空 prompt affordance、過去送信済みの `› <submitted prompt>` のような transcript / last-submitted prompt 表示は non-dirty。不確実なら狭い capture / status を追加確認し、入力空の pane への file handoff を dirty-input 不確実性だけで skip しない
- Worker boundary: ユーザー監視用の `interactive-executor` pane を disposable worker として扱わない。subagent / worker が必要な場合、親 reviewer が直接起動せず、target pane の実行者に `codex-subagent` leaf task として作成・監督を依頼する
