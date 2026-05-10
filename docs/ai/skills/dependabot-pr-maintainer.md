# dependabot-pr-maintainer

- Purpose: Dependabot が作成した Open Pull Request を点検し、競合解消、CI確認、適切なマージまで進める
- Use when: Dependabot の依存更新 PR を整理・対応・マージしたいとき
- Codex entrypoint: `.agents/skills/dependabot-pr-maintainer`
- Claude entrypoint: `.claude/skills/dependabot-pr-maintainer`
- Key outputs: initial_open_prs、merged_prs、updated_prs、skipped_prs、final_open_prs、local_notes
