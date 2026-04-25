---
name: harness-autoptimizer
description: "Auto-trigger when the user asks to run or adjust autonomous harness optimization, repo-wide Codex experience capture, slow or failing gates, Codex agent control loops, resource registry evaluation, constrained self-repair, and draft pull requests."
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

この skill は Codex agent が repo-local harness を小粒に自己最適化するための評価・制約ハーネスです。自律判断の主体は現在の Codex agent であり、Python helper は prompt assembly、sanitized state、diff guard、検証実行、draft pull request 補助に限定します。

経験捕捉はこの controller 経由の実行に限定しません。この repo 上で動く Codex agent は、通常タスクの終了時、ユーザー訂正時、gate 異常時、実装複雑化や instruction 矛盾を見つけた時に、軽量 Self-Audit で保持判断します。

## Workflow

1. Sense: repo state、gate 結果、duration、failure text、changed paths、task friction、`docs/architecture/harness-resources.toml` を読む。
2. Classify: 全 registry resource を比較し、evidence から resource / goal / confidence / reason を決める。人間入力の `TARGET` / `GOAL` は使わない。
3. Constrain: `AutoptRequest` に editable paths、excluded paths、diff limits、validators、success criteria、draft pull request policy を固定する。
4. Repair: Codex agent 自身が `AutoptRequest` の範囲内で最小変更する。
5. Verify: `make doctor`、`make lint`、`make test` と diff guard を通す。
6. Self-Audit: 実行経験を ExperienceCandidate として扱い、code simplification、test、validator、skill prompt、canonical rule、設計判断メモ、非追跡 state、discard のどれに値するか判断する。
7. Reflect: low confidence、unsupported evidence、gate failure、保持価値不足の場合は修復や昇格をせず sanitized state に理由を残す。
8. Propose: 成功時だけ draft pull request を作る。

## Controller Prompts

- `.claude/skills/harness-autoptimizer/prompts/auto-controller.md`: Codex agent の制御ループ
- `.claude/skills/harness-autoptimizer/prompts/self-audit.md`: 全 Codex agent 向けの経験保持判断
- `.claude/skills/harness-autoptimizer/prompts/experience-to-rule.md`: 経験候補の昇格・棄却・配置判断
- `.claude/skills/harness-autoptimizer/prompts/repair-request.md`: `AutoptRequest` から作る編集指示書

```bash
uv run python .claude/skills/harness-autoptimizer/scripts/harness_autopt.py \
  --print-controller-prompt
```

## Guardrails

- 1 run 1 improvement を維持する。
- `make doctor`, `make lint`, `make test` を通過しない候補は採用しない。
- raw prompt、raw model output、秘密情報、`.env*`、`secrets/**` を pull request 本文に含めない。
- `guarded_pr` resource は draft pull request のみ作る。
- 全 registry resource を分類対象にし、low confidence なら修復せず止まる。
- Markdown / settings / template / validation / test performance / skill resource は、それぞれの `mutable_paths`、`excluded_paths`、diff limit を守る。
- raw prompt、raw model output、秘密情報、runtime logs、一回限りの作業メモは tracked knowledge に昇格しない。
- 永続化する経験は、再発可能性、影響度、一般性、検証可能性、context cost を満たす蒸留済み artifact だけにする。
