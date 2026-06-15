# Review Loop Protocol

## Roles

- Parent reviewer: レビュー、指摘整理、handoff、収束判定、ユーザー意思決定の取りまとめを行う。review target は編集しない。target pane の代わりに subagent / worker を起動せず、必要な worker の最小枠組みを target pane agent に渡す。
- Target pane agent: 指摘対応、検証、必要な staging を行う。追加 worker が必要な場合は既存 Codex 会話を維持したまま `codex-subagent` leaf task として作成・監督し、親 reviewer へ結果を報告する。
- User: 要件・仕様・スコープ・受け入れ基準の意思決定を行う。

tmux review-loop role boundary: 親 agent は reviewer / coordinator に留まり、target pane が受け持つ修正を自己実装しない。
target pane lifecycle boundary: target pane は user-owned runtime surface として扱い、親 reviewer はユーザー明示なしに `C-d`、`exit`、`quit`、`tmux kill-pane`、Codex TUI 終了、再起動、resume / fork を行わない。
target pane input-clear boundary: target pane の prompt 入力も user-owned state として扱い、Codex TUI、editor、または状態不明の target pane へ入力クリア目的で `C-c` / `C-u` を送らない。未送信入力を安全に扱えない場合は `target_pane_input_dirty` とする。
target pane dirty-input classification: dirty input は現在の編集可能 prompt / composition area、つまり current editable prompt の実入力、または prompt area の途中 paste だけを指す。placeholder、空 prompt affordance、過去送信済みの `› <submitted prompt>` のような transcript / last-submitted prompt 表示は non-dirty とする。不確実なら狭い capture / status を追加確認し、入力空の pane への handoff を skip しない。

## Separation Contract

レビュー対象の修正は target pane agent が行い、parent reviewer は行わない。

理由:

- レビューと修正を 2 つ以上の別セッション / 別 agent に分けることで、指摘の具体性と修正結果の対応を外部化できる。
- 親 reviewer が同じセッションで修正すると、指摘に書かなかった前提や暗黙文脈を無意図に補完できてしまい、レビュー artifact の不足を検出できない。
- 別 agent が修正することで、レビュー文の解釈ずれ、実装方向のずれ、受け入れ基準の曖昧さが差分として表面化する。

例外:

- ユーザーが明示的に「親が対象ファイルを直接修正してよい」と指示した場合のみ、親が修正できる。その場合も、レビュー分離を破る理由、対象 path、検証方法を報告する。
- review loop skill や handoff protocol 自体の改善は、レビュー対象成果物ではないため親が修正できる。ただし target artifact と混ぜない。

## Round State

各 round で以下を明示する。

- `round`: 1 から始まる番号。
- `target`: 対象ファイル、差分、pane、pane role。
- `findings`: 指摘一覧。
- `handoff_file`: pane に渡したレビュー結果ファイル。
- `expected_actions`: 実装 pane に期待する修正、検証、git 操作、必要時の `codex-subagent` leaf worker 作成。
- `verification`: reviewer が確認する gate と状態。
- `converged`: true / false。
- `stop_reason`: 収束しない場合の理由。
- `nonconverged_stop_reasons`: target pane 未確定は `target_pane_unresolved`、handoff 未確認は `handoff_unconfirmed`、親 reviewer の自己実装は `role_boundary_violation`、target pane の未送信入力を安全に扱えない場合は `target_pane_input_dirty`、target pane lifecycle 変更は `target_pane_lifecycle_violation`、target pane が親 reviewer 自身または親 transcript を表示している場合は `self_handoff_blocked`。

## Finding Classification

- `implementable`: 既存合意とローカル事実だけで実装者が直せる。
- `needs_user_decision`: 要件、仕様、スコープ、優先度、互換性、受け入れ基準の判断が必要。
- `resolved`: 前 round の指摘が解消済み。
- `non_issue`: 調査の結果、指摘として扱わない。

`needs_user_decision` がある場合は、実装 pane へ修正依頼を続けず、ユーザーに戻す。実装者にプロダクト判断を任せない。

## Review Gatekeeping

実行者の完了報告、自己採点、validator 通過は review input であり、閉鎖 evidence ではない。

- `Prior Findings Closure Table`: ユーザー指摘、前 round の finding、明示 review artifact、既知の material finding をすべて載せる。再発見できないことは解消根拠ではない。
- `Failure Hypothesis Table`: semantic output、既存実装との差分、集計・重複排除・境界条件、ユーザー承認が必要な判断を高リスク仮説として確認する。
- `no material findings requires negative evidence`: finding なしにする場合も、高リスク仮説ごとの negative evidence と source refs を残す。
- `parent reducer must audit no-finding leaves`: target pane / 実行者の「合格」「修正完了」「9 点以上」をそのまま採用せず、親 reviewer が source refs で監査する。
- `validators do not close semantic findings`: gate 通過だけで出力意味、設計契約、業務ルールの finding を閉じない。
- `existing implementation output semantics are protected`: 既存実装の出力意味を変える、または別意味に読める文書化をする場合は、source-refed approval か明示 agreement override を要求する。

## Review Checklist

- 最新のユーザー依頼と active plan が一致しているか。
- 自分が実装者ではなく reviewer である場合、review target を勝手に修正していないか。
- review target の修正は target pane agent が行い、parent reviewer は artifact / handoff / re-review だけを担当しているか。
- `Prior Findings Closure Table` で既知 finding が消えずに閉鎖されているか。
- `Failure Hypothesis Table` で no finding に必要な negative evidence が示されているか。
- ユーザー監視用の `interactive-executor` pane を消費、上書き、終了させていないか。
- subagent / worker が必要な場合、親 reviewer が直接起動せず target pane agent へ `codex-subagent` leaf task として依頼しているか。
- target pane を `tmux list-panes` / `tmux capture-pane` で一意に確認したか。
- review artifact を file handoff し、`C-m` 送信後の受理を capture で確認したか。
- dirty input 判定を現在の編集可能 prompt / composition area、つまり current editable prompt に限定し、placeholder や過去送信済み `› ...` transcript を未送信入力と誤認していないか。
- Codex TUI / editor / unknown prompt に `C-c` / `C-u` を送らず、未送信入力があれば `target_pane_input_dirty` で止めたか。
- target pane を終了・再起動・resume / fork していないか。必要ならユーザー明示確認を得たか。
- 差分がレビュー指摘だけを反映しているか。
- 無関係な既存変更を stage / revert していないか。
- 指定 gate が通っているか。
- `git status --short` が期待どおりか。
- 以前の指摘がすべて fixed / not_applicable / resolved / non_issue / needs_user_decision に分類されているか。

## Loop Exit

`converged=true` にできる条件:

- material な `implementable` finding が残っていない。
- `needs_user_decision` がない。
- `Prior Findings Closure Table` の全行が `fixed` / `not_applicable` / `resolved` / `non_issue` / `needs_user_decision` として説明されている。
- no finding の場合、`Failure Hypothesis Table` に negative evidence と source refs がある。
- 指定 gate が通っている、または未実行理由が受け入れ可能として明記されている。
- stage / unstaged 状態が依頼と一致している。
- target pane が完了を報告しているか、reviewer が差分と gate から完了を確認している。
- `target_pane_unresolved`、`handoff_unconfirmed`、`role_boundary_violation`、`target_pane_input_dirty`、`target_pane_lifecycle_violation`、`self_handoff_blocked` が残っていない。

停止条件:

- target pane を一意に確認できない。この場合は `target_pane_unresolved`。
- review artifact の file handoff と送信後受理を確認できない。この場合は `handoff_unconfirmed`。
- target pane が親 reviewer 自身、または親 transcript を表示している。この場合は `self_handoff_blocked`。
- 親 reviewer がユーザー明示なしに target pane の修正を自己実装した。この場合は `role_boundary_violation`。
- target pane の Codex TUI / editor / unknown prompt の現在の編集可能 prompt / composition area、つまり current editable prompt に未送信入力があり、ユーザー明示なしには消せない。この場合は `target_pane_input_dirty`。placeholder、空 prompt affordance、過去送信済み `› ...` transcript だけなら停止理由にしない。
- 親 reviewer が Codex TUI / editor / unknown prompt に入力クリア目的で `C-c` / `C-u` を送った。この場合は、入力改変だけなら `target_pane_input_dirty`、TUI 終了や shell 遷移など lifecycle 変更が起きたなら `target_pane_lifecycle_violation`。
- 親 reviewer がユーザー明示なしに target pane の Codex TUI、shell、editor、または tmux pane を終了・再起動・resume / fork した。この場合は `target_pane_lifecycle_violation`。
- 要件判断が必要。
- 同じ finding が 2 round 以上残り、依頼文では解消できない。
- target pane が送信不能、停止、誤 pane、または `interactive-executor` として会話維持できない状態と判明した。
- gate failure が実装範囲外または環境要因で、追加判断が必要。
- ユーザーが停止・中断・方針変更を指示した。

## Verification Commands

タスクに応じて最小の検証を選ぶ。

```bash
git status --short --branch
git diff --cached --name-status
git diff --name-status
make doctor
```

コード変更を伴う場合は、対象テストや `make lint` / `make test-harness` を追加する。ただし reviewer が実装 pane の代わりに勝手に修正しない。

## Common Failure Recovery

- 古い plan を実行した: 最新のユーザー依頼を読み直し、何を実行したか、何を実行していないかを分けて報告する。
- 誤って review target を自分で修正した: 自分の変更だけを特定して戻す。ユーザーや別 agent の変更は戻さない。戻せない場合は、どの path に親修正が混入したかを明示してユーザー判断に戻す。
- 誤って interactive Codex pane を worker として消費した: 原因を報告し、それ以上の pane 操作を止める。復旧はユーザー承認または target pane agent の指示を待つ。
- paste が途中で切れた: target pane が Codex TUI / editor / unknown prompt なら入力欄を消さず、`target_pane_input_dirty` として止める。shell prompt かつユーザーが明示した場合だけ最小操作で入力欄を消し、ファイル連携に切り替える。
- transcript を未送信入力と誤認した: 末尾の狭い capture と pane status で現在の編集可能 prompt、つまり current editable prompt を確認する。`› <submitted prompt>` のような過去送信済み表示だけなら non-dirty とし、file handoff を続ける。
- 送信確定ができていない: `capture-pane` で入力欄に残っていることを確認してから `send-keys C-m` を 1 回再送する。
- 親 reviewer が自己実装した: `role_boundary_violation` として round を non-converged にし、自己実装範囲と未 handoff 範囲を分けてユーザーに報告する。
- target pane を誤って終了した: `target_pane_lifecycle_violation` として round を non-converged にし、resume ID など復旧手段が capture で確認できる場合だけ報告する。以後の lifecycle 操作はユーザー確認まで止める。
