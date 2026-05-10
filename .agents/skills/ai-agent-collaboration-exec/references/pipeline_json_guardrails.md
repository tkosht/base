# Pipeline JSON Guardrails (汎用)

目的
- pipeline の stage_result を JSON スキーマに確実適合させ、失敗を再発させないための共通ルール。

失敗パターン（実測）
- capsule_patch 必須なのに欠落
- next_stages 要素が文字列、または id 欠落
- JSON 構文不正（余分な } や区切りミスで JSONDecodeError）
- 出力過大・複数 JSON 混在

ガードレール（必須）
1) stage_result は **単一の JSON オブジェクトのみ** を出力する（補足文禁止）。
2) **単一行 JSON** を強制し、文字列内の改行/\n を禁止する。
3) **capsule_patch は必須**（空配列でも可）。
4) capsule_patch は **1件のみ** を推奨（replace で最小単位を更新）。
5) next_stages は原則使わない（allow_dynamic_stages=false）。動的が必要な場合は `pipeline_dynamic_stage_rules.md` に従う。
6) 出力サイズを最小化（短文、配列は少数件、ネストは浅く）。

再実行時の縮退手順
- 1回目で失敗 → next_stages を削除 → capsule_patch を1件に縮小 → 文字列を短縮。
- 2回目で失敗 → /facts または /draft の **replace 1件のみ** に縮小 →配列は最大3件。
- それでも失敗 → pipeline を中止し、single/multi-single へ切替。

チェックリスト（実行前）
- 必須キーが存在する（schema_version, stage_id, status, output_is_partial, capsule_patch）。
- JSON は単一行で、文字列に改行がない。
- capsule_patch が空でない場合は 1件のみ。
- next_stages を出していない（または id を含むオブジェクト配列）。
