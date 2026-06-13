# Harness Autoptimizer Repair Request

Use the AutoptRequest as the binding instruction for this repair.

Required behavior:

- Treat classification as the Codex agent's evidence-based decision, not as a human override.
- Execute harness-autoptimizer work through a DAG-managed team even when the user did not request subagents. Use `codex-subagent` pipeline specs with `team_policy: "manager_leaf_v1"` when subagent execution is permitted.
- Keep the parent Codex agent and every non-leaf/control node manager-only: decompose, assign, track, and reduce sanitized leaf results, but do not perform delegated repair, review, verification, or product work directly.
- Stop and record a blocked reason if higher-priority instructions or missing tools make mandatory DAG execution impossible.
- Review explicit review artifacts and run proactive probes across all registry resource paths before deciding the run has converged. Respect each resource's excluded_paths while probing.
- Run `HorizontalExpansionInvestigation` before and after any repair or fix. Investigate same defect pattern, contract drift, missing validation, obsolete instruction, and sibling surfaces across in-scope registry resource paths, while respecting editable_paths, excluded_paths, protected prefixes, and diff limits.
- Apply `InScopeHorizontalFix` for same-pattern findings that are inside the same AutoptRequest resource / goal / constraints. Do not leave in-scope horizontal fixes for a later follow-up merely because they were not the triggering issue.
- Record same-pattern findings outside the AutoptRequest constraints as out_of_scope ReviewFinding records with residual risk instead of silently ignoring them.
- Do not edit outside editable_paths.
- Do not edit inside excluded_paths.
- Respect max_changed_files and max_changed_lines.
- Run every validator listed in validators.
- Stop if the evidence does not justify the selected resource and goal.
- Stop if the change would require touching protected prefixes.
- Create only a draft pull request after all validation passes.
- After validation, run a self-review pass against the AutoptRequest, requirements, implementation, prompts, tests, helper boundaries, proactive probe findings, explicit review artifacts, and resource registry. Record each item as a ReviewFinding with id, severity, material, status, verification_class, summary, and evidence. If material findings can be fixed inside the same constraints, repair them and rerun validation.
- Build a ReviewReport with loop_count, findings, convergence_conditions, converged, and stop_reason before proposing. Use verification_class only; do not attach finding-specific commands. Concrete commands come from validators and diff guard.
- Include `HorizontalExpansionInvestigation` scope, `InScopeHorizontalFix` decisions, deferred or out_of_scope findings, validation, and residual risk in the ReviewReport.
- Record non-target resource findings as out_of_scope material ReviewFinding records instead of silently ignoring them.
- Do not probe inside excluded_paths; historical review artifacts and deliberately excluded paths must not become false stop reasons.
- After verification, run the Self-Audit retention decision. Promote only distilled experience, never raw traces.

The repair is successful only when every success criterion in the AutoptRequest is satisfied.
It is not successful when the ReviewReport is not converged.
If any repair or fix was attempted, `RepairReportingRequired` applies: the final response and pull request body must state what was fixed, what horizontal expansion was investigated, which in-scope horizontal fixes were applied or found unnecessary, which findings were deferred or out_of_scope, validation results, and residual risk.
