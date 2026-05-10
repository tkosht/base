# Harness Autoptimization Resource Registry

- Status: Accepted
- Date: 2026-04-24

## Context

この repo は skill だけでなく、instruction surface、knowledge docs、settings、template、validation tests を合わせて AI agent harness として機能する。`codex-subagent` の自己最適化だけを直接実装すると、Skill 以外の harness 面を安全に広げる判断材料が不足する。

## Decision

`docs/architecture/harness-resources.toml` を harness resource registry として追加する。各 resource は `kind`、`paths`、`mutable_paths`、`authority`、`depends_on`、`validators`、`mutation_policy`、`risk_level`、`goals` を持つ。

`harness-autoptimizer` は registry を読み、対象 resource の `mutable_paths` と `validators` を使って候補生成、diff guard、通常ゲート、pull request 作成を制御する。v1 は `codex-subagent` の安定性を初期対象にし、Skill 以外の harness は registry と評価モデルだけを先に定義する。

## Consequences

- Skill は harness resource の一種として扱われ、docs や settings と同じ制御面で評価できる。
- 自律編集範囲は resource ごとの `mutable_paths` に閉じられる。
- 評価器を追加する前でも、registry により将来の拡張対象とリスク分類を明示できる。
- 自動 pull request は小粒に保ち、`make doctor`、`make lint`、`make test` を通過した候補だけを採用する。
