---
name: harness-autoptimizer
description: "Auto-trigger when the user asks to run or adjust autonomous harness optimization for repo-local agent harnesses, including codex-subagent stability, resource registry evaluation, worktree-based candidate generation, and automated pull requests."
allowed-tools:
  - Bash(uv run python:*)
  - Bash(make:*)
  - Bash(git:*)
  - Bash(gh:*)
  - Bash(codex:*)
  - Read
  - Glob
metadata:
  version: 0.1.0
  owner: codex
  maturity: draft
  tags: [skill, harness, autoptimization, codex-subagent, worktree]
---

# Harness Autoptimizer

## Purpose

この skill は repo-local harness を小粒に自己最適化するための実行入口です。初期対象は `codex-subagent` の安定性で、将来は resource registry に登録された instruction surface、knowledge docs、settings、template、validation surface へ拡張します。

## Workflow

1. `docs/architecture/harness-resources.toml` で対象 resource と編集許可範囲を確認する。
2. `harness_autopt.py --list-resources` で registry が読めることを確認する。
3. `make harness-autopt` または直接 CLI を実行し、worktree 上で baseline gate、candidate generation、diff guard、candidate gate を通す。
4. gate 通過時だけ自動 commit / push / pull request 作成まで進める。
5. gate 失敗時は pull request を作らず、`.codex/sessions/harness_autopt/` の run state を確認する。

## Commands

```bash
make harness-autopt
```

```bash
uv run python .claude/skills/harness-autoptimizer/scripts/harness_autopt.py \
  --target codex-subagent \
  --goal stability \
  --candidate-count 1 \
  --base origin/main \
  --worktree-root worker/harness-autopt \
  --create-pr
```

## Guardrails

- 1 run 1 improvement を維持する。
- `make doctor`, `make lint`, `make test` を通過しない候補は採用しない。
- raw prompt、raw model output、秘密情報、`.env*`、`secrets/**` を pull request 本文に含めない。
- 既存の作業ツリーは編集せず、base ref から作成した worktree だけを候補生成対象にする。
