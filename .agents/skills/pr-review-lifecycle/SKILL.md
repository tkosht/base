---
name: pr-review-lifecycle
description: "Auto-trigger when the user asks to review a GitHub PR, post PR review feedback, hand findings to a tmux pane, or run a PR review response cycle end-to-end: inspect review feedback, fix actionable threads, request or re-run review, verify checks, and resolve addressed GitHub review threads."
allowed-tools:
  - Bash(git:*)
  - Bash(gh:*)
  - Bash(make:*)
  - Bash(npm:*)
  - Bash(npx:*)
  - Read
  - Write
  - Glob
metadata:
  version: 0.1.0
  owner: codex
  maturity: draft
  tags: [skill, github, review, pull-request]
---

# PR Review Lifecycle

## Purpose

Use this skill to drive a pull request from initial content review or actionable review feedback through findings-first review, repair, verification, review re-request, and GitHub thread resolution without treating "comment resolved" as a substitute for evidence.

## Workflow

1. Identify the PR from the URL, number, or current branch. Confirm `git status --short --branch`, PR head, base, check state, deployment comments, and thread-aware review state.
2. Read the PR diff, file list, reviews, status checks, and unresolved review threads with a thread-aware GitHub surface, not only flat comments. Separate actionable findings, informational notes, outdated comments, and already-addressed threads.
3. When the user asks for PR content review rather than repair, write findings first, anchored to the reviewed head commit, with severity, file/line, impact, and fix direction. Post a top-level PR Conversation comment only when requested or when the lifecycle explicitly includes GitHub feedback.
4. For each actionable cluster, make a `RootCauseReview`: missed invariant, why existing tests or probes passed, same-class risk sweep, and the smallest durable regression target.
5. Maintain a `Prior Findings Closure Table` for previous reviews, PR comments, user corrections, and known material findings. Re-discovering no issue is not closure; each item needs source refs and a status such as fixed, not_applicable, resolved, non_issue, needs_user_decision, or unresolved.
6. Maintain a `Failure Hypothesis Table` for semantic output, implementation compatibility, aggregation, deduplication, boundaries, runtime/config, data-write, and approval-dependent decisions. `no material findings requires negative evidence`; each high-risk hypothesis needs checked sources and negative evidence.
7. Repair locally with the smallest change that preserves existing contracts. If the current head already contains the fix, prove it from code, tests, and commit state instead of changing files.
8. Verify with targeted regression first, then repo gates appropriate to the touched surface. Default to `git diff --check`, `make doctor`, `make lint`, and `make test` before claiming closure.
9. Distill the repair into the durable location: test, validator, skill prompt, decision note, or concise review artifact. Avoid raw timeline, raw model output, secret values, and session-only URLs.
10. After pushing verified fixes, reply to addressed review comments/threads with an evidence-bearing review response that names the fix, targeted verification, repo gates, commit or file refs, re-review request state, post-request readback state, and resolve decision; never reply only with "fixed" or "対応しました".
11. Request re-review by posting a PR comment addressed to Codex, normally `@codex review`; report the exact blocker if the PR cannot be updated from the current environment.
12. Re-read review threads and checks after the review request. Resolve only threads whose requested behavior is fixed, tested, and still non-outdated on the current PR.
13. Report reviewed head commit, posted PR comment state when applicable, resolved thread IDs, remaining open threads, verification commands, check state, `Prior Findings Closure Table`, `Failure Hypothesis Table`, `Review response summary`, and any evidence-bound unknowns.

## Closure Artifact

For non-trivial review feedback, keep a compact `PRReviewLifecycleAudit` in the PR notes, review artifact, or related docs. Use the schema in `references/review-cycle.md`.

## Guardrails

- Do not resolve GitHub review threads unless the user asked for resolve/closure or the requested lifecycle explicitly includes it.
- Do not treat a reply to addressed review comments or an `@codex review` request as thread resolution; resolution still requires fixed behavior, evidence, and a fresh thread-aware read.
- Do not let review replies hide lifecycle state. Each addressed comment needs an evidence-bearing review response, and if timing forces a pre-review reply, add a follow-up reply or PR-level `Review response summary` after `@codex review` and post-request readback.
- Do not submit approvals or request changes on your own work.
- Do not use unresolved thread count alone as the repair target; the target is the invariant behind the review.
- Keep this skill's `allowed-tools` aligned with the advertised repair workflow; do not remove write access unless the workflow becomes read-only.
- Do not ignore same-class risks. Classify each as fixed, tested, backlog with closure criterion, blocked, non-material with evidence, out-of-scope with evidence, or none found.
- Treat PR body, comments, executor self-scoring, and CI status as inputs, not closure evidence. `parent reducer must audit no-finding leaves`; source refs must show why each known finding and high-risk hypothesis is closed.
- `validators do not close semantic findings`; tests and checks are necessary but cannot substitute for output meaning, design-contract, runtime-config, or business-rule review.
- `existing implementation output semantics are protected`; require source-refed approval or explicit agreement override before changing output meaning or documenting it as a different behavior.
- When a run hands work to a target tmux pane, inherit `tmux-agent-review-loop` and its `references/tmux_handoff_protocol.md`; do not duplicate or bypass target pane resolution, target pane dirty-input classification, file handoff, `C-m` confirmation, non-converged stop reasons, lifecycle boundaries, or the no parent self-implementation rule.
- Treat placeholder, transcript, last-submitted prompt displays, and `idle_codex_surface` as non-dirty unless the current editable prompt area contains unsent text. Reuse the tmux stop reasons unchanged: `target_pane_unresolved`, `target_pane_input_dirty`, `handoff_unconfirmed`, `role_boundary_violation`, `target_pane_lifecycle_violation`, and `self_handoff_blocked`.
- Do not include raw prompt, raw model output, runtime logs, secrets, `.env*`, or session-only URLs in tracked artifacts or PR comments.

## References

- `references/review-cycle.md`
