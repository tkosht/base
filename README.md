# AI Agent Repository Template

Codex のコマンドラインツール（Codex CLI）と Claude Code を中心に、GitHub の標準機能と AI エージェント運用を最初から揃えるためのテンプレートリポジトリです。

## Quick Start

1. GitHub の template repository 機能で新しい repo を作成する
2. `.github/CODEOWNERS` の placeholder を実 owner に置き換える
3. `docs/architecture/overview.md`、`docs/ai/repo-contract.md`、root の `DESIGN.md` を実プロジェクト向けに更新する
4. `make bootstrap` を実行して Python 依存と Volta 管理のエージェント CLI を入れる
5. 必要なら starter overlay を適用する
   - Python: `make use-python-starter`
   - Next.js: `make use-nextjs-starter`
6. Codex 実行テストを使うなら、`codex` を一度起動して ChatGPT にログインする

## Primary Docs

- 人間向け入口: [README.md](./README.md)
- Codex / agent 入口: [AGENTS.md](./AGENTS.md)
- Claude Code 入口: [CLAUDE.md](./CLAUDE.md)
- visual contract: [DESIGN.md](./DESIGN.md)
- AI 共通運用契約: [docs/ai/repo-contract.md](./docs/ai/repo-contract.md)
- Model Context Protocol（MCP）方針: [docs/ai/mcp.md](./docs/ai/mcp.md)
- 実行用チェックリスト: [docs/ai/operator-checklist.md](./docs/ai/operator-checklist.md)
- 実行プレイブック: [docs/ai/execution-playbooks.md](./docs/ai/execution-playbooks.md)
- design guidance: [docs/design/README.md](./docs/design/README.md)
- 構造説明: [docs/architecture/overview.md](./docs/architecture/overview.md)
- 知識配置: [docs/architecture/knowledge-architecture.md](./docs/architecture/knowledge-architecture.md)
- ハーネス一覧: [docs/architecture/base-harness-set.md](./docs/architecture/base-harness-set.md)
- ハーネス資源 registry: [docs/architecture/harness-resources.toml](./docs/architecture/harness-resources.toml)
- 設計判断メモ: [docs/architecture/decision-records/README.md](./docs/architecture/decision-records/README.md)
- 実装標準: [docs/standards/](./docs/standards/)
- コミュニケーション標準: [docs/standards/communication.md](./docs/standards/communication.md)
- 元設計書: [docs/repository-template-design.md](./docs/repository-template-design.md)

## Repository Shape

- root: README / instruction surface / visual contract / GitHub governance / shared tool settings
- `docs/ai/`: AI エージェント向けの詳細契約、Model Context Protocol（MCP）方針、checklist、skill reference
- `docs/design/`: root `DESIGN.md` を支える design guidance と reference-only sample
- `docs/architecture/`: ディレクトリ責務、知識配置、ハーネス一覧、設計判断メモ
- `docs/standards/`: 実装、テスト、セキュリティ、レビュー、コミュニケーションの標準
- `.claude/`, `.codex/`, `.agents/`: shared settings と tool-specific entrypoints
- `scripts/ci/`: template 健全性検証
- `scripts/template/`: overlay 適用ロジック
- `templates/`: `python-minimal` と `nextjs-app` の starter overlay

## Commands

- `make bootstrap`: Python 依存と Volta 管理のエージェント CLI を導入
- `make doctor`: template の必須構造と shared settings を検証
- `make lint`: repo の lint を実行
- `make test`: 通常の control-plane / retained skill tests を実行
- `make test-codex-live`: ChatGPT にログイン済みのローカル端末でのみ `codex exec` を使う実行テストを実行
- `make harness-autopt`: `codex-subagent` を対象に自己最適化 run を起動し、通常 gate 通過時だけ PR を作成
- `make template-smoke`: overlay smoke tests のみ実行
- `make sync-skill SKILL=grill-me`: vendored upstream skill を再取得して `.claude/skills/` と symlink を同期

通常の継続的インテグレーション（CI）と `make test` では、ChatGPT ログインを要する Codex 実行テストは実行しません。

## Compatibility Notes

- `.cursor/`、`GEMINI.md`、`.codex/skills/` は互換のため残ることがありますが、v1 テンプレートの primary surface ではありません。
- Codex 用の repo-local skill entrypoint は `.agents/skills/`、Claude 用は `.claude/skills/` を正面入口とします。`.codex/skills/` は互換 shim として維持します。
- `docs/repository-template-design.md` は入力設計書として凍結し、運用中の正本は `docs/` と `docs/architecture/decision-records/` に置きます。
- root の `DESIGN.md` が canonical な visual contract です。`docs/design/README.md` は補助面で、generated repo では通常 root の `DESIGN.md` を更新します。
