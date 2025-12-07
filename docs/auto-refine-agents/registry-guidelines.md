# Registry 運用ガイドライン（正典）

目的
- 共有正典（Git管理）としての `agent/registry/` の役割・構造・命名・昇格フロー・レビュー基準を定義する。

## 1. 役割と命名
- 単数形の `agent/registry/` を採用（`agents/` は使用しない）
- ランタイム `.agent/`（非Git・worktree専用）とは責務分離
- `memory-bank/` は意思決定・進捗の記録（正典の「なぜ」を残す）

## 2. ディレクトリ構造（例）
```
agent/
  registry/
    prompts/
      templates.yaml
    playbooks/
      *.yaml
    rubrics/
      *.yaml
    config/
      *.defaults.yaml
  snapshots/
    YYYYMMDD-HHMM/
      .agent/config/*
      .agent/prompts/*
```

注意
- `agent/registry/**` は RAG インデクシング対象外（検索は `docs/**` と `memory-bank/**` を用いる）

## 3. 設定優先順位（レイヤリング）
1) `.agent/config/*`（ローカル上書き）
2) `agent/registry/config/*.defaults.yaml`（共有既定）
3) 内蔵デフォルト（設計書の記載）

## 4. 同期モデル
- pull（共有→ローカル）: `agent/registry/** → .agent/**`
- push / 昇格（ローカル→共有）: `.agent/** → PR → agent/registry/**`
  - 参照タスク: `.cursor/commands/agent/agent_templates_pull.md`, `.cursor/commands/agent/agent_templates_push_pr.md`

## 5. 昇格（PR）提出物（必須）
- 差分: `agent/registry/` 配下の更新ファイル
- 監査エビデンス:
  - scores（total/内訳）, logs 抜粋, input-hash, rubric_id, template_id
  - artifacts ハッシュ（入力/成果物）, metrics（cost, latency_ms）
  - 判定根拠抜粋, 実行環境（モデル/バージョン）
- 任意: `agent/snapshots/YYYYMMDD-HHMM/` へのエクスポート一式

## 6. レビューチェックリスト
- Gate MUST 全適合（回帰/ロバスト/コスト/ホールドアウト/監査/HITL）
- 仕様逸脱がない（Rubric/Spec準拠）
- RAG 対象の変更有無と影響の確認（対象は `docs/**`, `memory-bank/**`）
- 命名・配置の一貫性（`agent/registry` / `.agent` / `memory-bank`）

## 7.5 自動生成物（ランタイム）と昇格
- ランタイムの自動生成物は `.agent/generated/{rubrics,artifacts}` に保存（Git管理外）。
- 昇格対象は主に Rubric（`rubrics/*.yaml`）。安定化後に `agent/registry/rubrics/` へ PR として提案する。
- 付帯エビデンス: scores/logs 抜粋、input-hash、rubric_id、template_id、artifacts ハッシュ、metrics、根拠、環境（モデル/バージョン）。
- 既定値の上書きレイヤは以下の順で適用される（再掲）:
  1) `.agent/config/*`（ローカル上書き）
  2) `agent/registry/config/*.defaults.yaml`（共有既定）
  3) 内蔵デフォルト（設計書の記載）

## 7. 運用Q&A
- Q: `.agent/` 内の変更は直接コミットできる？
  - A: できない。PR昇格で `agent/registry/` の正典に反映する。
- Q: registry を RAG に入れない理由は？
  - A: テンプレやルーブリックは設計資産であり、検索は `docs/`/`memory-bank/` を経由するため。

注記（Symlink）: `.cursor/` は `.claude/` へのシンボリックリンクです。表記は `.cursor/commands/agent/*.md` に統一しています。

---
参照: `cli-implementation-design.md`, `worktree-guide.md`, `evaluation-governance.md`

