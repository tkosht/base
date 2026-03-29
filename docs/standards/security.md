# セキュリティ標準

- `.env*` と `secrets/**` は protected path として扱う
- shared Model Context Protocol（MCP）設定 / agent settings の追加はレビュー済みのものだけにする
- 公開 repo の runner は GitHub-hosted を基本とし、self-hosted は理由を明示する
- テンプレートの default は原則として安全側に倒し、緩和は generated repo 側で判断する
- 例外として、この template の `.codex/config.toml` は `approval_policy = "never"`、`sandbox_mode = "workspace-write"`、`network_access = false` を shipped default にする。これは maintainer-local の取りこぼしではなく、repo-local coding workflow 向けにレビュー済みの既定値である
- 上の例外でも `danger-full-access` は既定にしない。generated repo が `danger-full-access` を選ぶ場合は、少なくとも mount 範囲、秘密情報、network egress、container の破棄容易性を見直してから明示的に変更する
