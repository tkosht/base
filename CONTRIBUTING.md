# Contributing

## Before Opening a PR

1. `make doctor`
2. `make lint`
3. `make test`
4. 変更内容に応じて `docs/ai/`、`docs/standards/`、root の `DESIGN.md` を更新

## Pull Request Expectations

- 目的、変更点、検証内容、影響範囲を PR に書く
- shared settings や instruction surface を触る場合は、通常コード以上のレビュー基準で扱う
- visual contract や design guidance を触る場合は、root の `DESIGN.md` が正本であることと sample が reference-only であることを崩さない
- `DESIGN.md` 契約の文言を変える場合は、`docs/ai/repo-contract.md`、`scripts/ci/validate_template.py`、`tests/test_template_contract.py` を同時に見直す
- `DESIGN.md` 契約の文言変更では、最低限 `make doctor` と `uv run pytest -q tests/test_template_contract.py` を実行する
- 新機能では、可能なら TDD または acceptance-test-first で進める

## After Creating a Repo From This Template

- `.github/CODEOWNERS` の placeholder を置換する
- `docs/architecture/overview.md` を実プロジェクト向けに更新する
- root の `DESIGN.md` を generated repo の visual contract として更新する
- `docs/ai/repo-contract.md` のコマンド一覧と protected paths を実値に合わせる
- `docs/design/README.md` は template-maintained な補助面なので、generated repo では通常更新しない
- `.codex/config.toml` と `.claude/settings.json` をチーム運用に合わせて調整する
