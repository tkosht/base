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
| `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-15_round1.md` | 初回レビューで出た欠陥パターン |
| `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-15_round1_response.md` | round1 findings の fix 方針と verification |
| `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-16_round2.md` | apples-to-apples measurement mismatch の再指摘 |
| `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-16_round2_response.md` | measurement rule の補正例 |

## How To Read This Repo

1. まず `AGENTS.md` を読む。
2. 次に adapter 面 (`CLAUDE.md`, `GEMINI.md`, Cursor rules) を見て、正本への実導線を確認する。
3. 設計根拠が必要なら research note を読む。
4. 落とし穴と修正例が必要なら round1 / round2 review と response を読む。
