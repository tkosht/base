# ワークツリー運用ガイド（複数エージェント並列）

目的: 複数エージェントを安全に並列実行するための Git worktree ベース運用を標準化する。

## 1. 推奨レイアウト
```
<repo-root>/
  .git/
  (通常作業ツリー)
../worktrees/
  agent-a/
    .agent/     # 専用（共有禁止）
    ...
  agent-b/
    .agent/     # 専用（共有禁止）
    ...
```
- 各 worktree は `.agent/` を独立保持し、RAG `semantic/fts.db` を共有しない。

## 2. ブランチ命名
- 例: `feature/agent-a`, `feature/agent-b`（プロジェクト規約の `feature/* | task/*` に準拠）

## 3. 基本コマンド
```bash
# 作成
mkdir -p ../worktrees
git checkout develop

git branch feature/agent-a
git worktree add ../worktrees/agent-a feature/agent-a

# 一覧
git worktree list

# 削除（安全）
git worktree remove ../worktrees/agent-a
# ブランチも不要なら
git branch -D feature/agent-a
```

## 4. 安全基準
- `.agent/` と配下（`state/`, `generated/{rubrics,artifacts}`, `memory/semantic/fts.db`, `logs/` 等）は worktree 専用
- 同一 worktree 内での複数エージェント併走は非推奨
  - やむを得ず同居する場合: `task_id` 毎に WM/ログ/成果物のパスを完全分離する
- RAG投入や Playbook 共有は「ファイルコピー」で行い、DBファイル自体の共有を避ける

## 5. 初期化
- 各 worktree で初回アクセス時、ACE が `.agent/` を自動生成（冪等）
- 生成物: `state/`, `generated/{rubrics,artifacts}`, `memory/episodic`, `memory/semantic/fts.db`, `prompts/`, `config/`, `logs/`

## 6. トラブルシュート
- 衝突/ロック: `fts.db` を共有していないか確認。共有している場合は各 worktree の DB を再初期化
- 残骸 cleanup: `git worktree list` で不整合を確認し、`git worktree remove` を実行
- 生成物 cleanup: `.agent/generated/{rubrics,artifacts}` の古い世代を定期削除（昇格済みは正典へ移管）
- 参照ずれ: ブランチを worktree に対応させる（ブランチ切替は各 worktree 内で実施）

## 7. ベストプラクティス
- 各エージェントの成果は PR ベースで `develop` へ統合
- 昇格（テンプレ更新）は `evaluation-governance.md` のゲートを通過させ、人間承認を伴う

## 8. 同期（正典とランタイム）
- 正典（Git管理）: `agent/registry/`（prompts/playbooks/rubrics/config/*.defaults.yaml）
- ランタイム（非Git）: `.agent/`（各 worktree 専用の実行状態）

手順（tasksベース）
1) pull（共有→ローカル）
   - 目的: 正典を `.agent/` に同期
   - 参照タスク: `.cursor/commands/agent/agent_templates_pull.md`
2) push / 昇格（ローカル→共有）
   - 目的: `.agent/` の有用変更を正典へ提案（PR）
   - 要件: `evaluation-governance.md` の MUST（スコア/ログ/入力ハッシュ/テンプレID/コスト/レイテンシ/根拠）
   - 参照タスク: `.cursor/commands/agent/agent_templates_push_pr.md`

注記（Symlink）: `.cursor/` は `.claude/` へのシンボリックリンクです。表記は `.cursor/commands/agent/*.md` に統一しています。

リカバリ（競合・破損時の例）
- ローカル変更の退避: `.agent/{config,prompts}` を `agent/snapshots/YYYYMMDD-HHMM/` へコピー
- 再同期: `agent_templates_pull.md` を再実行
- 最終手段: `.agent/` を削除して `agent_init.md` で再初期化後、必要に応じてスナップショットから復元

---
参照:
- `cli-implementation-design.md` 4.2/4.3.2（ACE/構造）
- `evaluation-governance.md`

