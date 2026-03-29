# AI Agent Repository Template

Codex CLI と Claude Code を中心に、GitHub の標準機能と AI エージェント運用を最初から揃えるためのテンプレートリポジトリです。

## Quick Start

1. GitHub の template repository 機能で新しい repo を作成する
2. `.github/CODEOWNERS` の placeholder を実 owner に置き換える
3. `docs/architecture/overview.md` と `docs/ai/repo-contract.md` を実プロジェクト向けに更新する
4. `make bootstrap` を実行して control-plane 依存を入れる
5. 必要なら starter overlay を適用する
   - Python: `make use-python-starter`
   - Next.js: `make use-nextjs-starter`

## Primary Docs

- 人間向け入口: [README.md](./README.md)
- Codex / agent 入口: [AGENTS.md](./AGENTS.md)
- Claude Code 入口: [CLAUDE.md](./CLAUDE.md)
- AI 共通運用契約: [docs/ai/repo-contract.md](./docs/ai/repo-contract.md)
- MCP 方針: [docs/ai/mcp.md](./docs/ai/mcp.md)
- 構造説明: [docs/architecture/overview.md](./docs/architecture/overview.md)
- 実装標準: [docs/standards/](./docs/standards/)
- 元設計書: [docs/repository-template-design.md](./docs/repository-template-design.md)

## Repository Shape

- root: README / instruction surface / GitHub governance / shared tool settings
- `docs/ai/`: AI エージェント向けの詳細契約、MCP 方針、skill reference
- `docs/architecture/`: ディレクトリ責務、拡張方針、判断記録
- `docs/standards/`: coding / testing / security / review standards
- `.claude/`, `.codex/`, `.agents/`: shared settings と tool-specific entrypoints
- `scripts/ci/`: template 健全性検証
- `scripts/template/`: overlay 適用ロジック
- `templates/`: `python-minimal` と `nextjs-app` の starter overlay

## Commands

- `make bootstrap`: Python と Node の control-plane 依存を導入
- `make doctor`: template の必須構造と shared settings を検証
- `make lint`: repo の lint を実行
- `make test`: control-plane と retained skill tests を実行
- `make template-smoke`: overlay smoke tests のみ実行

## Compatibility Notes

- 既存の `memory-bank/`、`docs/04.knowledge/`、`.cursor/`、`GEMINI.md` は互換のため残っていますが、v1 テンプレートの primary surface ではありません。
- Codex 用の repo-local skill entrypoint は `.agents/skills/`、Claude 用は `.claude/skills/` を正面入口とします。`.codex/skills/` は互換 shim として維持します。
