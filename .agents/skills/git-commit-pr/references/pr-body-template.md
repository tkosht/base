# PR Body Template

## standard

```text
## Context
- <背景>

## Changes
- <変更点1>
- <変更点2>

## Test
- <実行した検証>
```

- `Context` は変更理由を簡潔に書く。
- `Changes` はレビューで追える粒度にする。
- `Test` は実行コマンドまたは手動確認手順を書く。

## compact

```text
## Why
- <目的>

## Verify
- <検証手順 または n/a>
```

- 小規模変更でのみ使う。
- Issue やチケットがある場合は末尾に `Refs: <URL>` を追加する。
