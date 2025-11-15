# agent_full_cycle — 完全ルート（評価/AB/昇格/PR）

目的: Quickstartの後、摂動ロバスト性→A/B比較→昇格判定→PR提出までのフルサイクルを実行します。ACEにより手動初期化は不要です。

## 実行
```bash
set -euo pipefail

# 1) Goal-only 実行（Evaluator I/O v2 / RAS/AO 自動）
awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_goal_run.md | bash

# 2) 摂動ロバスト性スイート
awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/eval_perturb_suite.md | bash

# 3) ABテスト → 昇格判定 → （合格時）PRエビデンス収集
#    反復上限: MAX_ITERS（優先順位: 環境変数 > loop_config.yaml > 既定1）
MAX_ITERS="${MAX_ITERS:-}"
if [ -z "${MAX_ITERS:-}" ] && command -v yq >/dev/null 2>&1; then
  MAX_ITERS=$(yq -e '.loop.max_iters' .agent/config/loop_config.yaml 2>/dev/null || true)
fi
MAX_ITERS="${MAX_ITERS:-1}"

i=1
PROMOTE_OK=0
while [ "$i" -le "$MAX_ITERS" ]; do
  awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/outerloop_abtest.md | bash
  if awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/outerloop_promote.md | bash; then
    # 合格時のみ
    awk '/^```bash/{flag=1;next}/^```/{if(flag){exit}}flag' ./.cursor/commands/agent/agent_templates_push_pr.md | bash
    PROMOTE_OK=1
    break
  fi
  i=$((i+1))
done

# outerloop が有効（MAX_ITERS>0）の場合は、昇格Gate未達をエラーとして伝播
if [ "$MAX_ITERS" -gt 0 ] && [ "$PROMOTE_OK" -ne 1 ]; then
  echo "NG: promotion gate not satisfied within MAX_ITERS=$MAX_ITERS" >&2
  exit 1
fi
```

## 成果物
- `.agent/logs/**` 一式（入力/結果/AB/ロバスト）
- `pr_evidence/**`（昇格PR添付）

参照: `docs/auto-refine-agents/evaluation-governance.md`
