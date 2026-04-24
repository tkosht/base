# harness-autoptimizer

- Purpose: repo-local harness resource を worktree 上で自己最適化し、通常ゲート通過時だけ小粒 pull request へまとめる
- Use when: `codex-subagent` の安定性改善、harness resource registry の確認、docs / settings / validation surface へ自己最適化対象を広げる設計や実行
- Codex entrypoint: `.agents/skills/harness-autoptimizer`
- Claude entrypoint: `.claude/skills/harness-autoptimizer`
- Key outputs: run state、diff guard result、gate results、pull request URL
- Notes: v1 の既定 target は `codex-subagent`、goal は `stability`、candidate は 1 件だけ
