# .cursor/commands シンボリックリンクメモ

- `.cursor/commands` は `.claude/commands/` へのシンボリックリンク（`ls -l .cursor` で確認）。
- 実体は `.claude/commands/` 側にあり、どちらのパスでも同一ファイルにアクセス可能。
- パス表記の揺れがレビュー指摘になりやすいので、ドキュメントやスクリプトでは `.claude/commands/` を正準パスとして記載するのが無難。
