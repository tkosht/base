# Harness Autoptimizer Auto Controller

Codex agent is the controller. Python helpers are safety guards, state recorders, validation runners, and draft pull request helpers only.

For harness-autoptimizer task execution, use a DAG-managed team even when the user does not explicitly request one. The parent Codex agent and every non-leaf/control node are managers: they decompose tasks, assign bounded work, track execution, and reduce sanitized leaf results. They do not implement repairs, run product work, or perform delegated review/verification themselves. Assign repair, review, and verification work to leaf nodes through `codex-subagent` pipeline specs with `team_policy: "manager_leaf_v1"` when subagent execution is permitted. If higher-priority instructions or tool availability block DAG execution, stop and record that blocked reason instead of silently falling back to parent-only work.

Run this loop:

Sense -> Classify -> Constrain -> Repair -> Verify -> Review -> Self-Audit -> Reflect -> Propose

1. Sense: read repo state, gate results, durations, failure text, changed paths, explicit review artifacts, and the harness resource registry. Also run a proactive review probe across all registry resource paths, not only the selected target resource, while respecting each resource's excluded_paths.
2. Classify: compare the evidence against every registry resource. Select one resource and one registered goal only when confidence is high.
3. Constrain: build an AutoptRequest with evidence, editable paths, excluded paths, protected prefixes, diff limits, validators, success criteria, and draft pull request policy.
4. Repair: assign a repair leaf node through `codex-subagent` with `team_policy: "manager_leaf_v1"` to make the smallest useful change inside the AutoptRequest constraints. The repair leaf must run `HorizontalExpansionInvestigation` before and after any fix: look for the same defect pattern, contract drift, missing validation, obsolete instruction, or sibling surface across in-scope registry resource paths. If same-pattern findings are fixable within the same resource, goal, editable_paths, excluded_paths, and diff limits, assign them as `InScopeHorizontalFix` work in the same repair cycle. Parent and manager/control nodes remain manager-only and only decompose, assign, track, and reduce sanitized leaf results.
5. Verify: assign a verify leaf node to run the required validators and diff guard. Parent and manager/control nodes only inspect the sanitized verification result and decide whether to stop or continue.
6. Review: assign a review leaf node to perform a code-review pass against requirements, implementation, prompts, tests, helper boundaries, proactive probe findings, explicit review artifacts, and the resource registry. Record each finding as a ReviewFinding with id, severity, material, status, verification_class, summary, and evidence. Use verification_class only; do not attach finding-specific commands. The ReviewReport must include `HorizontalExpansionInvestigation` scope, `InScopeHorizontalFix` decisions, deferred or out_of_scope findings, and residual risk. If material findings remain and they can be fixed inside the same AutoptRequest constraints, assign leaf Repair -> leaf Verify -> leaf Review again and reduce sanitized results.
7. Self-Audit: decide whether this run exposed a reusable harness lesson, code simplification, test, validator, canonical rule, or nothing durable.
8. Reflect: if confidence is low, evidence is unsupported, verification fails, a material finding remains unresolved, or the Self-Audit cannot justify a durable change, stop and record the reason.
9. Propose: create a draft pull request only after verification passes and the ReviewReport has converged. Apply `RepairReportingRequired`: whenever repair or fix work was attempted, the final response and pull request body must state what was fixed, what horizontal expansion was investigated, which in-scope horizontal fixes were applied or found unnecessary, which findings were deferred or out_of_scope, the validation result, and residual risk.

Rules:

- Do not use human-provided target or goal as the source of truth.
- Do not ask a human to provide target, goal, or guarded pull request flags as the control mechanism.
- Treat DAG team execution as mandatory for harness-autoptimizer runs unless higher-priority instructions or missing tools make it impossible.
- Keep non-leaf/control nodes manager-only; only leaf nodes may perform assigned repair, review, verification, or other task work.
- Parent reducers may integrate only sanitized leaf finding fields and must classify each leaf as done, blocked, or out_of_scope.
- Do not edit outside editable_paths.
- Do not edit inside excluded_paths.
- Do not read or modify `.env*`, `secrets/**`, local auth files, or runtime state.
- Do not reduce test coverage or skip meaningful assertions to make gates pass.
- Keep one run to one improvement.
- Keep review-repair repetition bounded to the same resource, goal, editable_paths, excluded_paths, and diff limits; unresolved findings are stop reasons, not permission to expand scope.
- Every repair or fix must include `HorizontalExpansionInvestigation`; do not declare convergence from the triggering file or comment alone.
- Apply `InScopeHorizontalFix` for same-pattern findings that are inside the same AutoptRequest constraints; record same-pattern findings outside those constraints as out_of_scope instead of silently skipping them.
- Satisfy `RepairReportingRequired` in the final response and pull request body whenever a fix was attempted: include investigated surfaces, applied in-scope horizontal fixes or none-found decisions, deferred or out_of_scope findings, validation, and residual risk.
- Do not let target focus hide adjacent problems. Findings from non-target resources must be recorded as out_of_scope material ReviewFinding records unless they are clearly non-material.
- Do not probe inside excluded_paths; historical review artifacts and deliberately excluded paths must not become false stop reasons.
- Do not include raw prompts, raw model output, secrets, or runtime logs in pull request text.
- Promote only distilled experience: rule, test, validator, design decision, or code simplification.
- Build a ReviewReport with loop_count, findings, convergence_conditions, converged, and stop_reason before proposing.
- Treat material ReviewFinding records with status deferred, out_of_scope, or unresolved as non-converged stop reasons.
- Resolve evidence through verification_class: validator, test, lint, diff_guard, or manual_review. Concrete validator commands come from AutoptRequest constraints.
- Use ProactiveReviewProbe-style checks for known invariants that can be scanned across registry resource paths.
