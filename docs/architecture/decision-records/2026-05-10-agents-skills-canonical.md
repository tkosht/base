# `.agents/skills` 正本化

## 背景

repo-local skill は Codex、Claude Code、互換用 Codex discovery の複数入口を持つ。従来は `.claude/skills/` に実体を置き、`.agents/skills/` を Codex 向け entrypoint として symlink にしていたため、repo-local agent 共通の正本が Claude Code 側に寄って見えていた。

## 判断

- repo-local skill の実体は `.agents/skills/<skill-name>/` に置く
- `.claude/skills/<skill-name>` と `.codex/skills/<skill-name>` は `.agents/skills/<skill-name>` へ向く互換 shim にする
- docs、validator、harness resource registry、sync helper は `.agents/skills` を mutable な skill source として扱う

## 理由

- `AGENTS.md` を repo-local instruction の正本にしている構造とそろう
- Codex と Claude Code の tool-specific entrypoint を、実体ではなく互換 layer として扱える
- skill の追加、更新、上流同期、harness 自己最適化で編集対象を 1 か所に固定できる

## 運用上の扱い

- 新しい skill は `.agents/skills/<skill-name>/SKILL.md` から作る
- Claude Code 向け discovery が必要な場合も `.claude/skills/<skill-name>` は symlink のまま保つ
- `.codex/skills/.system/` は local system skills の領域であり、repo-local skill 正本にはしない
