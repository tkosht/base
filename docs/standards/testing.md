# Testing Standard

- 新機能では、可能なら failing test または acceptance test を先に置く
- 狭い編集では、最も近い単体検証と補助確認を組み合わせる
- template control-plane の変更では、構造検証と smoke test をセットで更新する
- overlay 追加時は、適用 smoke と主要ファイル検証を用意する
