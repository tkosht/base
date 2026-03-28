# Agent Instruction Simplification Research

- Status: Reference
- Load: OnDemand
- Authority: Operational
- Canonical: `AGENTS.md`

## Goal
- `AGENTS.md` と関連文書群を、開発体験を維持したまま最小限に単純化する。
- ルールの有効/無効、常時読込/必要時参照、コンテキストサイズの関係を監査可能な形で残す。

## Before / After Load Matrix

| Tool | Before always-loaded docs | Before size | After always-loaded docs | After size | Notes |
| --- | --- | ---: | --- | ---: | --- |
| Codex | `AGENTS.md` | 21.7KB | `AGENTS.md` | 5.1KB | 正本は維持しつつ短文化。 |
| Claude Code | `CLAUDE.md` + `AGENTS.md` | 21.7KB | `CLAUDE.md` + `AGENTS.md` | 5.2KB | before / after ともに adapter 経由の実効読込量で計上。 |
| Gemini CLI | `none` | 0B | `GEMINI.md` + `@AGENTS.md` | 5.2KB | repo-local support を明示し、正本へ接続。 |
| Cursor | `.cursor/rules/core.mdc`, `.cursor/rules/project.mdc`, `.cursor/rules/rules.mdc` (`alwaysApply: true` x3) | 48.2KB | `.cursor/rules/rules.mdc` (`alwaysApply: true` x1) | 1.1KB | `core` / `project` は互換 shim 化。 |

- Matrix rule: tool ごとの `effective always-loaded bytes` を比較する。adapter 本体だけでなく、`@AGENTS.md` や symlink 相当の推移的な読込先も含める。
- Baseline rule: `before = git HEAD`、`after = current working tree`。KB 表記は 10 進で 0.1KB に丸める。

## Repo-Wide Fixed-Instruction Floor
- Before: `AGENTS.md` 21.7KB + Cursor `alwaysApply` 48.2KB = 69.9KB
- After: `AGENTS.md` 5.1KB + Cursor `alwaysApply` 1.1KB = 6.3KB
- Floor rule: これは tool 別 matrix とは別の repo-wide 集計で、repo 全体で常時効く代表面だけを合算する。

## Active / Inactive Instruction Map

### Always
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.cursor/rules/rules.mdc`

### OnDemand
- `memory-bank/00-core/mandatory_rules_checklist.md`
- `memory-bank/00-core/knowledge_access_principles_mandatory.md`
- `memory-bank/00-core/repository_directory_conventions.md`
- `memory-bank/11-checklist-driven/checklist_driven_execution_framework.md`
- `memory-bank/11-checklist-driven/templates/codex_mcp_collaboration_checklist_template.md`
- `memory-bank/02-organization/tmux_organization_success_patterns.md`
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`

### Deprecated
- `memory-bank/00-core/knowledge_loading_functions.md`
- `memory-bank/00-core/session_initialization_script.md`
- `.cursor/rules/core.mdc`
- `.cursor/rules/project.mdc`

## Source-to-Claim Mapping

| Claim | Source URL | Applied decision |
| --- | --- | --- |
| Codex has repo-local `AGENTS.md` support and recommends short, actionable instructions in the agent loop. | https://openai.com/index/unrolling-the-codex-agent-loop/ | `AGENTS.md` を単一の短い正本として維持し、重複規範を削除する。 |
| Claude Code loads `CLAUDE.md` at session start, supports `@path` imports, and recommends keeping the file concise. | https://docs.anthropic.com/en/docs/claude-code/memory | `CLAUDE.md` は薄いアダプタにし、長文規範は `@AGENTS.md` へ寄せる。 |
| Gemini CLI loads `GEMINI.md` hierarchically from the current directory and ancestors. | https://google-gemini.github.io/gemini-cli/docs/core/context/ | repo-local `GEMINI.md` を正式サポートし、正本の導線を維持する。 |
| Gemini CLI supports `@file` / `@directory` import syntax inside prompts and `GEMINI.md`. | https://google-gemini.github.io/gemini-cli/docs/core/memport/ | `GEMINI.md` に `@AGENTS.md` を置き、Claude と同じ薄いアダプタ構成にそろえる。 |
| Cursor rules are persistent context and should stay specific; rule types separate always-on from on-demand attachment. | https://docs.cursor.com/en/context/rules | `alwaysApply` は 1 ファイルに限定し、残りは互換 shim または OnDemand 文書へ退避する。 |
| Long contexts reduce retrieval quality around the middle of the prompt. | https://arxiv.org/abs/2307.03172 | 巨大な固定指示ではなく、短い正本 + 必要時参照を基本構成にする。 |

## Applied Decisions In This Repo
- 正本は `AGENTS.md` 1 枚に集約する。
- `CLAUDE.md` と `GEMINI.md` は最小限の adapter にし、正本を import する。
- Cursor は `alwaysApply: true` を 1 本だけ残し、他は互換 shim とする。
- チェックリスト、tmux、協働、配置規約は `OnDemand` とし、旧ローダーは `Deprecated` に落とす。
- tmux 文書は current entry point と historical appendix を分け、deprecated 手順を現役導線から外す。
