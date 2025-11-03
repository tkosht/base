# Task: Agent run with Goal only (Auto Rubric/Artifacts)

## Purpose
Goal 入力だけで自己改善ループを実行し、Rubric/Artifacts は自動生成（RAS/AO）する。

## Inputs
- goal: 実行したい目的/依頼文（文字列）

## Preconditions
- CLI: jq, yq, ripgrep(rg), awk, sed, sqlite3
- Worktree 分離: `.agent/` は worktree 毎に独立（RAG DB 共有禁止）

## Steps
1) Initialize (idempotent)
```bash
[ -d .agent ] || mkdir -p .agent/{state/session_history,generated/{rubrics,artifacts},memory/{episodic,semantic/documents,playbooks},prompts/{planner,executor,evaluator,analyzer},config,logs}
[ -f .agent/memory/semantic/fts.db ] || sqlite3 .agent/memory/semantic/fts.db "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path, content);"
[ -f .agent/config/agent_config.yaml ] || printf "default_config: {}\n" > .agent/config/agent_config.yaml
[ -f .agent/config/loop_config.yaml ]  || printf "default_loop_config: {}\n" > .agent/config/loop_config.yaml
```

2) Run with Goal only (Evaluator I/O v2)
```bash
GOAL="$1"
printf '{"goal":"%s","auto":{"rubric":true,"artifacts":true}}' "$GOAL" \
| tee .agent/logs/eval/input.json \
| jq -r '.' \
| rg -n "(ERROR|FAIL|Timeout)" - || true \
| jq -R -s '{ok:true, scores:{basic:1.0}, notes:["cli-eval (skeleton)"]}' \
| tee .agent/logs/eval/result.json
```

## Artifacts
- Logs: `.agent/logs/`
- Eval snapshots: `.agent/logs/eval/*.json`
- Generated rubric: `.agent/generated/rubrics/*.yaml`
- Orchestrated artifacts: `.agent/generated/artifacts/`

## Notes
- rubric/artifacts を明示指定した場合は自動化は発動しない（後方互換）
- Gate/HITL/監査要件は `docs/auto-refine-agents/evaluation-governance.md` を参照

