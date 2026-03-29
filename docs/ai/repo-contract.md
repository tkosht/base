# Repo Contract

## Purpose

この文書は、このテンプレートから生成された repo における人間と AI エージェントの共通運用契約です。`AGENTS.md` と `CLAUDE.md` は入口、ここが詳細の source of truth です。

## Reading Order

1. `README.md`
2. `AGENTS.md` または `CLAUDE.md`
3. `docs/ai/repo-contract.md`
4. `docs/architecture/overview.md`
5. `docs/standards/*.md`

## Repository Roles

- `README.md`: 人間向けの全体像と初動
- `AGENTS.md`: Codex / agent 向けの短い永続指示
- `CLAUDE.md`: Claude Code 向けの薄いアダプタ
- `docs/ai/`: AI 向けの詳細契約、MCP 方針、skill reference
- `docs/architecture/`: 構造と責務分離
- `docs/standards/`: coding / testing / security / review の標準
- `.codex/`, `.claude/`, `.agents/`, `.github/`: 行動規範を変えうる shared settings

## Default Workflow

- まずローカルのソース、設定、テスト、コマンド結果を確認する
- 新機能では可能なら TDD か acceptance-test-first を採る
- 狭い編集では最小変更と近接検証を優先する
- `main` / `master` に直接変更しない
- 破壊的操作は明示依頼なしで行わない
- shared settings と GitHub governance の変更は通常コード以上のレビュー基準で扱う

## Protected Paths

- `.env*`
- `secrets/**`
- 認証トークン、鍵、OAuth 資格情報
- local-only settings: `.claude/settings.local.json`, `.claude/.claude/**`
- Codex / Claude の runtime state: `.codex/auth.json`, `.codex/history.jsonl`, `.codex/log*`, `.codex/state*.sqlite`

これらは値の表示、コミット、PR 本文への貼り付けを禁止します。

## Settings Ownership

- `.claude/settings.json`: Claude Code の shared project settings
- `.codex/config.toml`: Codex CLI の repo-scoped defaults
- `.mcp.json`: Claude 向け shared MCP
- `.agents/skills/`: Codex 向け skill entrypoint
- `.claude/skills/`: Claude 向け skill entrypoint
- `.codex/skills/`: Codex 互換 shim

## Reporting Contract

- 実装報告では、変更結果と検証結果を分けて書く
- TDD を外した場合は理由と代替検証を書く
- 未実施 gate は `unknown` ではなく未実施 gate として分けて書く
- レビューでは finding ごとに分け、関数名・テスト名・契約名を明記する

## Generated Repo Checklist

テンプレートから repo を作成したら、最低限次を更新します。

1. `.github/CODEOWNERS`
2. `docs/architecture/overview.md`
3. `docs/standards/*.md`
4. `.codex/config.toml`
5. `.claude/settings.json`
6. `.mcp.json`

## Compatibility Notes

- `memory-bank/` と `docs/04.knowledge/` は互換や保守メモのために残ることがありますが、この文書の代替ではありません。
- `.cursor/` と `GEMINI.md` は compatibility adapter であり、repo-wide rule の primary source ではありません。
