# Harness Autoptimizer Downstream Feedback

- Status: Proposed
- Date: 2026-05-06
- Source: downstream `tkosht/corporate_site` harness-autoptimizer evolution after base PR #68

## Context

Base PR #68 moved the first repo-specialization feedback into this template:
`ReviewFinding`, `ProactiveReviewProbe`, `ReviewReport` convergence, PR creation
gating, and the `repo-template-specializer` skill.

The downstream corporate-site repo continued using `harness-autoptimizer` after
that merge. Several later incidents exposed a deeper lesson: the useful feedback
is not the corporate-site content itself. The base-level value is the control
system that prevents a Codex agent from treating prose guidance, local patches,
or convenient tools as proof of convergence.

This record is intentionally sanitized. It does not retain raw conversation,
raw model output, connector output, runtime logs, secrets, dashboard exports, or
session-only URLs.

## Essence

Move the generic controller contract into base. Do not move downstream product
knowledge into base.

Base should own:

- evidence-based resource classification and `AutoptRequest` constraints
- protected paths, diff guard, validators, and PR gating
- structured convergence artifacts, not prose-only requirements
- route and authority audit before tool or subagent evidence is used
- root-cause review before PR-comment or user-correction repair
- evidence quarantine for forbidden, failed, raw, or secret-bearing routes
- DAG-managed leaf subagent orchestration for deep investigation
- post-verify distillation before completion or pull request creation
- memory discipline for experience retention
- sanitized incident review records for high-impact harness failures
- configurable review-artifact contracts where code checks structure and the
  prompt or policy owns the review vocabulary

Base should not own:

- AGen Innoventoria identity, Nova role wording, or site-renewal documentation
- Astro public-route path lists, AGen public-copy slugs, or company research
  requirements
- D1 contact-funnel schema, Resend, Turnstile, Cloudflare Pages, R2, Wix,
  Squarespace, Search Console, Bing Webmaster Tools, IndexNow, or domain-specific
  probes as core behavior
- downstream route counts, sitemap identities, private operations state, or
  provider dashboard handoff details

## Transfer Candidates

### 1. Convergence Artifact Model

Add base-owned artifacts that `ReviewReport` can require:

- `ToolRouteAudit`: authority resolution, allowed routes, forbidden routes,
  actual routes, fallback, and pass/fail result
- `RootCauseReview`: trigger source, missed invariant, bypass scenario, prior
  coverage gap, local-versus-architectural scope, verification target, retention
  surface, same-class risk sweep, same-class dispositions, and material finding
  ids
- `EvidenceQuarantine`: route, reason, sanitized evidence summary, reacquisition
  target, and resolved state
- `EssenceReviewLeaf`: approved local subagent route, sandbox, context packet,
  reducer fields, quarantine policy, and done/blocked/out-of-scope status
- `DistillationReview`: what was concentrated, what invariant was preserved,
  quality or performance evidence, and why no further distillation is safe
- `MemoryDisciplineReview`: scope, index/body boundary, write gate, freshness
  verification, authority boundary, security quarantine, and prune policy
- `SessionLessonSweepReview`: sanitized counts, source digest, signal kinds,
  purpose essence, constraint essence, target cognition, metacognition,
  abstract-concrete shuttle, candidate dispositions, DAG leaf status, reducer
  summary, and prompt-to-artifact checklist
- `LifecycleInventoryReview`: generic external lifecycle state machine for
  configured, reflected, rebuilt, uploaded, promoted, routed, smoked, and
  observed states

Acceptance:

- A harness self-improvement run without a passing `ToolRouteAudit` cannot
  converge.
- A PR-comment or user-correction repair without a complete `RootCauseReview`
  cannot converge.
- Unresolved `EvidenceQuarantine` records are material findings.
- Required `DistillationReview`, `MemoryDisciplineReview`,
  `SessionLessonSweepReview`, or `LifecycleInventoryReview` records block
  convergence when missing or incomplete.

### 2. Artifact Requirements Derived From Run Context

The current base helper relies on caller-provided context for many decisions.
Base should derive required artifacts from trigger source, changed resource,
task class, tool route usage, feedback classification, and review-artifact
policy where possible.

Acceptance:

- `harness-autoptimizer` changes automatically require `ToolRouteAudit` and
  `DistillationReview`.
- PR-comment and user-correction repairs automatically require
  `RootCauseReview`.
- Deep investigation, ambiguity resolution, or overlapping write scope requires
  a `SubagentDAGPlan`.
- Experience retention requires `MemoryDisciplineReview`.

### 3. DAG-Managed Subagent Orchestration

Base should keep the parent Codex agent as controller. Subagents are leaves, not
an alternate source of truth.

Acceptance:

- Deep investigation, exhaustive review, root-cause analysis, essence extraction,
  or improvement-cycle strengthening triggers a DAG-managed leaf plan.
- Overlap risk is handled with separate worktrees, disjoint write roots,
  read-only reviewer leaves, serial writer leaves, or blocked dependencies.
- Ambiguity is split into evidence-bound unknowns; repo-answerable unknowns can
  go to read-only leaves, while user-intent unknowns are asked explicitly.
- Parent reducer integrates only sanitized finding fields and classifies each
  leaf as done, blocked, or out of scope.

### 4. Tool-Route Authority And Evidence Quarantine

Base should make route choice auditable before a tool or delegated review can
influence repair.

Acceptance:

- Actual tool routes are structured, not only substring-matched prose.
- Forbidden connector, tool-discovery, or subagent routes fail the audit unless a
  higher-priority instruction explicitly permits them.
- Invalid-route evidence must be reacquired through an allowed route before it
  can support a finding.
- Explanatory text mentioning a forbidden route does not itself fail; actual
  route records do.

### 5. Prompt-Owned Review Vocabulary

The middle layer between semantic judgment and static schema is artifact
integrity. Code should verify that a review artifact is tied to the authoritative
prompt or policy catalog without deciding semantic quality.

Acceptance:

- Unknown or typoed review slugs fail as artifact integrity gaps.
- Adding a new prompt-owned slug does not require editing a duplicated Python
  enum.
- Code validates marker, required fields, reviewed sources, unchecked surfaces,
  runtime or implementation evidence, and unresolved material findings.
- Code does not require all semantic slugs and does not judge which checks apply.

### 6. Policy-Pack Boundary

Base should separate core harness logic from downstream policy packs.

Core base:

- resource registry schema
- protected path and diff guard
- convergence artifacts and `ReviewReport`
- sanitized state and report serialization
- generic review-artifact contract mechanism
- adapter and skill layout validation
- doctor/lint/test validator vocabulary

Downstream policy:

- public-copy target profile
- trigger paths
- required source list
- review slug catalog
- provider-specific lifecycle probes
- app-specific resources and retained harness set

Acceptance:

- The base package works in a repository with no `docs/site-renewal`, no Astro
  app, and no Cloudflare configuration.
- Domain literals such as `agen-i`, `Cloudflare`, `Resend`, `D1`,
  `Search Console`, or route names are absent from base core tests except inside
  examples that are explicitly marked as downstream policy.

### 7. Resource Registry Schema Hardening

The base registry should validate more than TOML shape.

Acceptance:

- `id`, `kind`, `authority`, `paths`, `mutable_paths`, and `validators` are
  non-empty.
- `depends_on` references existing resource ids.
- `mutation_policy` and `risk_level` use known enums.
- `mutable_paths` are a subset of known paths unless an explicit override is
  documented.
- validators use registered command vocabulary, normally `make doctor`,
  `make lint`, and `make test`.
- global and resource-level protected prefixes are supported.

### 8. Sanitized State And Memory Discipline

Base should treat memory as a hint surface, not authority.

Acceptance:

- raw prompt, raw model output, stdout/stderr, runtime logs, connector output,
  secrets, auth state, and session-only URLs cannot enter retained knowledge,
  PR bodies, review reports, or serialized state.
- session-history sweeps may read local session files only through an allowlist
  and may persist only counts, digests, signal kinds, and sanitized dispositions.
- experience retention uses a no-op default unless scope, verification target,
  retention surface, and prune policy are explicit.

## Non-Transfer Items

Keep these out of base core:

- corporate-site public-copy slug list and AGen-specific review vocabulary
- exact route names, sitemap URL set, trailing-slash policy, and indexing handoff
  state
- contact form D1 tables, reporting query shapes, and Resend email behavior
- Cloudflare Pages project names, Workers/D1/R2 settings, Turnstile, Wix, and
  Squarespace operational notes
- downstream `.codex`, `.claude`, `.cursor`, and retained-harness naming history
- generated repo clean-up findings that are already template-specific history,
  except as examples for `repo-template-specializer`

## Implementation Backlog

1. Add the artifact dataclasses and completeness predicates.
2. Extend `ReviewRunContext` or replace it with derived artifact requirements.
3. Make `build_review_report()` apply all artifact requirements before checking
   convergence.
4. Add tests that every required artifact blocks convergence when missing,
   incomplete, or contradicted by material findings.
5. Add `ToolRouteAudit` structured route records and forbidden evidence
   quarantine tests.
6. Add `SubagentDAGPlan` tests for deep investigation, overlap risk, and
   ambiguity.
7. Add `DistillationReview` tests that produce `distillation pass missing` and
   `distillation evidence missing` stop reasons.
8. Add `ReviewArtifactContract` so downstream prompts can own vocabulary and
   path/source policy.
9. Split core probes from downstream policy probes.
10. Harden registry schema validation and protected-prefix configuration.
11. Add adapter sync tests for `.claude/skills`, `.agents/skills`, and
    `.codex/skills`.
12. Add a downstream migration checklist covering identity surfaces, retained
    harness selection, policy-pack configuration, registry updates, validators,
    and unknowns.

## Verification Targets

The base implementation is not complete until these checks exist:

- missing `ToolRouteAudit` blocks harness self-improvement convergence
- forbidden route evidence creates unresolved material `EvidenceQuarantine`
- missing `RootCauseReview` blocks PR-comment and user-correction repair
- same-class material findings must have matching `ReviewFinding` ids and
  statuses
- parent-only essence inference fails when a dedicated read-only leaf is required
- missing `SubagentDAGPlan` blocks deep investigation convergence
- missing or evidence-free `DistillationReview` blocks convergence
- missing `MemoryDisciplineReview` blocks memory-related convergence
- missing `LifecycleInventoryReview` blocks external lifecycle completion claims
- prompt-owned slug derivation rejects unknown values without duplicating the
  slug catalog in code
- base core tests pass without downstream site-renewal, Astro, or Cloudflare
  files

## Current Known Gap

As of this record, base `main` contains the PR #68 generation of
`harness-autoptimizer`, but does not contain the downstream artifact model and
policy-pack boundary described here. This record is a feedback handoff, not a
claim that the transfer is implemented.
