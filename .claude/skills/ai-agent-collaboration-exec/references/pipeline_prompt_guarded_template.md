# Pipeline Prompt Guarded Template (汎用)

目的
- pipeline stage_result の JSON 逸脱を防ぐための最小プロンプト雛形。

テンプレート
```
ROLE: Parent agent orchestration for <topic>
DATE: YYYY-MM-DD

STRICT NO-TOOLS RULE
- Do NOT call any tools or run any commands.
- Use ONLY the FACTS INPUT below. If evidence is missing, mark as 不明.
- Output JSON ONLY (single-line JSON; no line breaks anywhere).
- 不明は /open_questions に追加する。

OUTPUT FORMAT (MANDATORY)
- Required keys: schema_version, stage_id, status, output_is_partial, capsule_patch.
- /facts is an array of objects. Each object must include item, evidence, source, status.
- /draft /critique /revise must be objects. /open_questions and /assumptions are arrays.
- Do NOT include next_stages.
- All string values must be single-line and must not contain newline or \n.
- Avoid double quotes inside string values.

OBJECTIVE
- <goal>

CHECK ITEMS (exactly N)
1) <item1>
2) <item2>
3) <item3>

FACTS INPUT (EVIDENCE ONLY)
- <path:line summary>
- <path:line summary>
```

運用ルール
- FACTS INPUT には **本文要約 + 行番号** を必ず含める（行番号のみは不可）。
- 長文になりそうなら項目数を減らし、段階分割する。
- 動的ステージが必要な場合は `pipeline_prompt_dynamic_template.md` を使用する。
