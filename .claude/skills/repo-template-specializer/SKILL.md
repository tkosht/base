---
name: repo-template-specializer
description: "Use when a repository copied from a template or base repository must be slimmed down and specialized for its own project, including README/docs/settings/agent instructions, retained harness selection, validation hardening, and review-loop closure."
---

# Repo Template Specializer

## Purpose

Template/base 複製 repo を、配布元ではなく現 repo の固有目的・検証契約・AI 運用面へ収束させる。テンプレート配布用の導線を削り、残す shared harness は現 repo の目的で再定義する。

## Workflow

1. Sense: `references/checklist.md` を読み、README、docs、metadata、CI、settings、agent instructions、skills、scripts、tests、review artifact から template/base 残骸を拾う。明示された review artifact がある場合は、先に finding を構造化する。
2. Inventory: 見つけた項目を identity surface、template-only asset、retained shared harness、validation/review surface に分ける。歴史的記録、外部由来、意図的な除外 path は false positive 候補として分離する。
3. Specialize: active な説明・設定・AI 向け instruction を現 repo の目的、所有者、検証コマンド、運用ルールへ置き換える。instruction surface が大きい場合は `repo-instruction-optimizer` を併用する。
4. Remove: 現 repo が template 配布をしない場合だけ、starter、overlay、sample、template smoke test などの配布側資産を削除する。削除前後で active reference を必ず更新する。
5. Retain and harden: 残す harness は配布元名ではなく用途名へ再定義し、manifest、registry、Makefile、tests、skills、docs を同期する。人間または AI review で見つかった漏れは validator/test に落とす。
6. Review loop: task-specific scan と `harness-autoptimizer` の review loop を回し、loop count、material finding、out-of-scope finding、converged、stop reason を `ReviewReport` 相当で確認する。
7. Verify and hand off: `make doctor`、`make lint`、`make test` と focused checks を通す。PR 作成は収束後に `git-commit-pr` へ委譲する。

## References

- `references/checklist.md`

## Guardrails

- Template 由来でも現 repo が使う資産は削除せず、retained harness として再定義する。
- 歴史的な decision record や review 記録は active instruction と混同しない。
- 汎用 Skill なので、特定 repo 固有の名称は例示に留め、手順の前提にしない。
- v1 では新規 helper script を増やさない。繰り返し発生する機械検出だけを後続で script 化する。
