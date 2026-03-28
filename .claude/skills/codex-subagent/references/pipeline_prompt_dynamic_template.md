# Pipeline Prompt Dynamic Template (汎用)

目的
- 動的ステージ運用時の安全なプロンプト雛形。

テンプレート
```
ROLE: Parent agent orchestration for <topic>
DATE: YYYY-MM-DD

STRICT NO-TOOLS RULE
- Do NOT call any tools or run any commands.
- Use ONLY the FACTS INPUT below. If evidence is missing, mark as 不明.
- Output JSON ONLY (single-line JSON; no line breaks anywhere).

OUTPUT FORMAT (MANDATORY)
- Required keys: schema_version, stage_id, status, output_is_partial, capsule_patch.
- next_stages は必要時のみ。要素は {id} のみ。
- /facts is an array of objects. Each object must include item, evidence, source, status.
- /draft /critique /revise must be objects. /open_questions and /assumptions are arrays.
- All string values must be single-line and must not contain newline or \n.

OBJECTIVE
- <goal>

DYNAMIC CONDITIONS
- next_stages 追加条件を明示（/draft.proposal に記録）。
- 追加は1回につき最大1件。
- 不明があれば next_stages で verify を追加する。

FACTS INPUT (EVIDENCE ONLY)
- <path:line summary>
```
