# リポジトリ運用契約

## Purpose

この文書は、このテンプレートから生成された repo における人間と AI エージェントの共通運用契約です。`AGENTS.md` と `CLAUDE.md` は入口であり、ここが詳細の正本です。

## Reading Order

1. `README.md`
2. `AGENTS.md` または `CLAUDE.md`
3. `docs/ai/repo-contract.md`
4. `docs/ai/experience-capture.md`
5. `docs/architecture/overview.md`
6. `docs/architecture/knowledge-architecture.md`
7. `docs/standards/*.md`

design 系作業では、root の `DESIGN.md` を先に読み、必要に応じて `docs/design/README.md` を補助面として読む。

## Repository Roles

- `README.md`: 人間向けの全体像と初動
- `AGENTS.md`: Codex / agent 向けの短い永続指示
- `CLAUDE.md`: Claude Code 向けの薄いアダプタ
- `DESIGN.md`: generated repo の visual contract の正本
- `docs/ai/`: AI 向けの詳細契約、Model Context Protocol（MCP）方針、実行プレイブック、skill reference
- `docs/ai/experience-capture.md`: Codex agent の経験捕捉と保持判断の正本
- `docs/design/README.md`: root `DESIGN.md` を支える design guidance の canonical な補助面
- `docs/design/samples/**`: reference-only の sample。canonical surface ではない
- `docs/architecture/`: 構造、知識配置、ハーネス一覧、設計判断メモ
- `docs/standards/`: 実装、テスト、セキュリティ、レビュー、コミュニケーションの標準
- `.codex/`, `.claude/`, `.agents/`, `.github/`: 行動規範を変えうる shared settings

## Default Workflow

- まずローカルのソース、設定、テスト、コマンド結果を確認する
- 新機能では可能なら失敗テスト先行か受け入れテスト先行で進める
- 狭い編集では最小変更と近接検証を優先する
- `main` / `master` に直接変更しない
- 破壊的操作は明示依頼なしで行わない
- shared settings と GitHub governance の変更は通常コード以上のレビュー基準で扱う

## Test Modes

- `make test`: ChatGPT ログインを必要としない通常テストだけを実行する
- `make test-codex-live`: ChatGPT にログイン済みのローカル端末でだけ、`codex exec` を実際に呼ぶ実行テストを実行する
- 通常の GitHub Actions は `make test` を使い、Codex 実行テストは標準の継続的インテグレーション（CI）に含めない
- 実行テストの前に `make bootstrap` で `codex` のコマンドラインツール（CLI）を導入し、`codex` を一度起動して ChatGPT にログインしておく

## Protected Paths

- `.env*`
- `secrets/**`
- 認証トークン、鍵、OAuth 認証情報
- local-only settings: `.claude/settings.local.json`, `.claude/.claude/**`
- Codex / Claude の runtime state: `.codex/auth.json`, `.codex/history.jsonl`, `.codex/log*`, `.codex/state*.sqlite`

これらは値の表示、コミット、PR 本文への貼り付けを禁止します。

## Settings Ownership

- `.claude/settings.json`: Claude Code の shared project settings
- `.codex/config.toml`: Codex のコマンドラインツール（CLI）向け repo-scoped defaults
  この template の shipped default は `approval_policy = "never"` と `sandbox_mode = "danger-full-access"`。maintainer-local override ではなく、review 済みの shared setting として扱う。generated repo は threat model に応じて `workspace-write` へ tighten してよく、その場合は `sandbox_workspace_write.network_access = false` を保つ。`danger-full-access` を維持する場合は、mount 範囲、秘密情報、外向き通信、container の破棄容易性を見直す
  `features.goals = true` は `/goal` の利用面を開くための shared default だが、goal session はユーザーが明示的に指示した場合だけ開始する。generated repo がこの実験的な利用面を不要と判断する場合は、`.codex/config.toml` の `[features]` block を削除して repo 単位の明示 opt-in に戻してよい
- `.mcp.json`: Claude 向け shared Model Context Protocol（MCP）設定
- `.agents/skills/`: repo-local skill entrypoint の正本
- `.claude/skills/`: Claude 向け互換 shim
- `.codex/skills/`: Codex 互換 shim

## Reporting Contract

- 実装報告では、変更結果と検証結果を分けて書く
- テスト駆動開発（TDD）を外した場合は理由と代替検証を書く
- 未実施 gate は `unknown` ではなく未実施 gate として分けて書く
- レビューでは finding ごとに分け、関数名・テスト名・契約名を明記する

## Experience Capture Contract

- この repo 上で動く Codex agent は、通常タスクの終了時、ユーザー訂正時、gate 異常時、実装複雑化や instruction surface の矛盾を見つけた時に、経験を将来の行動改善へ残すべきかを軽量に判断する
- 経験捕捉は `harness-autoptimizer` 経由の実行に限定しない。`harness-autoptimizer` は経験候補を評価し、棄却、非追跡 state、code simplification、test、validator、skill prompt、canonical rule、設計判断メモのどれにするかを判断する optimizer とする
- raw prompt、raw model output、秘密情報、runtime logs、巨大ログ、一回限りの作業メモは tracked knowledge に昇格しない。必要な場合も sanitized summary だけを非追跡 state に残す
- repo に永続化できるのは、蒸留済みの rule、test、validator、設計判断メモ、または code simplification だけとする
- 人間が `TARGET` / `GOAL` / guarded pull request flag を指定することを、自律改善の制御機構にしない。Codex agent が evidence から resource、goal、confidence、constraints を判断する
- Plan Mode などで repo-tracked state を変更できない時に保持価値のある経験候補を見つけた場合は、pending ExperienceCandidate として会話中に明示し、保留理由と想定 placement を残す
- 詳細な保持判断は `docs/ai/experience-capture.md` に従う

## Design Synchronization Policy

- repo 内で canonical 名の `DESIGN.md` を使うのは root だけとする
- generated repo では root の `DESIGN.md` を通常更新対象として扱う
- `docs/design/README.md` は template-maintained な補助面であり、自動同期はしない
- template 側の design guidance を既存 generated repo に反映したい場合は、maintainer が手動で取り込む

## Design Contract Maintenance

- design 契約の正本は `docs/ai/repo-contract.md` とし、validator の正本は `scripts/ci/validate_template.py`、mutation test の正本は `tests/test_template_contract.py` とする
- `DESIGN.md` 契約に関する文言を変えるときは、`docs/ai/repo-contract.md`、`scripts/ci/validate_template.py`、`tests/test_template_contract.py` を同じ変更として扱う
- design 契約の文言だけを変える pull request でも、最低限 `make doctor` と `uv run pytest -q tests/test_template_contract.py` を実行する
- workflow や retained harness まで影響する変更では `make test` まで実行する
- `README.md` と `CONTRIBUTING.md` は mirror なので、canonical surface の意味を変えない案内整理だけなら validator の更新対象にはしない

## Generated Repo Checklist

テンプレートから repo を作成したら、最低限次を更新します。

1. `.github/CODEOWNERS`
2. `docs/architecture/overview.md`
3. `DESIGN.md`
   generated repo の visual contract の通常更新対象として、実プロジェクト向けに更新する
4. `docs/standards/*.md`
5. `.codex/config.toml`
   `approval_policy`、`sandbox_mode`、`network_access` を、自分たちの threat model、mount 範囲、秘密情報の配置、環境の破棄容易性に合わせて見直す
6. `.claude/settings.json`
7. `.mcp.json`
8. `docs/design/README.md`
   template-maintained な補助面なので、generated repo では通常更新しない。同期ポリシーの正本は `docs/ai/repo-contract.md` とする

## Compatibility Notes

- `.cursor/` と `GEMINI.md` は compatibility adapter であり、repo-wide rule の primary source ではありません。
- `docs/repository-template-design.md` は入力設計書として残しますが、運用中の正本ではありません。
