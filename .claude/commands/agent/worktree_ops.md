# worktree_ops — Git worktree 運用タスク

目的: 複数エージェントを安全に並列実行するための標準手順を提供します。

## 前提
- `git worktree` 利用可能
- `.agent/` は各 worktree で独立運用（共有禁止）

## 作成
```bash
mkdir -p ../worktrees
# ベースは develop
git checkout develop

# 新規ブランチ & worktree 追加
BR=feature/agent-a
 git branch "$BR"
 git worktree add ../worktrees/agent-a "$BR"
```

## 一覧
```bash
git worktree list
```

## 削除（安全）
```bash
git worktree remove ../worktrees/agent-a
# ブランチも不要なら
git branch -D feature/agent-a
```

## 初期化
```bash
# 各 worktree で一度だけ
bash ./.cursor/commands/agent/agent_init.md
```

## ベストプラクティス
- 同一 worktree 内の併走は非推奨。やむを得ず同居する場合は `task_id` 毎に WM/ログ/成果物パスを完全分離
- RAG投入や Playbook 共有は「ファイルコピー」。`fts.db` の共有は禁止

参照: `docs/auto-refine-agents/worktree-guide.md`

