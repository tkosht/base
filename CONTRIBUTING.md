# Contributing

## Before Opening a PR

1. `make doctor`
2. `make lint`
3. `make test`
4. 変更内容に応じて `docs/ai/` または `docs/standards/` を更新

## Pull Request Expectations

- 目的、変更点、検証内容、影響範囲を PR に書く
- shared settings や instruction surface を触る場合は、通常コード以上のレビュー基準で扱う
- 新機能では、可能なら TDD または acceptance-test-first で進める

## After Creating a Repo From This Template

- `.github/CODEOWNERS` の placeholder を置換する
- `docs/architecture/overview.md` を実プロジェクト向けに更新する
- `docs/ai/repo-contract.md` のコマンド一覧と protected paths を実値に合わせる
- `.codex/config.toml` と `.claude/settings.json` をチーム運用に合わせて調整する
