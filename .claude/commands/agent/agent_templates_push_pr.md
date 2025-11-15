# agent_templates_push_pr — ランタイム → 正典 昇格PR提出

目的: `.agent/**` の有用変更（テンプレ/設定/ルーブリックなど）を `agent/registry/**` へ昇格提案（PR）します。

## 前提
- Gate MUST を満たす監査エビデンスが揃っている（`evaluation-governance.md` 参照）
- ブランチ: `feature/* | task/*` 等

## 昇格（例）
```bash
set -euo pipefail

# rubrics を昇格（必要に応じ該当ファイル）
mkdir -p agent/registry/rubrics

# 生成済み Rubric が無い場合は、昇格処理をスキップ（MVPスケルトン対応）
shopt -s nullglob
RUBRICS=(.agent/generated/rubrics/*.yaml)
if [ "${#RUBRICS[@]}" -eq 0 ]; then
  echo "INFO: .agent/generated/rubrics に昇格対象Rubricが無いため、今回のPR昇格はスキップします。" >&2
  exit 0
fi

cp -v "${RUBRICS[@]}" agent/registry/rubrics/

git add agent/registry/rubrics
git commit -m "chore(registry): promote rubric from runtime"
# upstream へ PR（ホストに応じて実施）
```

## PR テンプレ（要点）
- 対象差分: `agent/registry/**`
- 監査: scores/logs 抜粋, input-hash, rubric_id, template_id, artifacts ハッシュ, metrics
- HITL: 承認者/理由/チケットID
- リスク: 回帰/ロバスト性/コストへの影響

参照: `docs/auto-refine-agents/evaluation-governance.md`, `registry-guidelines.md`
