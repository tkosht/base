# Skills Notes

## ai-agent-collaboration-exec

### Dependency Checks (examples)
- codex binary: `command -v codex`
- jsonschema availability: `uv run python -c "import jsonschema"`

### Input Handoff
- review_output_dir has no codex-subagent CLI parameter; pass via prompt/artifact paths.
- Example default review_output_dir: `docs/ai-agent-reviews/`.

### Defaults / Workflow Policy
- allow_dynamic_stages default: false when not set in pipeline spec (codex_exec.py).
- retry limit: not implemented in codex_exec; must be defined by workflow (e.g., 2).

### Naming Guidance
- Recommended artifact naming (from execution_framework.md):
  - `<review_output_dir>/<topic>_design_<YYYY-MM-DD>.md`
  - `<review_output_dir>/<topic>_review_<YYYY-MM-DD>_roundN.md`
  - `<review_output_dir>/<topic>_test_method_<YYYY-MM-DD>.md`
  - `<review_output_dir>/<topic>_notes_<YYYY-MM-DD>.md`

### Pipeline Spec Validation
- Example validation command:
  - `uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov`

### Repo Test Command (note)
- Internal docs example: `poetry run pytest -v .`
- README/Makefile/package.json do not define a standard test command.
