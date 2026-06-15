# harness-autoptimizer

- Purpose: Codex agent が repo-local harness resource と repo-wide experience capture を診断・分類・制約化・検証し、通常ゲート通過時だけ小粒 draft pull request へまとめる
- Use when: slow / failing gates、Codex agent control loop、Codex experience capture、harness resource registry、Markdown docs / settings / validation surface の自己最適化設計や実行
- Skill source: `.agents/skills/harness-autoptimizer`
- Claude shim: `.claude/skills/harness-autoptimizer`
- Key outputs: AutoptRequest、ProactiveReviewProbe、ReviewFinding、ReviewReport、ExperienceCandidate、ExperienceAssessment、sanitized run state、diff guard result、gate results、draft pull request URL
- Notes: 自律判断の主体は Codex agent。Python helper は prompt assembly、sanitized state、diff guard、検証実行、draft pull request 補助に限定する
- Notes: 実行タスクは DAG team 必須。親 Codex agent と非 leaf / control node は manager-only とし、実作業は `team_policy: "manager_leaf_v1"` の leaf node に委譲する
- Notes: review leaf は `Prior Findings Closure Table` と `Failure Hypothesis Table` を使い、no material findings requires negative evidence、parent reducer must audit no-finding leaves、validators do not close semantic findings、existing implementation output semantics are protected、meaning-first repair、Context Reconstruction Table、needs_user_decision を守る
- Sanitized feedback: `docs/architecture/decision-records/2026-05-06-harness-autoptimizer-downstream-feedback.md` records a generic base-level transfer backlog from an applied repository. Move generic convergence artifacts and policy-pack boundaries into base, but keep product-specific probes out of base core.
- Prompt entrypoints: `.agents/skills/harness-autoptimizer/prompts/auto-controller.md`、`.agents/skills/harness-autoptimizer/prompts/self-audit.md`、`.agents/skills/harness-autoptimizer/prompts/experience-to-rule.md`、`.agents/skills/harness-autoptimizer/prompts/repair-request.md`、`.agents/skills/harness-autoptimizer/prompts/harness-contracts.md`
