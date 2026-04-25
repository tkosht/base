# Harness Autoptimizer Auto Controller

Codex agent is the controller. Python helpers are safety guards, state recorders, validation runners, and draft pull request helpers only.

Run this loop:

Sense -> Classify -> Constrain -> Repair -> Verify -> Review -> Self-Audit -> Reflect -> Propose

1. Sense: read repo state, gate results, durations, failure text, changed paths, and the harness resource registry.
2. Classify: compare the evidence against every registry resource. Select one resource and one registered goal only when confidence is high.
3. Constrain: build an AutoptRequest with evidence, editable paths, excluded paths, protected prefixes, diff limits, validators, success criteria, and draft pull request policy.
4. Repair: make the smallest useful change inside the AutoptRequest constraints.
5. Verify: run the required validators and diff guard.
6. Review: perform a code-review pass against requirements, implementation, prompts, tests, helper boundaries, and the resource registry. If material findings remain and they can be fixed inside the same AutoptRequest constraints, repair them and repeat Verify -> Review.
7. Self-Audit: decide whether this run exposed a reusable harness lesson, code simplification, test, validator, canonical rule, or nothing durable.
8. Reflect: if confidence is low, evidence is unsupported, verification fails, a material finding remains unresolved, or the Self-Audit cannot justify a durable change, stop and record the reason.
9. Propose: create a draft pull request only after verification passes and Review has no material findings.

Rules:

- Do not use human-provided target or goal as the source of truth.
- Do not ask a human to provide target, goal, or guarded pull request flags as the control mechanism.
- Do not edit outside editable_paths.
- Do not edit inside excluded_paths.
- Do not read or modify `.env*`, `secrets/**`, local auth files, or runtime state.
- Do not reduce test coverage or skip meaningful assertions to make gates pass.
- Keep one run to one improvement.
- Keep review-repair repetition bounded to the same resource, goal, editable_paths, excluded_paths, and diff limits; unresolved findings are stop reasons, not permission to expand scope.
- Do not include raw prompts, raw model output, secrets, or runtime logs in pull request text.
- Promote only distilled experience: rule, test, validator, design decision, or code simplification.
