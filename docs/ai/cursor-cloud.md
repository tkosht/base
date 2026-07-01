# Cursor Cloud 実行メモ

- Status: OnDemand
- Load: Conditional
- Authority: Runbook

この文書は Cursor Cloud でこのテンプレート repo を扱う時だけ読む実行メモです。repo-wide rule の正本ではありません。

標準コマンドは `Makefile` と `README.md` の Commands 節を正本とします。この文書では Cloud 環境で非自明な点だけを補足します。

## Setup Notes

- この repo は Python 製の control-plane / template tooling で、パッケージ管理は `uv` です。
- 依存の入口は `make bootstrap` ですが、これは `bin/install_agentcli.sh` による Claude / Codex / Gemini のコマンドラインツール導入も実行します。
- Cloud の update script で依存同期だけが必要な場合は `uv sync --all-groups --all-extras` を使い、エージェントのコマンドラインツール導入は含めません。
- `uv` は `~/.local/bin` に入り、`~/.bashrc` の `. "$HOME/.local/bin/env"` 経由で新規シェルの `PATH` に載ります。`uv` が見つからない場合は、同じ source コマンドを現在のシェルで実行します。

## Verification Notes

- `make test` は codex-live を除外した通常の control-plane suite を実行します。
- `make test-codex-live` と `codex-subagent` pipeline の実行には、実際の Codex コマンドラインツールと ChatGPT ログインが必要です。Cloud では通常動かせませんが、`--help` までなら確認できます。
- ルートの `compose.yml` は `docker/compose.gpu.yml` への symbolic link です。`make up` などの Docker / GPU 系 target は Cloud の通常セットアップでは不要です。
- `Makefile` の `webapp` target は、存在しない `app.demo:api` を参照する残骸のため使いません。
- 動作確認用の自己完結タスクが必要な場合は、`scripts/template/apply_overlay.py` で `python-minimal` starter overlay を一時ディレクトリへ適用します。生成物は `pytest` と `ruff` で検証できます。
- `.pre-commit-config.yaml` は未存在の check script を参照するため、そのままでは動作しません。コミット前 gate は `make lint`、`make doctor`、`make test` を使います。
