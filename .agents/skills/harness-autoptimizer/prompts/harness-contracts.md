# Harness Prompt Contracts

These sections are generic harness contracts appended by
`harness_autopt.py`. The Markdown is the source of the contract text; the
helper only transports it into effective prompts.

## Agreement Reversal Contract

Markers:

- agreement override
- hidden reversal proposal
- material ReviewFinding
- do not bury reversal as cleanup

Prompt text:

- Preserve accepted specs, explicit assumptions, and prior agreements as
  binding inputs until the user changes them.
- If changing a binding input is necessary, surface it as an agreement
  override: a user-visible proposal with evidence, impact, alternative
  behavior, and validation, then wait for approval before implementation.
- A hidden reversal proposal is a silent attempt to mix that change into code,
  docs, tests, prompt expectations, option guidance, or cleanup; treat it as a
  material ReviewFinding.
- Do not bury reversal as cleanup.

## Conversation Capture Contract

Markers:

- agent-owned conversation capture
- retention-worthy conversation event
- Codex agent owns retention judgment
- no user-maintained ledger
- no helper-owned agreement meaning
- sanitized pending ExperienceCandidate
- source refs, not raw transcript
- self_handoff_blocked
- user_confirmed_idle
- `tmux capture-pane -S -40`
- cursor 近傍
- helper classification
- file-based handoff

Prompt text:

- Use agent-owned conversation capture for retention-worthy user corrections,
  agreements, accepted specs, and explicit assumptions.
- Treat each retention-worthy conversation event as the Codex agent's
  responsibility: Codex agent owns retention judgment.
- Emit a sanitized pending ExperienceCandidate during the conversation when
  mutation is blocked; do not wait for the user to maintain a ledger.
- Keep no user-maintained ledger and no helper-owned agreement meaning.
- Store source refs, not raw transcript, raw prompts, raw model output,
  secrets, runtime logs, or session-only URLs.
- For tmux handoff, prefer cursor 近傍 and helper classification over broad
  scrollback. If the user says the target pane is idle, pass
  `user_confirmed_idle=True` only as supporting evidence, not as permission to
  overwrite unrelated current input.
- Before handoff, ensure the target is not the parent conversation. Stop with
  `self_handoff_blocked` when pane ids match or recent parent markers appear.

## Review Gatekeeping Contract

Markers:

- Prior Findings Closure Table
- Failure Hypothesis Table
- no material findings requires negative evidence
- parent reducer must audit no-finding leaves
- validators do not close semantic findings
- existing implementation output semantics are protected
- meaning-first repair
- Context Reconstruction Table
- latest comment is evidence, not the repair target
- literal patch
- keyword presence is not closure evidence
- target-layer review
- meta-layer review
- recursive review pass
- same resource/goal/editable paths
- docs/implementation/tests consistency
- no data-specific embedded values
- clone referenced source repos
- `git clone`
- `git fetch`
- needs_user_decision

Prompt text:

- Review leaves must search for reasons to fail before accepting reasons to
  pass; executor self-scoring is review input, not closure evidence.
- Use meaning-first repair before editing: reconstruct the target artifact's
  intended expression, resource purpose, target layer, meta layer,
  reader/operator, source refs, prior user corrections, implicit-context
  assumptions, in-scope/out-of-scope boundary, unknowns, and ask-user trigger
  in a Context Reconstruction Table.
- The latest comment is evidence, not the repair target. Do not implement a
  literal patch when it contradicts the reconstructed intended expression.
- Keyword presence is not closure evidence. Closure requires source-refed
  alignment with the intended expression and removal of the impact path, or an
  explicit user/source approval for the material decision.
- Maintain a Prior Findings Closure Table for user-raised issues, prior
  reviewer findings, review artifacts, and proactive probe findings. A known
  item remains open until a reviewer closes it as fixed, not_applicable,
  resolved, non_issue, or needs_user_decision with source refs.
- Maintain a Failure Hypothesis Table for high-risk semantic,
  output-compatibility, aggregation, deduplication, boundary, runtime/config,
  data-write, and approval-dependent hypotheses. No material findings requires
  negative evidence and source refs for these hypotheses.
- A parent reducer must audit no-finding leaves by rechecking known findings
  and high-risk hypotheses. Missing evidence is unresolved, not convergence.
- Validators do not close semantic findings; tests, lint, diff guards, and
  application gates are necessary but cannot substitute for output meaning,
  design contracts, runtime configuration, or business-rule review.
- Existing implementation output semantics are protected unless source-refed
  approval or an explicit agreement override authorizes the change.
- Clone referenced source repos before declaring them unavailable. When a
  review depends on a referenced repository or upstream source, first try an
  existing local checkout, `git fetch`, or `git clone` with available
  credentials; record the checkout path or remote, commit hash, and any failure
  reason.
- If local checkout, `git fetch`, and `git clone` fail, keep the missing source
  as a blocker or residual risk with command-level evidence instead of
  guessing from absence.
- Review target and meta layers as a pair: target-layer review checks the
  changed artifact; meta-layer review checks the harness, prompt, or test
  prevents the same failure class without overfitting.
- When harness rules, prompts, or tests are changed, they become target
  artifacts for a recursive review pass bounded to the same resource, goal,
  editable paths, excluded paths, and diff limits.
- Check necessary and sufficient scope, docs/implementation/tests consistency,
  stale or over-complex structure cleanup, no data-specific embedded values,
  appropriate abstraction, readability, maintainability, operability,
  extensibility, and current security best practices.
- When logic cannot decide the correct behavior, keep the finding unresolved
  and explain it as `needs_user_decision` instead of guessing.

## User-Facing Language Contract

Markers:

- user-facing plain language
- plain Japanese before internal labels
- avoid unexplained jargon
- translate internal review labels
- scope decision before technical label

Prompt text:

- Follow `docs/standards/communication.md` for every user-facing update,
  question, handoff notice, and closeout.
- Lead with the concrete meaning in plain Japanese before using internal
  labels such as ReviewFinding, AutoptRequest, verification_class, DAG, leaf,
  reducer, or gate.
- If an internal label is useful, define it in the same sentence and reuse it
  only when it helps the reader.
- Before proposing a fix, say exactly what file or behavior would change and
  why it is inside the user's requested scope.
- Review artifacts may keep structured labels, but user-facing summaries must
  include a plain-language paraphrase before or next to those labels.
