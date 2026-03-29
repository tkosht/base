# テスト標準

- 新機能では、可能なら失敗テストまたは受け入れテストを先に置く
- 狭い編集では、最も近い単体検証と補助確認を組み合わせる
- template control-plane の変更では、構造検証と smoke test をセットで更新する
- overlay 追加時は、適用 smoke と主要ファイル検証を用意する
- `make test` は通常テストの正面入口とし、ChatGPT ログインが必要な Codex live test を含めない
- `make test-codex-live` は ChatGPT にログイン済みのローカル端末でのみ実行する
- `codex exec` を実際に呼ぶテストは `codex_live` marker を付け、標準の継続的インテグレーション（CI）から外す
- live test の再試行回数が必要な場合だけ `CODEX_INTEGRATION_MAX_ATTEMPTS` を使う
- テスト駆動開発（TDD）を外した変更では、理由と代替検証を報告する
