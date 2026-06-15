# Review Artifact Template

```markdown
# <target> Review Round <N>

Target:

- Pane: `<pane-id>`
- Files: `<paths>`
- Reviewed state: `<commit/branch/status summary>`

## Findings

### 1. <severity>: <summary>

- Classification: `implementable | needs_user_decision | resolved | non_issue`
- Evidence: `<file:line, diff, command output, pane output>`
- Impact: `<why it matters>`
- Required action: `<specific fix or decision>`
- Verification: `<how to confirm>`

## Prior Findings Closure Table

| Prior item | Source refs | Current evidence | Status | Closing reviewer |
| --- | --- | --- | --- | --- |
| `<user/prior finding/probe>` | `<refs>` | `<evidence>` | `fixed/not_applicable/resolved/non_issue/needs_user_decision/unresolved` | `<reviewer>` |

## Failure Hypothesis Table

| Hypothesis | Checked sources | Negative evidence | Residual risk |
| --- | --- | --- | --- |
| `semantic output / implementation compatibility / aggregation / deduplication / boundary / approval-dependent decision` | `<refs>` | `<evidence>` | `<risk or none>` |

## User Decisions Required

- `<none>` or `<decision item with options/context>`

## Expected Actions For Target Pane

- `<specific edits>`
- `<specific gates>`
- `<specific git status/staging expectation>`

## Reviewer Follow-Up

- Re-review changed diff.
- Confirm gates.
- Confirm `git status --short`.
- Mark findings resolved / remaining / needs_user_decision.
```

## Writing Rules

- Keep findings first.
- `no material findings requires negative evidence`: when there are no material findings, keep the `Failure Hypothesis Table` and cite source refs.
- `parent reducer must audit no-finding leaves`; do not treat executor self-scoring as closure evidence.
- `validators do not close semantic findings`; gates do not replace output-meaning or design-contract review.
- `existing implementation output semantics are protected`; require source-refed approval or agreement override before changing output meaning.
- Do not include raw secrets, raw model output, huge logs, or unrelated diff.
- Use concrete file paths and line references when available.
- Avoid ambiguous requests such as "いい感じに直す".
- If the finding is really a product requirement question, classify it as `needs_user_decision`.
