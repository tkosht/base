# Harness Autoptimizer Repair Request

Use the AutoptRequest as the binding instruction for this repair.

Required behavior:

- Treat classification as the Codex agent's evidence-based decision, not as a human override.
- Do not edit outside editable_paths.
- Do not edit inside excluded_paths.
- Respect max_changed_files and max_changed_lines.
- Run every validator listed in validators.
- Stop if the evidence does not justify the selected resource and goal.
- Stop if the change would require touching protected prefixes.
- Create only a draft pull request after all validation passes.
- After validation, run a self-review pass against the AutoptRequest, requirements, implementation, prompts, tests, helper boundaries, and resource registry. If material findings can be fixed inside the same constraints, repair them and rerun validation.
- After verification, run the Self-Audit retention decision. Promote only distilled experience, never raw traces.

The repair is successful only when every success criterion in the AutoptRequest is satisfied.
