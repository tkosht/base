# 知識面の統合

## 背景

このテンプレートには旧 knowledge surface が残っており、現在の `docs/` と二重の正本に見えやすい状態でした。あわせて、略語だけの説明が現れ、初見の利用者にとって理解コストが高くなっていました。

## 判断

- 長く残す知識は `docs/` と `docs/architecture/decision-records/` に一本化する
- 旧 knowledge surface は live surface から外し、削除する
- primary docs では略語だけで説明しない
- 設計判断を略語だけで呼ばず、「設計判断メモ」に統一する

## 採用した配置

- 実行時に参照する運用知識は `docs/ai/`
- 構造と設計理由は `docs/architecture/`
- 共通ルールは `docs/standards/`
- 入力設計書は `docs/repository-template-design.md` に凍結し、更新は新しい正本へ反映する

## 蒸留して残した知識

- 知識の置き方と読み順
- 実行前の確認表
- 複雑タスク向けのプレイブック
- AI エージェント協調実行で残すべき運用ノウハウ
- ベースハーネス一覧と検証方法

## 残さなかったもの

- 旧ローダー手順
- 旧セッション初期化手順
- `tmux` 中心の組織運用メモ
- dated research note の生データ

これらは現行コンセプトの正本には入れず、必要なら git history で参照する方針とした。
