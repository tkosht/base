# セキュリティ標準

- `.env*` と `secrets/**` は protected path として扱う
- AI エージェント実行環境での秘密情報保護は `docs/ai/agent-secret-handling.md` を参照する
- shared Model Context Protocol（MCP）設定 / agent settings の追加はレビュー済みのものだけにする
- 公開 repo の runner は GitHub-hosted を基本とし、self-hosted は理由を明示する
- テンプレートの default は原則として安全側に倒し、緩和は generated repo 側で判断する
- 例外として、この template の `.codex/config.toml` は `approval_policy = "never"` と `sandbox_mode = "danger-full-access"` を shipped default にする。これは maintainer-local の取りこぼしではなく、Ubuntu Docker + `devuser` のように `workspace-write` が高確率で成立しない環境でも初期状態から動くようにするための reviewed default である
- generated repo は bootstrap 後に `.codex/config.toml` を threat model に合わせて見直す。`danger-full-access` を維持する場合は、少なくとも mount 範囲、秘密情報、外向き通信、container の破棄容易性を確認する
- generated repo が `workspace-write` に tighten する場合は、`sandbox_workspace_write.network_access = false` を維持し、関連 docs の説明と設定の整合を保つ

## Public base repo workflow defaults

- この base repo は public template として、workflow の意図を残しつつ secret 未設定時に強い AI 実行へ進まない default にする
- `.github/workflows/harness-autopt.yml` は schedule を持つが、`CODEX_AUTH_JSON` が未設定なら最初の auth check で成功終了し、checkout、依存 install、Codex 実行、`GH_TOKEN` 利用へ進まない
- `CODEX_AUTH_JSON` を設定した repo では schedule 実行が有効になる。secret を追加する時は、定期実行させる意思があるかを同時に確認する
- `.github/workflows/claude.yml` は `@claude` 起動を `OWNER`、`MEMBER`、`COLLABORATOR` に限定し、Claude action は commit SHA に pin する
- repo secrets がない public base repo で残る主なリスクは、schedule run の履歴ノイズ、わずかな runner 消費、将来 secret を追加した時に write 権限付き AI workflow が有効化されること
- generated repo へ継承する時は、workflow permission、required secrets、trusted actor、schedule の要否、Actions 履歴ノイズを移植先の運用に合わせて見直す
