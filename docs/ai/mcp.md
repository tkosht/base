# MCP Policy

## Purpose

shared MCP は便利ですが、外部ツールへの追加権限でもあります。この文書は project-scoped MCP を repo にコミットする条件を定めます。

## Default

テンプレート初期状態の `.mcp.json` は最小構成に保ちます。v1 では汎用的でローカル完結しやすい `sequential-thinking` のみを shared default とします。

## Admission Criteria

shared MCP として採用してよいのは、次を満たすものだけです。

- 利用目的が説明できる
- チーム全体で再利用価値がある
- 権限範囲を説明できる
- 秘密情報の注入方法が明確
- レビューで監査できる

## Rules

- 一時検証用や個人専用の MCP は local/user スコープに留める
- 秘密情報を必要とする MCP は `.env.example` と運用文書を先に整える
- network access や write 権限を広げる設定は、PR で理由を明示する
- `.mcp.json`, `.claude/settings.json`, `.codex/config.toml` はセットで見直す

## Review Checklist

- どの agent が使うか
- どの入力にアクセスするか
- どの権限が必要か
- fallback があるか
- 削除時の影響が限定されるか
