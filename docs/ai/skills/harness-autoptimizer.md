# harness-autoptimizer

- Purpose: Codex agent が repo-local harness resource と repo-wide experience capture を診断・分類・制約化・検証し、通常ゲート通過時だけ小粒 draft pull request へまとめる
- Use when: slow / failing gates、Codex agent control loop、Codex experience capture、harness resource registry、Markdown docs / settings / validation surface の自己最適化設計や実行
- Codex entrypoint: `.agents/skills/harness-autoptimizer`
- Claude entrypoint: `.claude/skills/harness-autoptimizer`
- Key outputs: AutoptRequest、ProactiveReviewProbe、ReviewFinding、ReviewReport、ExperienceCandidate、ExperienceAssessment、sanitized run state、diff guard result、gate results、draft pull request URL
- Notes: 自律判断の主体は Codex agent。Python helper は prompt assembly、sanitized state、diff guard、検証実行、draft pull request 補助に限定する
- Downstream feedback: `docs/architecture/decision-records/2026-05-06-harness-autoptimizer-downstream-feedback.md` records the next base-level transfer backlog. Move generic convergence artifacts and policy-pack boundaries into base, but keep downstream product probes out of base core.
- Prompt entrypoints: `.claude/skills/harness-autoptimizer/prompts/auto-controller.md`、`.claude/skills/harness-autoptimizer/prompts/self-audit.md`、`.claude/skills/harness-autoptimizer/prompts/experience-to-rule.md`、`.claude/skills/harness-autoptimizer/prompts/repair-request.md`
