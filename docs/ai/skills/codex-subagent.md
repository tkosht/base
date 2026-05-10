# codex-subagent

- Purpose: Codex 実行のカプセル化、結果保存、比較実行
- Use when: 単発・並列・競争実行、checkpoint 付き pipeline、DAG stage 実験、結果照会
- Notes: graph writer stage は `write_roots` を明示し、parallel branch は isolated workspace で扱う
- Notes: pipeline mode の `workdir` は repo 内限定で、evaluation の retry policy は stage logs から導出する
- Notes: `team_policy: "manager_leaf_v1"` では DAG と `node_kind` が必須。manager node は read-only / no-write / non-executor、実作業は leaf node に限定する
- Skill source: `.agents/skills/codex-subagent`
- Claude shim: `.claude/skills/codex-subagent`
- Key outputs: 実行ログ、pipeline results、checkpoint state、feedback records
