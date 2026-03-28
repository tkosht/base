# Pipeline Dynamic Test Run Template (汎用)

目的
- 動的ステージ (next_stages) を実運用で安全に使うためのテスト実行テンプレート。

前提
- 動的ステージ用 spec: `references/pipeline_spec_dynamic_safe.json`
- 動的ステージ用 prompt: `references/pipeline_prompt_dynamic_template.md`

手順
1) spec 検証
```
uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov
```

2) prompt を用意（FACTS INPUT は本文要約 + 行番号）
- 例: docs/ai-agent-reviews/<topic>_dynamic_prompt_YYYY-MM-DD.txt
- 重要: 文字列に改行を入れない、next_stages は {id} のみ

3) pipeline 実行
```
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline \
  --pipeline-spec .claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_dynamic_safe.json \
  --capsule-store auto \
  --sandbox read-only \
  --timeout 600 \
  --json \
  --prompt "$(cat <PROMPT_FILE>)"
```

成功条件
- wrapper exit code = 0
- JSON の success=true
- stage_results の status が全て ok
- next_stages がある場合、要素は {id} のみ

失敗時の対応
- `pipeline_json_guardrails.md` を再確認
- 文字列の改行、capsule_patch 欠落、next_stages 形式違反がないか確認
- 1回失敗で出力サイズを半減（配列数削減、短文化）
- 2回失敗で固定4ステージにフォールバック
