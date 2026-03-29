# Source Map

## Canonical / Adapter Surface

| Role | Path | Use when |
| --- | --- | --- |
| Canonical repo-local instructions | `AGENTS.md` | 短い入口と repo-local の不変条件を確認するとき |
| Claude adapter | `CLAUDE.md` | thin adapter が正本を実参照しているか確認するとき |
| AI contract details | `docs/ai/repo-contract.md` | 詳細な agent workflow、protected path、settings ownership を確認するとき |
| Standards | `docs/standards/` | coding / testing / security / review の標準を確認するとき |
| Architecture | `docs/architecture/overview.md` | repo の責務分離と overlay 戦略を確認するとき |
| Gemini adapter | `GEMINI.md` | Gemini 側の import 導線を確認するとき |
| Cursor always-on adapter | `.cursor/rules/rules.mdc` | Cursor 側の常時読込面を確認するとき |
| Cursor compatibility shims | `.cursor/rules/core.mdc`, `.cursor/rules/project.mdc` | 互換維持だけの退避面を確認するとき |

## OnDemand Support Docs

| Path | Why it matters |
| --- | --- |
| `docs/repository-template-design.md` | AI agent template の親設計文書 |
| `memory-bank/00-core/knowledge_access_principles_mandatory.md` | canonical / adapter / OnDemand 分離の原則 |
| `memory-bank/00-core/mandatory_rules_checklist.md` | 正本から切り出した軽量確認表 |
| `memory-bank/02-organization/tmux_organization_success_patterns.md` | deprecated 手順の隔離例 |
| `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md` | before / after load matrix、source-to-claim、sizing ルール |

## Review And Audit Evidence

| Path | Why it matters |
| --- | --- |
| `scripts/ci/validate_template.py` | 新しい template health の構造検証 |
| `tests/test_template_contract.py` | control-plane contract の単体検証 |
| `docs/04.knowledge/base_harness_set.toml` | 現在の retained harness inventory の正本 |
| `docs/04.knowledge/base_harness_set.md` | 人が読むための retained harness 要約 |
| `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md` | source-to-claim と before / after load matrix |

## How To Read This Repo

1. まず `AGENTS.md` を読む。
2. 次に `docs/ai/repo-contract.md` と `docs/architecture/overview.md` を見て、詳細 contract と責務分離を確認する。
3. adapter 面 (`CLAUDE.md`, `GEMINI.md`, Cursor rules) を見て、正本への実導線を確認する。
4. 設計根拠が必要なら `docs/repository-template-design.md` と research note を読む。
5. retain / exclude の背景が必要なら base harness set と external research note を読む。
