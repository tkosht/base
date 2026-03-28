# Source Map

## Canonical / Adapter Surface

| Role | Path | Use when |
| --- | --- | --- |
| Canonical repo-local instructions | `AGENTS.md` | 正本の構造、Always-On Defaults、Execution、Load Map を確認するとき |
| Claude adapter | `CLAUDE.md` | thin adapter が正本を実参照しているか確認するとき |
| Gemini adapter | `GEMINI.md` | Gemini 側の import 導線を確認するとき |
| Cursor always-on adapter | `.cursor/rules/rules.mdc` | Cursor 側の常時読込面を確認するとき |
| Cursor compatibility shims | `.cursor/rules/core.mdc`, `.cursor/rules/project.mdc` | 互換維持だけの退避面を確認するとき |

## OnDemand Support Docs

| Path | Why it matters |
| --- | --- |
| `memory-bank/00-core/knowledge_access_principles_mandatory.md` | canonical / adapter / OnDemand 分離の原則 |
| `memory-bank/00-core/mandatory_rules_checklist.md` | 正本から切り出した軽量確認表 |
| `memory-bank/02-organization/tmux_organization_success_patterns.md` | deprecated 手順の隔離例 |
| `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md` | before / after load matrix、source-to-claim、sizing ルール |

## Review And Audit Evidence

| Path | Why it matters |
| --- | --- |
| `docs/04.knowledge/base_harness_set.toml` | 現在の retained harness inventory の正本 |
| `docs/04.knowledge/base_harness_set.md` | 人が読むための retained harness 要約 |
| `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md` | source-to-claim と before / after load matrix |

## How To Read This Repo

1. まず `AGENTS.md` を読む。
2. 次に adapter 面 (`CLAUDE.md`, `GEMINI.md`, Cursor rules) を見て、正本への実導線を確認する。
3. 設計根拠が必要なら research note を読む。
4. retain / exclude の背景が必要なら base harness set と external research note を読む。
