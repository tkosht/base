# Commit Message Formats

## simple

```text
<type>: <summary>

Context: <変更の背景>
Changes:
- <主な変更点を1行ずつ>
Test: <確認したテストや手順>
```

- `<type>` は `feat` `fix` `docs` `chore` を優先して選ぶ。
- `<summary>` は 50 文字以内を目安にする。
- `Changes` は変更の事実のみを書く。
- `Test` は実施内容を具体化し、実施なしなら `n/a` を使う。

## super-light

```text
<summary>
Why: <目的やチケット番号>
Verify: <テスト／確認方法 もしくは "n/a">
```

- `<summary>` は 72 文字以内に収める。
- `Why` と `Verify` が自明な場合は行ごと削除してよい。
- Issue 連携が必要なら `Refs: <URL>` を追加する。

## Selection Heuristic

- 原則は `simple` を使う。
- 次のすべてを満たす場合のみ `super-light` を選ぶ。
  - 小規模変更で意図が1行で説明できる。
  - 変更の影響範囲が限定的である。
  - 検証内容が短く `Verify` で十分に表現できる。

## Pre-commit Checks

- コミット前に必ず以下を実行する。
  - `uv run ruff check .`
  - `uv run black --check .`
- `black --check` 失敗時は対象ファイルを `uv run black <path...>` で整形し、再チェック後にコミットする。
- 失敗が `.codex/skills/.system/**` のみなら、local system skill の未整形としてローカルで整形して再チェックする。
- `.codex/*` は `.gitignore` 対象なので、`.codex/skills/.system/**` の整形結果は通常コミット対象に含めない。
