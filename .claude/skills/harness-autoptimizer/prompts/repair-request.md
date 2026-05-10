# Harness Autoptimizer Repair Request

Use the AutoptRequest as the binding instruction for this repair.

Required behavior:

- Treat classification as the Codex agent's evidence-based decision, not as a human override.
- Review explicit review artifacts and run proactive probes across all registry resource paths before deciding the run has converged. Respect each resource's excluded_paths while probing.
- Do not edit outside editable_paths.
- Do not edit inside excluded_paths.
- Respect max_changed_files and max_changed_lines.
- Run every validator listed in validators.
- Stop if the evidence does not justify the selected resource and goal.
- Stop if the change would require touching protected prefixes.
- Create only a draft pull request after all validation passes.
- After validation, run a self-review pass against the AutoptRequest, requirements, implementation, prompts, tests, helper boundaries, proactive probe findings, explicit review artifacts, and resource registry. Record each item as a ReviewFinding with id, severity, material, status, verification_class, summary, and evidence. If material findings can be fixed inside the same constraints, repair them and rerun validation.
- Build a ReviewReport with loop_count, findings, convergence_conditions, converged, and stop_reason before proposing. Use verification_class only; do not attach finding-specific commands. Concrete commands come from validators and diff guard.
- Record non-target resource findings as out_of_scope material ReviewFinding records instead of silently ignoring them.
- Do not probe inside excluded_paths; historical review artifacts and deliberately excluded paths must not become false stop reasons.
- After verification, run the Self-Audit retention decision. Promote only distilled experience, never raw traces.

The repair is successful only when every success criterion in the AutoptRequest is satisfied.
It is not successful when the ReviewReport is not converged.
