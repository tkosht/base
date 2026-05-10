# Codex Shared Default の例外

## 背景

この template は shared setting として `.codex/config.toml` を track しています。`docs/standards/security.md` の原則は「テンプレートの default は安全側」ですが、Codex の repo-scoped default を毎回 approval prompt 前提にすると、この template が想定する repo-local coding workflow と相性が悪く、shared default と実運用が乖離しやすい状態でした。

一方で、`workspace-write` は安全側の sandbox として望ましいものの、Ubuntu Docker + `devuser` のような一般的な環境では `bwrap` 制約により成立しないケースがあり、template の初期状態をそのままでは再現しにくいことが分かりました。

## 判断

- この template の shipped default は `approval_policy = "never"` を採用する
- shipped default の `sandbox_mode = "danger-full-access"` を採用する
- この設定は maintainer-local convenience ではなく、review 済みの shared setting として docs に明記する
- generated repo は bootstrap 時に `.codex/config.toml` を見直し、自分たちの threat model に合わせて `workspace-write` へ tighten するか、必要なら別の reviewed setting に調整する
- generated repo が `workspace-write` を使う場合は `sandbox_workspace_write.network_access = false` を維持する
- template contract は sandbox mode を 1 つに hard-code せず、supported mode と docs の説明責務を検査する

## 含める説明

- `docs/standards/security.md` に原則と例外を併記する
- `docs/ai/repo-contract.md` に shipped default と generated repo 側の再評価義務を書く
- template contract で `.codex/config.toml` と docs の整合を検査する
