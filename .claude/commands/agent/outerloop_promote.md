# outerloop_promote — 昇格判定（Gate MUST）

目的: A/B 比較・ロバスト性・コスト・監査条件に基づき、テンプレートの昇格可否を判定します。

## 前提
- `outerloop_abtest.md` 実行済み（`summary.json` あり）
- `eval_perturb_suite.md` 合格
- 監査ログ: input-hash, rubric_id, template_id, scores, metrics（コスト/レイテンシ）

## 判定（擬似ロジック例）
```bash
AB=.agent/logs/eval/ab/summary.json
jq 'sort_by(.s) | reverse | .[0]' "$AB" > .agent/logs/eval/ab/best.json
cat .agent/logs/eval/ab/best.json

# Gate MUST の簡易チェック（例）
PERT=.agent/logs/eval/perturb.json
PASS_PERT=$(jq -r '.ok' "$PERT")
if [ "$PASS_PERT" != "true" ]; then
  echo "NG: perturbation suite failed" >&2; exit 1
fi

# ここではコスト閾値など必要に応じて追加チェック
```

## 結果
- ベスト候補と Gate MUST 合否をログに記録
- 合格時は `agent_templates_push_pr.md` へ進む

参照: `docs/auto-refine-agents/evaluation-governance.md`

