# AGENTS.md

- Status: Canonical
- Load: Always
- Authority: Normative
- Canonical: this file

このファイルは、このテンプレート repo における repo-local instruction の正本です。system / developer / user などの高優先度指示がある場合はそちらを優先し、このファイルは上書きしません。

詳細な運用契約、Model Context Protocol（MCP）方針、skill 仕様、知識配置、実装標準は `docs/` に置きます。

- visual contract: `DESIGN.md`
- AI 共通運用契約: `docs/ai/repo-contract.md`
- Codex 経験捕捉: `docs/ai/experience-capture.md`
- design guidance: `docs/design/README.md`
- Model Context Protocol（MCP）方針: `docs/ai/mcp.md`
- skill reference: `docs/ai/skills/`
- 知識配置: `docs/architecture/knowledge-architecture.md`
- 構造説明: `docs/architecture/overview.md`
- 実装標準: `docs/standards/`
- ハーネス資源 registry: `docs/architecture/harness-resources.toml`

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
- タスク終了時やユーザー訂正時に、経験を将来の行動改善へ残すべきかを軽量に判断する。詳細は `docs/ai/experience-capture.md` に従う。

## Execution

- 新機能の開発では、可能なら先に失敗テストまたは受け入れテストを追加・更新し、最小実装と整理の循環で進める。テスト駆動開発（TDD）を採らない場合は、理由と代替検証を報告する。
- 狭い編集タスクでは、隣接実装と対象テストを確認し、最小変更と近接検証を優先する。
- レビューでは finding ごとに分け、影響した関数・テスト・契約名を本文に明示する。

## Maintenance

- `AGENTS.md` は短い入口に保ち、長い手順や変化しやすい詳細は `docs/` へ分離する。
- 長く残す知識は `docs/architecture/knowledge-architecture.md` に従って配置し、設計理由は `docs/architecture/decision-records/` に設計判断メモとして残す。
- skill entrypoint の正本は `.agents/skills/` とする。`.claude/skills/` と `.codex/skills/` は互換 shim として扱う。

## Cursor Cloud specific instructions

このリポジトリは Python 製の control-plane / template tooling です。標準コマンドは `Makefile` と `README.md` の Commands 節を正本とする（`make lint` / `make doctor` / `make test`）。以下は Cloud 環境で非自明な点のみ。

- パッケージ管理は `uv`。依存の入口は `make bootstrap` だが、これは `bin/install_agentcli.sh`（Claude / Codex / Gemini CLI 導入）も走らせる。update script では依存同期に必要な `uv sync --all-groups --all-extras` のみ行い、エージェント CLI 導入は含めない。
- `uv` は `~/.local/bin` に入り、`~/.bashrc`（`. "$HOME/.local/bin/env"`）経由で新規シェルの PATH に載る。もし `uv` が見つからない場合は `. "$HOME/.local/bin/env"` を実行する。
- `make test` は codex-live を除外した control-plane スイート（`tests/` 配下、約 297 件）。`make test-codex-live` と `codex-subagent` パイプラインの実行（`.agents/skills/codex-subagent/scripts/codex_exec.py`）は、実際の `codex` CLI と ChatGPT ログインが必要で Cloud では動かせない（`--help` までは可）。
- ルート `compose.yml` は `docker/compose.gpu.yml` への symlink で、`make up` などの Docker/GPU 系ターゲットは Docker + GPU 前提。Cloud の通常セットアップでは不要。`Makefile` の `webapp` ターゲットは存在しない `app.demo:api` を参照する残骸で使わない。
- 動作確認用の自己完結タスク（外部依存なし）: `uv run python scripts/template/apply_overlay.py --template python-minimal --target <dir>` で starter overlay を適用し、生成物を pytest / ruff で検証できる。
- `.pre-commit-config.yaml` は未存在の `scripts/*_check.py` を参照するため、そのままでは動作しない。コミット前ゲートは `make lint` / `make doctor` / `make test` を使う。
