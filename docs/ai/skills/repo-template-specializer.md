# repo-template-specializer

- Purpose: template/base 複製 repo を、現 repo 固有の identity、検証契約、AI 運用面へスリム化・特化する
- Use when: README/docs/settings/agent instructions などに template/base 由来の記述や導線が残っている repo を整理する
- Codex entrypoint: `.agents/skills/repo-template-specializer`
- Claude entrypoint: `.claude/skills/repo-template-specializer`
- Key outputs: residue inventory、removal/retention decision、validator/test hardening、ReviewReport 相当の収束確認
