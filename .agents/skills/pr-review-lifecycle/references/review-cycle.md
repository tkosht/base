# PR Review Lifecycle Reference

## When To Use

Use this process when a user asks for any of these outcomes:

- address PR review feedback
- review PR contents and report findings
- post a top-level PR Conversation review summary
- hand PR findings to a tmux target pane
- review the response to feedback
- ask Codex or another reviewer to re-review
- close or resolve GitHub review threads
- run the whole cycle until no actionable review thread remains

This process can work with the GitHub plugin, `gh`, or both. Thread state must come from a thread-aware source such as `reviewThreads` GraphQL data or the GitHub plugin review-thread tool.

If the lifecycle is coordinated through a target tmux pane, use `tmux-agent-review-loop` / `references/tmux_handoff_protocol.md` as the authoritative handoff contract. This PR lifecycle remains responsible for review state, `RootCauseReview`, regression and gates, and evidence-bound resolve decisions; the tmux protocol owns target pane resolution, target pane dirty-input classification, file handoff, `C-m` confirmation, non-convergence stop reasons, pane lifecycle boundaries, and reviewer/coordinator role boundaries.

## Evidence Order

Prefer evidence in this order:

1. Current user instruction and PR URL or branch.
2. Local git state and current source.
3. PR head/base, commits, changed files, checks, deployment comments, and thread-aware review state.
4. Targeted failing or regression test.
5. Full local gates and remote check status.
6. Official tool contract or primary documentation only when GitHub or hosting behavior is uncertain.

Flat PR comments are not enough for closure because they do not prove thread resolution state.

## Cycle

1. Sense
   - Run `git status --short --branch`.
   - Resolve PR head, base, URL, draft state, review decision, check state, and deployment status.
   - Fetch review threads with `isResolved`, `isOutdated`, `path`, `line`, comment body, and URL.

2. Classify
   - Group unresolved threads by behavior, not only by file.
   - Classify each as actionable, already fixed on head, outdated, duplicate, informational, blocked, or out-of-scope.
   - If a review comment points at a symptom, name the invariant that failed.
   - For review-only requests, review the current diff findings first and anchor the result to the reviewed head commit. Do not approve, request changes, or post to GitHub unless the user requested that action.
   - For requested GitHub feedback, post a concise top-level PR Conversation comment that names the reviewed head, findings, checked evidence, and residual risk. Do not include secrets, raw logs, raw model output, or long diff excerpts.

3. Root Cause
   - Record why the previous implementation and tests allowed the issue.
   - Identify the bypass scenario or reproduction.
   - Sweep same-class surfaces, especially public conversion, data-write, runtime config, external deployment lifecycle, security, privacy, and operational observability.
   - Keep a `Prior Findings Closure Table` for previous review findings, PR comments, user corrections, and proactive probe findings. A known item remains open until it is fixed, not_applicable, resolved, non_issue, or needs_user_decision with source refs.
   - Keep a `Failure Hypothesis Table` for semantic output, existing implementation compatibility, aggregation, deduplication, boundary, runtime/config, data-write, and approval-dependent risks. `no material findings requires negative evidence`.
   - `parent reducer must audit no-finding leaves`: self-scoring, green checks, or a small diff are review inputs, not closure evidence.
   - `validators do not close semantic findings`: tests and checks do not replace output-meaning, design-contract, runtime-config, or business-rule review.
   - `existing implementation output semantics are protected` unless source-refed approval or explicit agreement override authorizes the change.

4. Repair
   - Add or update the regression before or with the fix when feasible.
   - Keep the change traceable to the review cluster.
   - Preserve existing public behavior unless the review explicitly requires a change and the contract supports it.

5. Verify
   - Run the narrow test that proves the reviewed behavior.
   - Run `git diff --check`.
   - Run `make doctor`, `make lint`, and `make test` unless the task scope or environment makes a gate impossible. If a gate is skipped, record the reason and residual risk.
   - Check remote PR checks after pushing or after the user asks for review status.

6. Distill
   - Keep the durable invariant in the smallest useful place: regression test, validator, skill prompt, decision record, or review artifact.
   - Do not save raw thread dumps, raw command logs, secrets, or session-only URLs.

7. Tmux Handoff, when applicable
   - Before sending work to a target pane, follow the tmux handoff protocol instead of implementing an ad hoc paste flow.
   - placeholder, transcript, last-submitted prompt displays, and `idle_codex_surface` are non-dirty by themselves; only unsent text in the current editable prompt area is dirty.
   - Use the helper classification when available, including `pending_handoff_notice`, `self_handoff_blocked`, `user_confirmed_idle`, and `handoff_enter_retry_sent`.
   - Stop as non-converged with the protocol reason, such as `target_pane_unresolved`, `target_pane_input_dirty`, `handoff_unconfirmed`, `role_boundary_violation`, `target_pane_lifecycle_violation`, or `self_handoff_blocked`, instead of self-implementing the target pane's repair.

8. Review Request
   - Re-request review only after the PR contains the fix and local evidence is green.
   - After pushing verified fixes, reply to addressed review comments or threads with an evidence-bearing review response. A useful reply names the fix, targeted verification, repo gates, commit or file refs, re-review request state, post-request readback state, and resolve decision.
   - Do not reply only with "fixed", "done", or "対応しました". If the reply happens before `@codex review` or before readback, add a follow-up thread reply or PR-level `Review response summary` after the review request and readback so reviewers can see that re-review was actually requested and checked.
   - Post a PR comment addressed to Codex, normally `@codex review`, to request re-review.
   - Re-read review threads and checks after the review request before resolving anything.
   - Use the repo's established mechanism, such as marking a draft ready, pushing to update checks, requesting a reviewer, or posting the minimal accepted trigger comment.
   - If the review mechanism is unknown or write-sensitive, ask before posting.

9. Resolve
   - Re-fetch thread state after the final pushed head.
   - Resolve only threads that are fixed or proven already fixed, have evidence, and are still the intended thread.
   - Do not resolve a material thread just because checks are green.

10. Report
   - List reviewed head commit, posted PR comment state when applicable, fixed clusters, unresolved clusters, resolved thread IDs or URLs, verification commands, remote check state, and blockers.
   - Include a `Review response summary` mapping each addressed comment/thread to its reply URL, fix evidence, verification, re-review request, post-request readback, and resolve state.
   - Mention local unrelated changes separately so they are not confused with the PR repair.

## Review Comment Response Template

Use this compact shape for each addressed review comment or thread. Keep it concise, but keep lifecycle state visible:

```markdown
対応しました。

- Fix: <file/commit refs and behavior changed or already proven fixed>
- Verification: <targeted test and required gates>
- Re-review request: <`@codex review` URL/status or blocker>
- Post-request readback: <threads/checks reread result or not-yet-done reason>
- Resolve state: <resolved / left open with reason / blocked>
```

When multiple comments are handled together, add a PR-level `Review response summary` table and link it from individual replies if needed.

## PRReviewLifecycleAudit

Use this compact artifact for non-trivial cycles:

```markdown
## PRReviewLifecycleAudit

- PR: <owner/repo#number or URL>
- Head/base: <head> -> <base>
- Review threads checked: <count>; unresolved actionable at start: <count>
- Target cognition: <what the reviewer/user needed to trust>
- Metacognition: <what could make the agent falsely claim done>
- Abstract-concrete shuttle: <invariant> -> <specific failing path/test/comment>
- RootCauseReview:
  - missed_invariant: <text>
  - why_existing_checks_passed: <text>
  - same_class_risk_sweep: <paths/surfaces>
  - same_class_dispositions: <fixed/tested/backlog/blocked/non-material/out-of-scope/none_found>
- Prior Findings Closure Table: <items/status/source refs>
- Failure Hypothesis Table: <hypotheses/checked sources/negative evidence/residual risk>
- Repair evidence: <files or commit>
- Verification:
  - targeted: <command/result>
  - repo_gates: <commands/results>
  - remote_checks: <checks/results or not checked reason>
- Review request: <mechanism/result or not requested reason>
- Addressed comment replies: <comment/thread replies posted after pushing, with evidence refs or blocker>
- Codex review request: <`@codex review` PR comment URL/result or blocker>
- Post-request readback: <review threads and checks reread result>
- Review response summary: <comment/thread -> reply URL, fix, verification, re-review request, post-request readback, resolve state>
- Tmux handoff: <target pane/protocol result/non-convergence reason or not applicable>
- Resolve:
  - resolved_threads: <ids/urls>
  - remaining_threads: <ids/urls and reason>
- DistillationReview: <test/validator/skill/doc location or no-op reason>
- Evidence quarantine: <raw logs/secrets/session URLs excluded>
```

## Resolve Decision Table

| Thread state | Code state | Verification | Action |
| --- | --- | --- | --- |
| unresolved and actionable | not fixed | missing or failing | repair, do not resolve |
| unresolved and actionable | fixed on current head | targeted and required gates pass | resolve |
| unresolved but outdated | superseded by diff | current behavior verified | leave or note as outdated depending on repo practice |
| unresolved but informational | no behavior request | not applicable | leave or resolve only if repo convention allows |
| unresolved and blocked | fix requires external/user action | blocker documented | do not resolve |

## MemoryDisciplineReview

- Scope: this skill stores a reusable PR review lifecycle, not the raw PR #79 timeline.
- Index/body boundary: `SKILL.md` is the trigger and short workflow; this reference holds the detailed procedure and artifact schema.
- Authority boundary: this skill is a hint surface. Current PR state, local source, test output, and GitHub thread state remain authoritative.
- Freshness verification: re-read PR threads and checks every run before resolving anything.
- Security quarantine: never retain secrets, raw logs, `.env*`, raw model output, or session-only URLs.
- Prune policy: if repo practice for review requests or thread resolution changes, update the workflow and remove obsolete mechanisms.
