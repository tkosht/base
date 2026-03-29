# Security Standard

- `.env*` と `secrets/**` は protected path として扱う
- shared MCP / agent settings の追加はレビュー済みのものだけにする
- 公開 repo の runner は GitHub-hosted を基本とし、self-hosted は理由を明示する
- テンプレートの default は安全側に倒し、緩和は generated repo 側で判断する
