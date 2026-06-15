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

実行タスクは、ユーザー指定がない場合でも DAG team を必須とします。親 Codex agent と leaf 以外の制御ノードは manager として分解・割当・進行管理・sanitized result の集約に限定し、repair / review / verify などの実作業は leaf node に委譲します。subagent 実行が高優先度指示や tool 不足で使えない場合は、親が代行せず blocked reason として停止します。

## Workflow

1. Sense: repo state、gate 結果、duration、failure text、changed paths、task friction、明示された review artifact、`docs/architecture/harness-resources.toml` を読む。選択 target だけでなく、registry 全 resource paths に対して `ProactiveReviewProbe` による proactive review probe を走らせる。ただし各 resource の `excluded_paths` は尊重する。
2. Classify: 全 registry resource を比較し、evidence から resource / goal / confidence / reason を決める。人間入力の `TARGET` / `GOAL` は使わない。
3. Constrain: `AutoptRequest` に editable paths、excluded paths、diff limits、validators、success criteria、draft pull request policy を固定する。
4. Repair: `codex-subagent` の `team_policy: "manager_leaf_v1"` で repair leaf node に `AutoptRequest` の範囲内の最小変更を委譲する。repair leaf node は修正前後に `HorizontalExpansionInvestigation` を必ず実行し、same defect pattern、contract drift、missing validation、obsolete instruction、または sibling surface が in-scope にないか調査する。`InScopeHorizontalFix` として同じ resource / goal / constraints 内で直せる same-pattern findings は同じ repair cycle で修正し、範囲外は out_of_scope finding として残す。親 Codex agent と非 leaf manager は manager-only とし、分解・割当・進行管理・sanitized result の集約だけを行う。subagent が使えない場合は blocked reason を残して停止し、親や manager が代行せず実装しない。
5. Verify: verify leaf node が `make doctor`、`make lint`、`make test` と diff guard を通す。親 Codex agent と manager は manager-only として結果確認と停止判断だけを行う。
6. Review: review leaf node が、要件・実装・prompt・test・proactive probe finding・review artifact の整合性を code review と同じ厳しさで確認する。finding は `ReviewFinding` として記録し、`verification_class` で検証種別を残す。`Prior Findings Closure Table` と `Failure Hypothesis Table` を使い、no material findings requires negative evidence、parent reducer must audit no-finding leaves、validators do not close semantic findings、existing implementation output semantics are protected、meaning-first repair、Context Reconstruction Table、needs_user_decision を守る。target 外 resource の material finding は `out_of_scope` として記録し、黙殺しない。`excluded_paths` 内の歴史的記録や意図的な除外 path は false stop reason にしない。`ReviewReport` の `loop_count`、`converged`、`stop_reason` に加えて、`HorizontalExpansionInvestigation` の調査範囲、`InScopeHorizontalFix` の適用有無、deferred / out_of_scope finding、residual risk を確認する。material finding があれば同じ `AutoptRequest` 制約内で leaf Repair -> leaf Verify -> leaf Review を繰り返す。親 Codex agent と manager は manager-only として反復を割り当て、sanitized result を集約するだけにする。
7. Self-Audit: 実行経験を ExperienceCandidate として扱い、code simplification、test、validator、skill prompt、canonical rule、設計判断メモ、非追跡 state、discard のどれに値するか判断する。
8. Reflect: low confidence、unsupported evidence、gate failure、保持価値不足、または unresolved material finding がある場合は修復や昇格をせず sanitized state に理由を残す。
9. Propose: 成功時だけ draft pull request を作る。`RepairReportingRequired` として、修正を試みた場合は final response / pull request body に、修正内容、水平展開で調査した範囲、適用した in-scope horizontal fixes、該当なしの判断、deferred / out_of_scope finding、validation result、residual risk を必ず記録する。

## Controller Prompts

- `.agents/skills/harness-autoptimizer/prompts/auto-controller.md`: Codex agent の制御ループ
- `.agents/skills/harness-autoptimizer/prompts/self-audit.md`: 全 Codex agent 向けの経験保持判断
- `.agents/skills/harness-autoptimizer/prompts/experience-to-rule.md`: 経験候補の昇格・棄却・配置判断
- `.agents/skills/harness-autoptimizer/prompts/repair-request.md`: `AutoptRequest` から作る編集指示書
- `.agents/skills/harness-autoptimizer/prompts/harness-contracts.md`: 合意反転、会話捕捉、レビュー閉鎖、ユーザー向け表現の汎用契約

```bash
uv run python .agents/skills/harness-autoptimizer/scripts/harness_autopt.py \
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
- 自己レビューの反復は scope creep の許可ではない。同じ resource / goal / constraints 内で解消できない finding は停止理由として記録する。
- すべての repair / fix は `HorizontalExpansionInvestigation` を必須とし、same defect pattern、contract drift、missing validation、obsolete instruction、sibling surface を水平展開して調査する。
- `HorizontalExpansionInvestigation` で見つかった same-pattern findings が同じ AutoptRequest の resource / goal / constraints 内で直せる場合、`InScopeHorizontalFix` として同じ repair cycle で修正し、検証と review を再実行する。
- 修正を試みた run は `RepairReportingRequired` を満たす。final response / pull request body には、水平展開の調査範囲、適用した in-scope horizontal fixes、該当なしの判断、deferred / out_of_scope finding、validation result、residual risk を明記する。
- DAG team 実行を既定必須にし、`codex-subagent` pipeline では `team_policy: "manager_leaf_v1"` を使う。
- 非 leaf / control node は manager-only とし、実装・検証・レビュー作業を直接実行しない。
