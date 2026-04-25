# Harness Self-Audit

Self-Audit is not a checklist of named failures. It is a retention decision:
whether this task experience should change future Codex behavior in this repo.

Ask this after meaningful task execution, user correction, gate failure,
unexpected complexity, or instruction conflict:

> Can this experience be compressed into a durable change that makes future
> Codex agents simpler, more consistent, safer, or more autonomous?

Evaluate these dimensions:

- Simplicity: did the implementation add parameters, branches, state, or
  ownership boundaries that can be removed?
- Autonomy: did the process rely on a human choosing target, goal, mode, or
  recovery policy that the Codex agent should infer from evidence?
- Authority: did two instruction surfaces, Markdown files, prompts, or helpers
  disagree about who controls the task?
- Retention: is the lesson likely to recur, high impact, general enough,
  verifiable, and worth its context cost?
- Placement: is the best retention form code simplification, test, validator,
  skill prompt, canonical rule, design decision, non-tracked state, or discard?

Do not promote raw traces. Raw prompts, raw model output, secrets, runtime logs,
and one-off task details must not become tracked knowledge.

If the evidence is weak, keep only a sanitized state summary or discard it.
