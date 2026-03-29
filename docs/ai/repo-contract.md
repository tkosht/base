# リポジトリ運用契約

## Purpose

この文書は、このテンプレートから生成された repo における人間と AI エージェントの共通運用契約です。`AGENTS.md` と `CLAUDE.md` は入口であり、ここが詳細の正本です。

## Reading Order

1. `README.md`
2. `AGENTS.md` または `CLAUDE.md`
3. `docs/ai/repo-contract.md`
4. `docs/architecture/overview.md`
5. `docs/architecture/knowledge-architecture.md`
6. `docs/standards/*.md`

## Repository Roles

- `README.md`: 人間向けの全体像と初動
- `AGENTS.md`: Codex / agent 向けの短い永続指示
- `CLAUDE.md`: Claude Code 向けの薄いアダプタ
- `docs/ai/`: AI 向けの詳細契約、Model Context Protocol（MCP）方針、実行プレイブック、skill reference
- `docs/architecture/`: 構造、知識配置、ハーネス一覧、設計判断メモ
- `docs/standards/`: 実装、テスト、セキュリティ、レビュー、コミュニケーションの標準
- `.codex/`, `.claude/`, `.agents/`, `.github/`: 行動規範を変えうる shared settings

## Default Workflow

- まずローカルのソース、設定、テスト、コマンド結果を確認する
- 新機能では可能なら失敗テスト先行か受け入れテスト先行で進める
- 狭い編集では最小変更と近接検証を優先する
- `main` / `master` に直接変更しない
- 破壊的操作は明示依頼なしで行わない
- shared settings と GitHub governance の変更は通常コード以上のレビュー基準で扱う

## Test Modes

- `make test`: ChatGPT ログインを必要としない通常テストだけを実行する
- `make test-codex-live`: ChatGPT にログイン済みのローカル端末でだけ、`codex exec` を実際に呼ぶ実行テストを実行する
- 通常の GitHub Actions は `make test` を使い、Codex 実行テストは標準の継続的インテグレーション（CI）に含めない
- 実行テストの前に `make bootstrap` で `codex` のコマンドラインツール（CLI）を導入し、`codex` を一度起動して ChatGPT にログインしておく

## Protected Paths

- `.env*`
- `secrets/**`
- 認証トークン、鍵、OAuth 認証情報
- local-only settings: `.claude/settings.local.json`, `.claude/.claude/**`
- Codex / Claude の runtime state: `.codex/auth.json`, `.codex/history.jsonl`, `.codex/log*`, `.codex/state*.sqlite`

これらは値の表示、コミット、PR 本文への貼り付けを禁止します。

## Settings Ownership

- `.claude/settings.json`: Claude Code の shared project settings
- `.codex/config.toml`: Codex のコマンドラインツール（CLI）向け repo-scoped defaults
- `.mcp.json`: Claude 向け shared Model Context Protocol（MCP）設定
- `.agents/skills/`: Codex 向け skill entrypoint
- `.claude/skills/`: Claude 向け skill entrypoint
- `.codex/skills/`: Codex 互換 shim

## Reporting Contract

- 実装報告では、変更結果と検証結果を分けて書く
- テスト駆動開発（TDD）を外した場合は理由と代替検証を書く
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

- `.cursor/` と `GEMINI.md` は compatibility adapter であり、repo-wide rule の primary source ではありません。
- `docs/repository-template-design.md` は入力設計書として残しますが、運用中の正本ではありません。
