# Subagent Skill (SKILL.md) テンプレート

## 目的
サブエージェント/オーケストレーター系の Skill を作る際に、SKILL.md に必要な要素（実行モード、コンテキスト整理、結果形式、ガードレール）を短く実用的にまとめるための再利用テンプレート。

このテンプレートは「SKILL.md の書き方」を提供するものであり、特定の実装（例: `single/parallel/competition` の実装有無）を保証しません。実装/スクリプト/コマンドに合わせて取捨選択してください。

## SKILL.md 雛形（コピペ用）

```markdown
---
name: <skill-name>
description: "Auto-trigger when ... (include explicit triggers)."
allowed-tools:
  - Bash(...)
  - Read
  - Write
  - Glob
metadata:
  version: 0.1.0
  owner: <owner>
  maturity: draft
  tags: [skill, subagent, orchestrator]
---

## Overview
<この Skill の役割を 2-4 行で。入口（何を受けて何を返すか）を明確に。>

## Quick Start
<最短で再現できる 1-3 個の実行例。>

## Execution Modes
<実装がある場合のみ。無いモードは書かない。>
- `single`: 1回実行（小さく速い）
- `parallel`: 複数回実行→統合（列挙/調査向け）
- `competition`: 複数案→比較→最良採用（品質重視）
- `pipeline`: 収集→設計→検証→出力の段階的処理（段階分割が必要な時）

## Context Engineering
- 目的・対象・制約・入力/出力を明確化
- 事実ベースで記述し、根拠（ファイルパス/ログ/コマンド）を示す
- 不明点は最小の確認質問で補完

## Result Handling
- 出力形式（JSON/箇条書き/パッチ等）を固定化し、機械処理できる形に寄せる
- 失敗時は「原因」「次の一手」「再現/検証手順」をセットで返す

## Guardrails
- 機密情報や認証情報を扱わない
- 破壊的コマンドは避ける
- 既定は安全側（read-only / dry-run）
```

## 由来
旧 `.claude/skills/codex-subagent/SKILL.md`（2025-12-22 生成）に含まれていた「SKILL.md 設計テンプレ」部分を、再利用可能な形に分離したもの。

