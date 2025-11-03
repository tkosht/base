# auto-refine-agents: Agent Commands

本ディレクトリは auto-refine-agents サブプロジェクト専用の実行タスクを集約します。

## 命名規約
- ファイル名は snake_case + `.md`
- 役割プレフィックスを付与: `agent_` / `outerloop_` / `eval_` / `worktree_`
- 一タスク一目的（入出力・前提・手順・注意・終了条件を明記）

## ACE（自動初期化）原則
- すべてのタスクは先頭で「ACE自動初期化スニペット」を実行します。
- `.agent/**` が未作成でも、初回アクセス時にディレクトリと FTS5 DB、最小 config を自動生成します（冪等）。
- 手動の初期化は不要です（復旧専用の `agent_recovery_init.md` を用意）。

## シンボリックリンク方針
- `.cursor/` は `.claude/` へのシンボリックリンクです（実体: `.claude/`）。
- ドキュメント上の表記は `.cursor/commands/agent/*.md` に統一します（Cursor互換）。
- 実体操作（追加/改名/削除）は `.claude/` 側で行っても同一です（二重生成禁止）。

## 実行導線
- 最短（Quickstart）: `agent_quickstart.md`
- 完全（Full Cycle）: `agent_full_cycle.md`

## タスク一覧（抜粋）
- `agent_goal_run.md`: Goal のみで Inner-Loop 最短経路実行（Evaluator I/O v2）
- `agent_templates_pull.md`: `agent/registry/**` → `.agent/**` 同期
- `agent_templates_push_pr.md`: `.agent/**` → `agent/registry/**` 昇格 PR
- `eval_perturb_suite.md`: 摂動ロバスト性スイート実行
- `outerloop_abtest.md`: テンプレ A/B 比較
- `outerloop_promote.md`: Gate MUST 基準で昇格判定
- `outerloop_rollback.md`: 劣化時の自動降格
- `worktree_ops.md`: worktree 作成/削除/分離ガイド

詳細は `docs/auto-refine-agents/*.md` を参照してください。


## 実行ガイダンス（.md は直接 bash 不可）
- `.md` を `bash file.md` で直接実行しないでください（Markdownはbashで解釈できません）。
- 各タスクは `.md` 内の最初の ```bash コードブロックを抽出して実行してください。

```bash
awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_goal_run.md | bash
```

- 簡便のためのエイリアス例（任意）:
```bash
alias mdrun='f(){ awk '\''/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag'\'' "$1" | bash; }; f'
# 使い方: mdrun ./.cursor/commands/agent/agent_goal_run.md
```

備考:
- 本ガイダンスは `docs/auto-refine-agents/cli-implementation-design.md` の「ゼロスクリプト（ワンライナー運用）」方針に準拠しています。

