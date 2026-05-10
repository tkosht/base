# git-mainbranch

- Purpose: PR マージ後に `main` / `master` へ戻し、同期、不要 worktree cleanup、local branch cleanup を安全に行う
- Use when: `git-commit-pr` 後の後処理
- Skill source: `.agents/skills/git-mainbranch`
- Claude shim: `.claude/skills/git-mainbranch`
- Key outputs: sync status、removed worktrees、skipped worktrees、deleted branches、force deleted branches、force delete candidates、skipped branches
