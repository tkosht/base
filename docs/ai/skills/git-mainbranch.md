# git-mainbranch

- Purpose: PR マージ後に `main` / `master` へ戻し、同期と local branch cleanup を安全に行う
- Use when: `git-commit-pr` 後の後処理
- Codex entrypoint: `.agents/skills/git-mainbranch`
- Claude entrypoint: `.claude/skills/git-mainbranch`
- Key outputs: sync status、deleted branches、skipped branches
