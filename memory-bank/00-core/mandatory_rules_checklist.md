# Mandatory Rules Checklist

- Status: Reference
- Load: OnDemand
- Authority: Operational
- Canonical: `AGENTS.md`

このチェックリストは `AGENTS.md` の要点を、実行前やレビュー前に手早く確認したいときの参照用にまとめたものです。
ここに新しい規範を追加せず、正本の更新が必要なら `AGENTS.md` を修正してください。

## Pre-Flight
- [ ] 変更を伴う作業なら `main` / `master` 以外で進めている
- [ ] 秘密情報や `.env` を露出する操作が含まれていない
- [ ] ローカル探索で足りる事実は先に確認した
- [ ] 最新性や高リスク判断がある場合は一次情報確認の要否を判断した
- [ ] 破壊的操作や無関係な巻き戻しをしない方針が守られている

## During Execution
- [ ] 進捗共有は短く、必要なときだけ行っている
- [ ] 技術事実は説明文ではなく現在のソースオブトゥルースで確認している
- [ ] 複雑なタスクでだけチェックリストや協働プレイブックを使っている

## Before Finish
- [ ] 実行したテストや未実施項目を明記できる
- [ ] 外部調査が判断に影響した場合は `memory-bank/07-external-research/` に記録した
- [ ] 参照切れや古い導線を新たに増やしていない
