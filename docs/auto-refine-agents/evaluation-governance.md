# 評価ガバナンス指針（Rubric/HITL/監査/プロモーション）

本ドキュメントは、`cli-implementation-design.md` の Inner-Loop/Middle-Loop における評価健全性を担保するための標準を定義する。テンプレート最適化を主手段とし、モデル学習は対象外（将来拡張）。

## 1. Rubric 定義規約（YAML）
- 目的: 要件を実行可能な形で宣言し、機械判定の一貫性を確保
- 必須キー（最小）
```yaml
id: code_quality_v1
version: 1
objectives:
  - name: "spec_compliance"
    weight: 0.4
  - name: "robustness"
    weight: 0.3
  - name: "cost_efficiency"
    weight: 0.2
  - name: "runtime_reliability"
    weight: 0.1
checks:
  - name: "no_errors_in_logs"
    detector: "rg -n '(ERROR|FAIL|Timeout)' logs/ | wc -l"
    expect: "== 0"
    weight: 0.4
  - name: "spec_tests_pass"
    detector: "bash tests/spec_run.sh"  # 0=pass
    expect: "exit_code == 0"
    weight: 0.3
  - name: "perturbation_robust"
    detector: "bash tests/perturbation_suite.sh"  # シャッフル/ノイズ
    expect: "exit_code == 0"
    weight: 0.2
  - name: "budget_within_limit"
    detector: "jq '.total_cost' artifacts/metrics.json"
    expect: "<=  budget.max_cost"
    weight: 0.1
thresholds:
  pass_score: 0.9
  hard_fail_checks: ["no_errors_in_logs", "spec_tests_pass"]
metadata:
  owner: "platform"
  description: "Spec準拠 + ロバスト性 + コスト上限を評価"
```

補足:
- detector は CLI コマンドや正規表現。戻り値と `expect` の比較で判定。
- `thresholds.pass_score` 以上かつ `hard_fail_checks` 非違反で合格。

## 2. Evaluator I/O（JSON 標準）
- 入力（stdin）
```json
{
  "task_id": "uuid",
  "rubric": {"id":"code_quality_v1","version":1,...},
  "artifacts": ["logs/app.log","artifacts/metrics.json"],
  "budget": {"max_cost": 1.50}
}
```
- 出力（stdout）
```json
{
  "ok": true,
  "scores": {"total": 0.93, "spec_compliance": 1.0, "robustness": 0.9},
  "notes": ["no error found", "perturbation suite passed"],
  "evidence": {"failed_checks": [], "raw": {"no_errors_in_logs":0}},
  "metrics": {"cost": 1.12, "latency_ms": 8200},
  "rubric_id": "code_quality_v1@1"
}
```
- 退出コード: 0=実行成功（評価可能）、>0=評価系エラー（Rubric不備等）。

## 3. ロバスト性・反チート
- 摂動テスト: 並べ替え/シャッフル/軽微ノイズ/境界ケースを混在
- 反チート: 
  - 非公開ホールドアウト/ネガティブコントロール混入
  - ImpossibleBench 類似の「抜け道」検知を最小導入
  - ルール・テキストへの過適合を監査ログで検出

## 4. プロモーション・ゲート（テンプレ昇格条件）
- Gate MUST（全て満たす）
  1) 回帰スイート全合格（spec）
  2) ロバスト性スイート合格（摂動・ノイズ）
  3) コスト閾値内（SLO）
  4) ホールドアウト合格（リーク無し）
  5) 監査ログ完備（再現可能）
  6) HITL 承認（責任者サイン）
- Gate SHOULD（望ましい）
  - A/B 有意: 反復 n≥5、片側 t 検定など簡易基準で優越性を確認
- 不合格時: 直前安定版テンプレへロールバック（自動降格）

## 5. 監査ログ（必須項目）
- `task_id`, 時刻, 入力ハッシュ, rubric_id, template_id, scores, checks結果, artifactsハッシュ, コスト・レイテンシ, 判定根拠（抜粋）, 実行環境（モデル/バージョン）

## 6. HITL（Human-in-the-Loop）
- 昇格時のみ必須。承認者/理由/チケットIDを記録。
- 緊急降格は運用権限者が実施（手順はプラットフォーム標準に準拠）。

## 7. 可視化・運用
- ダッシュボード/リプレイの最小要件: スコア遷移、失敗チェック分布、コスト時系列、CheatingRisk 指標。
- ログ保存期間はプロジェクト標準に従う（例: 90日）。

## 8. 昇格PR提出物（必須）
- 対象ファイル（正典）: `agent/registry/` 配下の差分（prompts/playbooks/rubrics/config/*.defaults.yaml）
- 監査エビデンス（添付/リンク）:
  - scores（total/内訳）, logs 抜粋, input-hash, rubric_id, template_id
  - artifacts ハッシュ（入力/成果物）, metrics（cost, latency_ms）
  - 判定根拠抜粋, 実行環境（モデル/バージョン）
- スナップショット（任意）: `.agent/{config,prompts}` の現用セットを `agent/snapshots/YYYYMMDD-HHMM/` として同梱可
- 満たすべき基準: 本書「Gate MUST」全項目への適合宣言 + HITL 承認者/理由/チケットID
- 手順参照: `.cursor/commands/agent/agent_templates_push_pr.md`

## 9. AutoRubric（RAS）運用指針（追加）
- 乾式検証（detector dry-run）を必須とし、不成立チェックは自動で除外/無効化する。
- 重み最適化: 直近の実行履歴（スコア/失敗分布）を用い `objectives.weight` を漸進調整（均等→学習済み）。
- しきい値調整: Gate 境界に張り付く場合は `thresholds.pass_score` を微調整。
- 監査: 生成元シグナル、rubricハッシュ、学習履歴（世代ID）を保存（再現可能性）。
- 保存場所（ランタイム）: `.agent/generated/rubrics/*.yaml`, `.agent/state/rubric_history.json`

## 10. Artifacts Orchestrator（AO）運用指針（追加）
- 既定の評価対象を標準化: `logs/app.log`, `artifacts/metrics.json`。無い場合は作成。
- 収集/生成: エラーログの集約、メトリクスの最小JSON生成（取得不能時）。
- 整合: RAS が参照する `checks` と `artifacts` の一致を強制（不整合の自動修正）。
- 監査: 収集/生成の根拠、入力ハッシュ、空生成の有無を保存。
- 保存場所（ランタイム）: `.agent/state/artifacts_map.json`, `.agent/logs/eval/*.json`

## 11. 自動生成 Rubric の昇格PR要件（追加）
- 差分: `agent/registry/rubrics/` への PR（対象Rubricの追加/更新）。
- 監査エビデンス（追加要件）:
  - RAS 生成元シグナルの要約、rubricハッシュ、世代ID、比較対象（Before/After）の失敗分布と改善差分
  - AO 生成/整形の根拠（入力ファイル一覧、空生成の扱い）
- 前提: Gate MUST 満たすこと + HITL 承認

---
参照:
- `cli-implementation-design.md` 4.3.4/4.3.5/8.3
- `architecture.md` 通信/標準/安全, 評価者ノード

注記（Symlink）: `.cursor/` は `.claude/` へのシンボリックリンクです。表記は `.cursor/commands/agent/*.md` に統一しています。

