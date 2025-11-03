# agent_templates_push_pr — ランタイム → 正典 昇格PR提出

目的: `.agent/**` の有用変更（テンプレ/設定/ルーブリックなど）を `agent/registry/**` へ昇格提案（PR）します。

## 前提
- Gate MUST を満たす監査エビデンスが揃っている（`evaluation-governance.md` 参照）
- ブランチ: `feature/* | task/*` 等

## 収集（必須エビデンス例）
```bash
mkdir -p pr_evidence
cp -v .agent/logs/eval/result.json pr_evidence/
# 例: 入力ハッシュ/テンプレID/コスト/レイテンシ抜粋
jq '{input_hash, rubric_id, template_id, scores, metrics}' .agent/logs/eval/result.json > pr_evidence/summary.json
```

## 昇格（例）
```bash
# rubrics を昇格（必要に応じ該当ファイル）
mkdir -p agent/registry/rubrics
cp -v .agent/generated/rubrics/*.yaml agent/registry/rubrics/

git add agent/registry/rubrics pr_evidence
git commit -m "chore(registry): promote rubric from runtime with evidence"
# upstream へ PR（ホストに応じて実施）
```

## PR テンプレ（要点）
- 対象差分: `agent/registry/**`
- 監査: scores/logs 抜粋, input-hash, rubric_id, template_id, artifacts ハッシュ, metrics
- HITL: 承認者/理由/チケットID
- リスク: 回帰/ロバスト性/コストへの影響

参照: `docs/auto-refine-agents/evaluation-governance.md`, `registry-guidelines.md`

