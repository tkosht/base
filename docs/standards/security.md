# セキュリティ標準

- `.env*` と `secrets/**` は protected path として扱う
- AI エージェント実行環境での秘密情報保護は `docs/ai/agent-secret-handling.md` を参照する
- shared Model Context Protocol（MCP）設定 / agent settings の追加はレビュー済みのものだけにする
- 公開 repo の runner は GitHub-hosted を基本とし、self-hosted は理由を明示する
- テンプレートの default は原則として安全側に倒し、緩和は generated repo 側で判断する
- 例外として、この template の `.codex/config.toml` は `approval_policy = "never"` と `sandbox_mode = "danger-full-access"` を shipped default にする。これは maintainer-local の取りこぼしではなく、Ubuntu Docker + `devuser` のように `workspace-write` が高確率で成立しない環境でも初期状態から動くようにするための reviewed default である
- generated repo は bootstrap 後に `.codex/config.toml` を threat model に合わせて見直す。`danger-full-access` を維持する場合は、少なくとも mount 範囲、秘密情報、外向き通信、container の破棄容易性を確認する
- generated repo が `workspace-write` に tighten する場合は、`sandbox_workspace_write.network_access = false` を維持し、関連 docs の説明と設定の整合を保つ
