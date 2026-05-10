# Evaluation Loop

## Goal

- instruction simplification が「短くなった」だけでなく、実務タスクで少なくとも非劣性、できれば改善を示すことを確認する。

## Lightweight Loop

1. 変更前後の Always-On 面と `effective always-loaded bytes` を棚卸しする。
2. 静的レビューを行い、adapter 漏れ、deprecated leakage、measurement mismatch を先に潰す。
3. 次の 3 系統で軽量 probe を回す。
   - currentness-sensitive task
   - scoped edit / narrow-edit task
   - review task
4. regressions が出たら、大きい protocol を戻さず、負け筋に対応する最小 bullet を canonical doc に足す。
5. probe が通ったら full rerun に進み、summary metrics で verdict を固定する。

## What To Watch

### Currentness

- broad search で迷走しないこと
- ローカル主張 -> 公式一次情報の順で確認していること
- 結果に確認日、版、URL が残ること

### Scoped Edit

- 近傍実装と対象テストを先に見ていること
- 最小変更になっていること
- `checks_ran` 相当の自前確認が最低 2 本あること
- parent / 外部が担う authoritative gate を unknown 扱いしていないこと

### Review

- finding を 1 つずつ分けていること
- file reference があること
- 関数名、テスト名、契約名など evaluator が拾う固有名詞が落ちていないこと

## When Probe Loses

- currentness が落ちるなら、検索規律と出力要件を 1 bullet で戻す。
- scoped edit が落ちるなら、自前確認と gate reporting の粒度を 1 bullet で補う。
- review recall が落ちるなら、finding 分離と symbol/test naming を 1 bullet で補う。

## Evidence Policy

- commit 対象は summary、preflight、設計メモを優先する。
- heavy run logs は原則 commit せず、必要なら snapshot として別保管する。
- verdict を説明するときは、mean、median、review_recall、gate 系の差分を短く並べる。
