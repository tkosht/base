---
allowed-tools: Bash(codex:*), Bash(uv run python:*), Bash(timeout:*), Read, Write, Glob, TodoWrite
description: Codex exec subagent for parallel code generation, review, and analysis with competition mode
---

## Quick Reference

```bash
/codex-subagent <task> [options]              # Basic usage
/codex-subagent gen "fibonacci function"       # Code generation
/codex-subagent review "security check"        # Code review
/codex-subagent analyze "architecture"         # Analysis
/codex-subagent doc "API reference"            # Documentation
```

## Options

| Option | Description | Usage | Use Case |
|--------|-------------|-------|----------|
| `-s` | Single mode | `/codex-subagent gen "sort" -s` | Simple, fast tasks |
| `-p` | Parallel mode (N=3) | `/codex-subagent gen "algo" -p` | Info gathering |
| `-c` | Competition mode | `/codex-subagent gen "auth" -c` | Quality-critical |
| `-n N` | Set count (default 3) | `/codex-subagent gen "test" -c -n 5` | More candidates |
| `--json` | JSON output | `/codex-subagent gen "util" --json` | Automation |
| `-v` | Verbose (show scores) | `/codex-subagent gen "api" -c -v` | Debugging |
| `--model MODEL` | codex model override | `/codex-subagent analyze "task" --model gpt-5.3-codex-spark` | A/B evaluation |

## Task Types

| Type | Trigger | Evaluation Focus |
|------|---------|------------------|
| `gen` / `generate` | Code generation | Spec match, tests, minimal diff |
| `review` | Code review | Bug detection, accuracy, coverage |
| `analyze` | Analysis/research | Factuality, reproducibility |
| `doc` / `docs` | Documentation | Accuracy, readability |

## Selection Strategies (Competition Mode)

| Strategy | Flag | Description |
|----------|------|-------------|
| `best_single` | `--strategy best` | Highest combined score |
| `voting` | `--strategy vote` | Consensus + average |
| `hybrid` | `--strategy hybrid` | CORRECTNESS threshold + top |
| `conservative` | `--strategy safe` | Minimal change + passing |

## Usage Patterns

### Basic Usage
```bash
# Simple code generation
/codex-subagent gen "Python function to parse JSON"

# Quick review
/codex-subagent review "check for SQL injection" -s

# Analysis
/codex-subagent analyze "dependency graph" -p
```

### Advanced Usage
```bash
# Competition mode for critical code
/codex-subagent gen "authentication middleware" -c -n 5 --strategy best -v

# Parallel research with merge
/codex-subagent analyze "performance bottlenecks" -p -n 3

# Documentation with JSON output
/codex-subagent doc "API endpoints" --json
```

## Execution

You are a codex-subagent orchestrator. For each request:

1. **Parse task type** from command or keywords:
   - gen/generate/create/implement → CODE_GEN
   - review/check/audit → CODE_REVIEW
   - analyze/investigate/research → ANALYSIS
   - doc/docs/document → DOCUMENTATION

2. **Select execution mode**:
   - Default: SINGLE (fast, simple tasks)
   - `-p`: PARALLEL (gather info, merge)
   - `-c`: COMPETITION (quality-critical)

3. **Execute via codex_exec.py**:
```bash
# Single mode
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single \
  --model gpt-5.3-codex \
  --prompt "$PROMPT" \
  --sandbox read-only

# Logs (default):
# - Any TTY (stdin/stdout/stderr): .codex/sessions/codex_exec/human/...
# - Non-TTY (captured):           .codex/sessions/codex_exec/auto/...
# Override:
# - --log-dir <dir> (log root; writes under <dir>/<human|auto>/...)
# - --log-scope human|auto (classification)
# - env: CODEX_SUBAGENT_LOG_DIR / CODEX_SUBAGENT_LOG_SCOPE

# Competition mode
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition \
  --prompt "$PROMPT" \
  --count $COUNT \
  --task-type $TASK_TYPE \
  --strategy $STRATEGY \
  --sandbox read-only \
  --json
```

補足:
- タイムアウト時は `timed_out=true` / `success=false` / `error_message="Timeout after <N>s"` として扱う。`codex_exec.py` はプロセスグループを終了して残留を避け、`output`/`stderr` は取得できた範囲で保持し `output_is_partial=true` になる。
- 非0終了時は stdout は保持され、stderr は `--json` 出力の `stderr`/`error_message` で確認できる。
- 終了コード: `0=全成功`, `2=サブエージェント失敗`, `3=ラッパー内部エラー`。`parallel` は候補のいずれかが失敗した時点で `2`。
- `--profile fast/very-fast` 指定時、`codex_exec.py` は警告を stderr に出し、ガードレール文をプロンプト先頭へ注入する（それでもタスク分割を優先）。

4. **Post-process**:
   - Extract output from JSON
   - Apply to codebase if needed (via parent agent tools)
   - Report score and rationale

## Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| CORRECTNESS | 40% | Meets requirements, no errors |
| COMPLETENESS | 25% | All requested items present |
| QUALITY | 20% | Readable, maintainable |
| EFFICIENCY | 15% | Fast execution, minimal tokens |

## References

- Prompt templates: `.claude/skills/codex-subagent/references/prompt_templates.md`
- Evaluation criteria: `.claude/skills/codex-subagent/references/evaluation_criteria.md`
- Merge strategies: `.claude/skills/codex-subagent/references/merge_strategies.md`
- Skill definition: `.claude/skills/codex-subagent/SKILL.md`

## Token Efficiency Tips

- Use `-s` for simple tasks (saves ~60% tokens)
- Use `--sandbox read-only` (84x cheaper than full access)
- Avoid `--profile fast/very-fast` by default (lower reasoning); if used, split tasks into micro-prompts
- Limit count with `-n 2` for cost-sensitive tasks
- Use `--json` for automated pipelines
