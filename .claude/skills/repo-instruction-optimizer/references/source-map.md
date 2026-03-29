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
| `docs/architecture/knowledge-architecture.md` | canonical / adapter / OnDemand 分離を現在の docs 面で確認するとき |
| `docs/ai/operator-checklist.md` | 正本から切り出した軽量確認表を参照するとき |
| `docs/ai/execution-playbooks.md` | 複雑タスクでの実行プレイブックを参照するとき |
| `docs/architecture/decision-records/knowledge-surface-consolidation.md` | 知識面の統合理由と legacy removal を確認するとき |

## Review And Audit Evidence

| Path | Why it matters |
| --- | --- |
| `scripts/ci/validate_template.py` | 新しい template health の構造検証 |
| `tests/test_template_contract.py` | control-plane contract の単体検証 |
| `docs/architecture/base-harness-set.toml` | 現在の retained harness inventory の正本 |
| `docs/architecture/base-harness-set.md` | 人が読むための retained harness 要約 |
| `docs/architecture/decision-records/knowledge-surface-consolidation.md` | source-to-claim を蒸留した判断の要約 |

## How To Read This Repo

1. まず `AGENTS.md` を読む。
2. 次に `docs/ai/repo-contract.md` と `docs/architecture/overview.md` を見て、詳細 contract と責務分離を確認する。
3. adapter 面 (`CLAUDE.md`, `GEMINI.md`, Cursor rules) を見て、正本への実導線を確認する。
4. 設計根拠が必要なら `docs/repository-template-design.md` と設計判断メモを読む。
5. retain / exclude の背景が必要なら base harness set と knowledge architecture を読む。
