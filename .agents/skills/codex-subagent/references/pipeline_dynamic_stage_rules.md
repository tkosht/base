# Pipeline Dynamic Stage Rules (汎用)

目的
- 動的ステージ（next_stages）を安全に運用し、JSON スキーマ逸脱を防止する。

適用条件
- 不確実性が高い / 追加検証や探索が前提のタスクに限定する。

必須ルール
1) allow_dynamic_stages=true を明示する。
2) allowed_stage_ids に **初期 + 追加候補すべて** を含める。
3) next_stages の要素は **オブジェクトのみ**。必須キーは id。追加キーは prompt / instructions のみ。
4) 1回の stage_result で **追加は最大1件**。
5) 追加は **最大2回まで**（合計ステージ数の上限を守る）。
6) 動的追加条件は /draft.proposal に記録する。
7) stage_result は **単一行 JSON**。文字列の改行は禁止。
8) チェック項目に **不明** が発生したら /open_questions に記録し、可能なら next_stages で verify を追加する。

推奨フォーマット（next_stages）
- 例: "next_stages":[{"id":"verify"}]

フォールバック
- JSON 逸脱が1回でも発生したら、動的追加を停止し固定4ステージに切替える。
