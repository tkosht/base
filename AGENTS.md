# AGENTS.md

- Status: Canonical
- Load: Always
- Authority: Normative
- Canonical: this file

このファイルは、このテンプレート repo における repo-local instruction の正本です。system / developer / user などの高優先度指示がある場合はそちらを優先し、このファイルは上書きしません。

詳細な運用契約、Model Context Protocol（MCP）方針、skill 仕様、知識配置、実装標準は `docs/` に置きます。

- visual contract: `DESIGN.md`
- AI 共通運用契約: `docs/ai/repo-contract.md`
- design guidance: `docs/design/README.md`
- Model Context Protocol（MCP）方針: `docs/ai/mcp.md`
- skill reference: `docs/ai/skills/`
- 知識配置: `docs/architecture/knowledge-architecture.md`
- 構造説明: `docs/architecture/overview.md`
- 実装標準: `docs/standards/`

`CLAUDE.md` は Claude Code 向けの薄いアダプタです。`GEMINI.md` と `.cursor/` は互換面として残ることがありますが、新しい repo-wide ルールを増やす場所にはしません。

## Communication

- ユーザーとの会話は日本語で行う。
- 作業中は短い進捗共有を挟み、止まらずに end-to-end で進める。
- 略語だけで説明しない。略語を使う場合は、その場で正式名または平易な日本語を先に書く。1 回しか出ない語は略さない。

## Always-On Defaults

- まず非破壊で状況を把握し、ローカルのソース・設定・テスト・コマンド結果を優先して確認する。
- 現在性が重要、高リスク、またはユーザーが明示した場合のみ、必要な主張を公式一次情報で検証する。
- 秘密情報、鍵、トークン、`.env*`、`secrets/` 配下の内容は表示しない。露出の恐れがある操作は停止する。
- 変更を伴う作業は `main` / `master` 以外で行う。
- 破壊的な git / ファイル操作は明示依頼なしでは行わない。ユーザーや自動生成の既存変更は巻き戻さない。
- 文書化された shared settings と skill entrypoints は code と同等以上の慎重さで扱う。

## Execution

- 新機能の開発では、可能なら先に失敗テストまたは受け入れテストを追加・更新し、最小実装と整理の循環で進める。テスト駆動開発（TDD）を採らない場合は、理由と代替検証を報告する。
- 狭い編集タスクでは、隣接実装と対象テストを確認し、最小変更と近接検証を優先する。
- レビューでは finding ごとに分け、影響した関数・テスト・契約名を本文に明示する。

## Maintenance

- `AGENTS.md` は短い入口に保ち、長い手順や変化しやすい詳細は `docs/` へ分離する。
- 長く残す知識は `docs/architecture/knowledge-architecture.md` に従って配置し、設計理由は `docs/architecture/decision-records/` に設計判断メモとして残す。
- Codex 用 skill entrypoint は `.agents/skills/`、Claude 用は `.claude/skills/` を正面入口とする。`.codex/skills/` は互換 shim として扱う。
