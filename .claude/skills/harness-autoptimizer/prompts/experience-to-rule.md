# Experience-to-Rule

All Codex agents in this repo may produce useful experience. The optimizer's
job is to decide what survives.

Use this retention ladder:

1. Discard when the event is one-off, unverifiable, already covered, or would
   only add instruction noise.
2. Keep as sanitized non-tracked state when the signal is plausible but not yet
   general enough.
3. Retain as code simplification when the lesson is that implementation shape
   became too complex.
4. Retain as a test or validator when executable verification can prevent the
   failure better than prose.
5. Retain as a skill prompt when the behavior is specific to a skill workflow.
6. Retain as a canonical rule only when it affects repo-wide Codex behavior.
7. Retain as a design decision when future maintainers need the reason for a
   placement or authority choice.

Before promoting a rule, check:

- Scope: exactly which agents or tasks it affects.
- Authority: which file is canonical and which files are adapters.
- Trigger: when the rule should be used.
- Expected behavior: what the agent should do differently.
- Validation: which test, validator, or probe can catch regression.
- Retirement: when the rule should be removed or demoted.

Prefer deleting or simplifying an existing rule over adding a new one when the
same behavior can be preserved with less always-loaded context.
