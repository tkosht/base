# AI エージェント実行環境の秘密情報保護

- Status: OnDemand
- Last reviewed: 2026-04-24

## Purpose

AI エージェントがリポジトリを読める環境では、`.env`、認証トークン、クラウド鍵、OAuth 認証情報、`secrets/**` などを読み取れること自体が主要なリスクになる。この文書は、AI エージェント実行環境で現実的に有効な秘密情報保護の方針をまとめる。

この文書は運用メモであり、正本の保護対象は `AGENTS.md` と `docs/ai/repo-contract.md` の Protected Paths に従う。

## Summary

最も有効な対策は、AI エージェントに「秘密情報を読まないよう指示する」ことではなく、AI エージェントの実行環境から秘密情報を物理的・権限的に外すことである。

優先順位は次の順に置く。

1. 秘密情報をワークスペースに置かない
2. AI エージェント実行環境をサンドボックス化し、ファイルとネットワークを allowlist 方式にする
3. 長命キーを減らし、短命・用途限定・監査可能な認証情報へ移行する
4. AI エージェントに秘密値を返さない broker 方式を使う
5. secret scanning と revoke / rotate を前提にした事故対応を整える

## Threat Model

AI エージェント環境では、次の経路で秘密情報が露出しうる。

- モデルまたはツールが `.env*`、`secrets/**`、ホームディレクトリ配下の認証ファイルを読む
- シェル、Python、Node.js、Model Context Protocol（MCP）サーバー経由で protected path を間接的に読む
- プロンプトインジェクションにより、issue、pull request、依存ファイル、外部ページから秘密情報の読み出しや送信を誘導される
- ログ、pull request 本文、issue コメント、AI 応答、テスト出力に秘密値が混入する
- 継続的インテグレーション（CI）や AI action に過大な repository 権限や secrets が渡される

このため、プロンプト上の禁止、運用注意、`.gitignore` だけでは十分ではない。

## Controls

### 1. Workspace から秘密情報を外す

- リポジトリには `.env.example` だけを置く
- 実値の `.env` は AI エージェント用 checkout に置かない
- ローカル開発者用の `.env` と AI エージェント実行環境は、別ユーザー、別コンテナ、別仮想マシン、別マウントで分離する
- AI エージェント環境に `~/.aws`, `~/.ssh`, `~/.config/gh`, password manager の認証済みセッションを置かない

`.gitignore` はコミット混入を防ぐ補助策であり、AI エージェントによる読み取り防止策ではない。

### 2. Sandbox と権限を最小化する

- ファイルシステムは allowlist 方式を優先する
- ネットワークは既定 deny とし、必要な公式ドメインだけを許可する
- shell、Python、Node.js などの汎用実行権限は、protected path の read deny を迂回できる点を考慮して付与する
- MCP サーバーは AI エージェントに追加権限を与える実行面として扱い、目的、入力、権限、秘密情報の注入方法をレビューする
- write 権限や外向き通信を広げる設定は、pull request で理由を明示する

ツール側の `Read` deny は有用だが、汎用シェルが同じ環境で自由に動ける場合は単独の防御境界として扱わない。

### 3. 短命・用途限定の認証へ寄せる

- GitHub Actions などの CI では、可能な限り OpenID Connect（OIDC）でクラウド側から短命 credential を取得する
- 長命の cloud access key を GitHub Secrets や `.env` に複製しない
- Vault などの secret manager では dynamic secrets を使い、要求時に短命・一意の credential を発行する
- Application Programming Interface（API）キーを使う場合も、用途別、権限最小、期限付き、即時ローテーション可能にする

AI エージェントから漏れて困る長命キーを置かないことが、漏洩時の影響を最も小さくする。

### 4. Broker 方式で秘密値を返さない

AI エージェントが秘密値を直接読む必要を減らすため、次のような broker 方式を優先する。

1. AI エージェントは `integration-test` や `deploy-preview` のような限定ツールを呼ぶ
2. ツール側だけが secret manager から値を取得する
3. 秘密値は子プロセス環境や一時ファイルに閉じ込め、ログは redact する
4. AI エージェントには成功、失敗、差分、要約だけを返す

この方式では、AI エージェントがキーそのものを知る必要がなくなる。

### 5. Detection と Incident Response を前提にする

- GitHub Secret Scanning と Push Protection を有効にする
- `gitleaks`、`trufflehog`、`detect-secrets` などを pre-commit と CI に入れる
- commit 差分だけでなく、AI 応答、pull request 本文、issue コメント、ログ、成果物にも secret scanning をかける
- 漏洩時は履歴削除より先に revoke / rotate を行う
- ローテーション手順と所有者を運用文書に残す

secret scanning は最後の防波堤であり、秘密情報を AI エージェント環境に置かない設計を置き換えるものではない。

## Current Repo Notes

2026-04-24 時点の確認では、次の状態だった。

- `.gitignore` は `.env*` を無視し、`.env.example` だけを例外許可している
- Protected Paths は `AGENTS.md` と `docs/ai/repo-contract.md` に定義されている
- `.codex/config.toml` は reviewed default として `sandbox_mode = "danger-full-access"` を採用している
- `.claude/settings.json` は複数の read / shell 系コマンドを許可している
- `.pre-commit-config.yaml` に secret scanner は入っていない
- `.github/workflows/claude.yml` は AI action に write 権限と Claude OAuth secrets を渡している

この repository template では、生成先 repository の threat model に応じて、`.codex/config.toml`、`.claude/settings.json`、AI action、secret scanning を見直す。

## Recommended Local Changes

生成先 repository で優先して検討する変更は次のとおり。

1. AI エージェント用環境には実値の `.env` を置かない
2. `.claude/settings.json` で `Read(./.env)`, `Read(./.env.*)`, `Read(./secrets/**)` などを deny する
3. Codex の sandbox を `workspace-write` または read-only に寄せ、ネットワークを既定 off にする
4. AI action の `permissions` を job ごとに最小化し、write job と secrets 利用 job を trusted actor、protected environment、手動承認で分ける
5. GitHub Secrets の長命クラウド鍵を OpenID Connect（OIDC）や dynamic secrets に置き換える
6. pre-commit と CI に secret scanning を追加する
7. 漏洩時の revoke / rotate 手順を owner 付きで文書化する

## Sources

- OWASP: [LLM02: Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/)
- OWASP: [LLM06: Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- OpenAI: [Safety in building agents](https://developers.openai.com/api/docs/guides/agent-builder-safety)
- Anthropic: [Claude Code Security](https://code.claude.com/docs/en/security)
- Model Context Protocol: [Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- GitHub: [About secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/about-secret-scanning)
- GitHub: [About push protection](https://docs.github.com/en/code-security/concepts/secret-security/about-push-protection)
- GitHub: [OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect)
- HashiCorp Vault: [Dynamic secrets](https://developer.hashicorp.com/hcp/docs/vault-secrets/dynamic-secrets)
- Docker: [Secrets](https://docs.docker.com/engine/swarm/secrets/)
- Docker: [SecretsUsedInArgOrEnv](https://docs.docker.com/reference/build-checks/secrets-used-in-arg-or-env/)
- Kubernetes: [Good practices for Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)
