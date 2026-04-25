# Codex 経験捕捉

## Purpose

この文書は、この repo 上で動くすべての Codex agent が、日々のタスク経験をどのように残すかを定義します。目的はログを増やすことではなく、将来の agent 行動をより単純・一貫・安全・自律的にする知識だけを蒸留して残すことです。

## Self-Audit

Codex agent は、タスク終了時、ユーザー訂正時、gate 異常時、実装複雑化を見つけた時、または instruction surface の矛盾を見つけた時に、軽量 Self-Audit を行います。

中心問いは次です。

> この経験は、将来の Codex agent の行動をより単純・一貫・安全・自律的にする形へ圧縮できるか。

見るべきものは固定リストではありません。実装で不要な分岐・状態・引数・責務混入が増えていないか、ハーネスとしてより効果的な rule や validator にできないか、矛盾した rule は authority と scope で解消できるか、不要な rule を消せないか、不足する rule を最小の形で足せないかを判断します。

ユーザー訂正により保持価値のある経験候補を見つけたが、Plan Mode などで repo-tracked state を変更できない場合は、会話中で pending ExperienceCandidate として明示します。書き込み可能になってから docs、skill prompt、test、validator、設計判断メモ、または非追跡 state へ昇格・棄却を行います。「保持対象」とだけ述べて終わらせず、保留理由、候補の要約、想定 placement を通知します。

## Retention

経験はすべて残しません。残す条件は、再発可能性がある、影響が大きい、一般化できる、検証できる、常時 context cost を上回る価値があることです。

保持先は次の順で選びます。

- discard: 一回限り、検証不能、既存 rule で十分、または残すとノイズになる。
- sanitized non-tracked state: 信号はあるが、まだ永続化には弱い。
- code simplification: ルール追加より実装を単純にする方がよい。
- test or validator: 実行可能な検証が prose より強い。
- skill prompt: 特定 skill の行動だけを変える。
- canonical rule: repo-wide の Codex 行動を変える。
- 設計判断メモ: 将来の保守者に配置や authority の理由を残す必要がある。

## What Not To Keep

raw prompt、raw model output、秘密情報、`.env*`、`secrets/**`、runtime logs、巨大ログ、一回限りの試行錯誤は tracked knowledge にしません。必要な場合も sanitized summary だけを非追跡 state に残します。

## Placement

`AGENTS.md` には短い always-on 契約だけを置きます。詳細な運用契約は `docs/ai/repo-contract.md`、この文書、skill 固有 prompt に置きます。

Markdown rule は instruction surface として扱います。rule を永続化する時は、scope、authority、trigger、expected behavior、validation、retirement condition を確認します。矛盾に見える rule は、まず authority と scope で解消し、解消できない場合は canonical surface へ統合して adapter 側の重複を削ります。

## Harness Autoptimizer

`harness-autoptimizer` は日常タスクの唯一の入口ではありません。全 Codex agent が得た経験候補を評価し、棄却、非追跡 state、code simplification、test、validator、skill prompt、canonical rule、設計判断メモのどれにするかを判断する optimizer です。
