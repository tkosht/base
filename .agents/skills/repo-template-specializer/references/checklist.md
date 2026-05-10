# Repo Template Specializer Checklist

この checklist は、template/base から複製した repo を固有 repo にする時の漏れ検出に使う。項目は機械検索だけで終わらせず、active な導線か、歴史的記録か、意図的な retained harness かを分類する。

## Inputs

- User request、review artifact、open findings。
- README、package metadata、Makefile、CI、Issue/PR template、CODEOWNERS、security/contributing/design docs。
- `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、`.cursor/`、`.codex/config.toml`、`docs/ai/`。
- `docs/architecture/*`、harness manifest、resource registry、decision records。
- `.agents/skills/*`、`.claude/skills/*`、`.codex/skills/*`、`docs/ai/skills/*`。
- `bin/`、repo-local scripts、tests、fixtures、sample assets。

## Residue Probes

- Old repo or template identity: base repo name、template、starter、scaffold、overlay、generated repo、shared settings などの active wording。
- Deleted or template-only paths: starter helpers、template scripts、overlay scripts、sample templates、template smoke tests、old design samples。
- Hardcoded upstream ownership: `OWNER`、`REPO`、remote URL、GitHub API helper、workflow dispatch target。
- Stale retained harness names: old harness filenames、test names、registry IDs、Makefile targets、skill examples。
- Agent-facing stale references: skill prompts、source maps、compatibility adapters、settings comments、review examples。
- Review-loop gaps: command success onlyで終わり、material finding、out-of-scope finding、loop count、stop reason が記録されていない状態。

## Action Matrix

- Active identity surface: 現 repo の目的、利用者、検証、運用へ置換する。
- Template-only asset: 現 repo が template 配布をしないなら削除し、参照を全て更新する。
- Retained shared harness: 削除せず、用途名へ rename/reframe し、manifest、registry、tests、docs、skills を同期する。
- Historical record: 原則保持し、active residue scan の false stop reason にならないよう除外や文脈を明確にする。
- External provenance: 必要なら残すが、現 repo の instruction や command として読まれない場所に置く。

## Validation Hardening

- 人間または AI review で出た漏れごとに、validator または test のどちらで再発検知するかを決める。
- 削除済み path 参照、old helper 名、old repo name、hardcoded upstream repo、old harness 名は negative test を追加する。
- `.agents/skills/*/SKILL.md` と `docs/ai/skills/*` も active reference scan の対象に含める。
- Skill を追加・削除した時は `.agents/skills`、`.claude/skills`、`.codex/skills`、`docs/ai/skills`、retained harness manifest の同期を確認する。
- すべてを script 化しない。語義判断が必要な項目は checklist と review loop、再発性が高い項目は validator/test に分ける。

## Review Loop Acceptance

- 少なくとも 1 回は task-specific scan と code-review 観点の自己レビューを行う。
- material finding がある間は同じ scope 内で Repair -> Verify -> Review を繰り返す。
- target 外の material finding は `out_of_scope` として記録し、黙殺しない。
- `ReviewReport` 相当の loop count、converged、stop reason が説明できるまで PR 作成に進まない。
- 最終状態で active な docs/config/scripts/tests/skills が現 repo の identity と一致し、削除済み path 参照が残っていない。

## Final Checks

- `make doctor`
- `make lint`
- `make test`
- Focused structural checks for new or changed skills and symlinks。
- Review artifact がある場合は、全 finding が resolved、out-of-scope、または intentional false positive のどれかに分類されていること。
