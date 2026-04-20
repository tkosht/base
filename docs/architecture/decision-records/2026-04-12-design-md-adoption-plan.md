# Template への `DESIGN.md` 導入計画

## Status

Proposed

## Date

2026-04-12

## Context

このテンプレート repo は、`README.md`、`AGENTS.md`、`docs/ai/`、`docs/architecture/` を通じて運用契約と知識面を canonical に管理している。一方で、見た目の正本となる `DESIGN.md` は未導入で、generated repo が AI エージェントに対して visual contract をどこで持つべきかが未定義である。

`awesome-design-md-jp` の調査と、Google Stitch / `awesome-design-md` 系の公開運用を踏まえると、`DESIGN.md` は project root に置き、デザインルールを agent-friendly な Markdown として Git 管理する運用が最も自然である。

今回の目的は、このテンプレートから生成される repo で、`DESIGN.md` を適切に構成し、AI エージェントが迷わず利用できる状態を最小構成で整えることである。

## Request and Discussion Notes

今回の計画は、次の依頼と会話内容を前提にしている。

- base リポジトリとして、このテンプレートから作った generated repo で、`DESIGN.md` を適切に構成して利用できるようにしたい
- まず何をすべきかを整理したい
- 必要なら世の中のベストプラクティスも調査して整理したい
- review 用にこの計画を `.md` に記録したい
- 計画メモには、最終方針だけでなく依頼内容や議論内容も残したい

会話で確定した前提は次のとおり。

- generated repo には root の canonical `DESIGN.md` だけでなく、参考用 sample も同梱したい
- sample の中には、`https://www.agen-i.com/` の刷新時に利用できる `DESIGN.md` の叩き台を含めたい
  - この前提は会話時点の要望として記録する。public repo であることの確認後、最終判断では public template 同梱を取り下げ、private companion overlay へ分離する方針に改めた
- v1 の主対象は単一プロダクト repo とする
- root の starter はブランド非依存の汎用 template を採用する
- sample は Markdown だけでなく `preview.html` も持たせたい
- `AGen I.` 向け sample は完全な再ブランドではなく、現ブランド刷新の方向で作る
  - この方向性自体は維持するが、配布先は public template ではなく private companion overlay に変更した

このため、本メモの判断は「single-product 前提で root に 1 枚の正本を置きつつ、review しやすい curated sample を別置きで同梱する」という形に収束している。

ただし 2 回目 review 時点で、この base repo 自体は public GitHub repo（`https://github.com/tkosht/base`）であることを確認した。そのため、ブランド固有の `AGen I.` sample は public template の常設物としては置かず、private な companion overlay として分離する方針に補正する。

## Decision Summary

- generated repo の見た目の正本を root の `DESIGN.md` に固定する
- v1 は単一プロダクト repo を対象にし、root に 1 枚の canonical `DESIGN.md` を置く
- canonical 名としての `DESIGN.md` は root の 1 枚だけに固定し、sample 側には `DESIGN.md` を増やさない
- canonical 名としての `DESIGN.md` の一意性は repo 全体で守り、root 以外の場所に `DESIGN.md` を置かない
- public template には root の starter `DESIGN.md` に加えて、public-safe な reference sample だけを同梱する
- sample 側には同名の `DESIGN.md` を置かず、`DESIGN.sample.md` を採用して canonical surface と明確に分離する
- public template の sample は generic 1 系統に絞り、`AGen I.` sample は private companion overlay で配布する
- `DESIGN.md` の存在と参照は template contract、workflow trigger、base harness の正本に昇格させて検証する
- `DESIGN.md` は canonical surface として `PRIMARY_DOCS` 相当の用語契約にも含める
- `docs/design/README.md` は reference doc ではなく canonical な補助面として扱い、`PRIMARY_DOCS` に含めて既存の共通用語契約も掛ける
- `docs/design/README.md` は generated repo の通常更新対象ではなく template-maintained な補助面として扱い、generated repo では原則として root `DESIGN.md` のみを見直す
- `docs/design/README.md` の責務は「design guidance の canonical な補助面であり、sync policy の正本ではない」に固定する
- `template-maintained` / 非自動同期ポリシーの正本は `docs/ai/repo-contract.md` に固定する
- `template-maintained` は generated repo への自動同期を意味しない。template 側の更新が既存 generated repo に必要な場合は maintainer が手動取り込みする方針に固定し、`manual cherry-pick` はその代表例として扱う
- `DESIGN.md` の略語契約は既存の `TERM_EXPANSIONS` をそのまま流用するのではなく、design 文書向けの追加契約を別に定義して適用する
- design 専用略語契約は validator だけで導入せず、canonical な詳細は `docs/standards/communication.md` と `docs/design/README.md` に置いたうえで検査する
- `AGENTS.md` には design 文書でも略語だけで説明しないという参照レベルだけを残し、具体的な略語一覧や運用細則は `docs/` 側へ分離する
- design 専用略語契約は既存の「1 回しか出ない語は略さない」を置き換える例外ではなく、design 文書では初出展開を最低限要求する追加ルールとして扱う
- design 専用略語契約の自動検査対象は root `DESIGN.md` だけでなく、`docs/design/README.md` と public sample の `DESIGN.sample.md` まで含む design 系文書全体にそろえる
- root `DESIGN.md` と `docs/design/README.md` の同期責務は、「root `DESIGN.md` の書き方・読書順・review 観点の template 契約を変えるときだけ template 側で `docs/design/README.md` を更新し、generated repo では通常更新しない」で固定する
- `docs/design/README.md` への読書導線は `repo-contract` に書くだけでなく validator と test でも守る
- design 系作業では root `DESIGN.md` を先に読む契約は方針ではなく machine-check 対象として守る
- `Generated Repo Checklist` は `docs/ai/repo-contract.md` 内の canonical section として扱い、mirror には落とさない
- `Generated Repo Checklist` section 自体に、generated repo の通常更新対象として root `DESIGN.md` があることと、`docs/design/README.md` は通常更新対象ではないことを validator と test で守る
- `README.md` と `CONTRIBUTING.md` に展開する `template-maintained` / 非自動同期の説明は、`docs/ai/repo-contract.md` の mirror として手動確認項目に留める

## Quality Gates

このフェーズの review と実装判断は、次の品質軸で評価する。

- 正本分離: `root DESIGN.md`、`docs/design/README.md`、`docs/ai/repo-contract.md`、`Generated Repo Checklist` の役割が重ならず、正本 / 補助面 / mirror / reference-only が一意に読めること
- 更新責務: generated repo が通常更新する文書と template-maintained な文書が混ざらないこと
- 検査境界: `run_checks()` と `tests/test_template_contract.py` が守る契約と、manual review に残す契約が混ざらないこと
- 発見導線: AI エージェントと maintainer が design 系作業の初動で迷わないこと
- 実装可能性: `validate_template.py` と `tests/test_template_contract.py` の既存構造に無理なく落ちること
- reference sample 分離: sample が canonical surface を汚染せず、agent が root 正本を取り違えないこと

## Artifact Roles

- `DESIGN.md`: generated repo の visual contract 正本。区分は canonical。通常更新主体は generated repo。canonical 名は repo 内で root のみ。machine-check 対象。
- `docs/design/README.md`: design guidance の補助正本。区分は canonical supplement。通常更新主体は template。machine-check 対象。
- `docs/ai/repo-contract.md`: sync policy、読書順、checklist の正本。区分は canonical。通常更新主体は template。machine-check 対象。
- `Generated Repo Checklist`: generated repo 初期更新の canonical section。区分は canonical section。通常更新主体は template。machine-check 対象。
- `README.md`: 人間向け mirror 導線。区分は mirror。manual review 対象。
- `CONTRIBUTING.md`: 人間向け mirror 導線。区分は mirror。manual review 対象。
- `DESIGN.sample.md`: reference sample。区分は reference-only。repo 内で root 以外に canonical 名の `DESIGN.md` を作らない。machine-check 対象。
- `preview.html`: sample の curated static artifact。区分は reference-only。static check 対象。

## Planned Changes

### 1. Canonical Surface

- root に `DESIGN.md` を追加する
- `AGENTS.md` では `AGENTS.md = 作り方`、`DESIGN.md = 見た目とデザイン制約` の責務分担を明記する
- `AGENTS.md` には design 文書でも略語だけで説明しないという参照レベルだけを追記する
- `docs/standards/communication.md` に design で頻出する略語の説明義務と、既存の「1 回しか出ない語は略さない」との優先関係を追記する
- `docs/ai/repo-contract.md` を最初に更新し、`Reading Order`、`Repository Roles`、`Generated Repo Checklist` に `DESIGN.md` を追加する
- `docs/ai/repo-contract.md` に、UI / frontend / LP / marketing site の作業では root の `DESIGN.md` を先に読む契約を追加する
- `docs/ai/repo-contract.md` の `Reading Order` には、design 系作業時の追加読書先として `docs/design/README.md` を明示する
- `docs/ai/repo-contract.md` の `Repository Roles` には、`docs/design/README.md` が root `DESIGN.md` を支える canonical な補助面であることを明記する
- `docs/ai/repo-contract.md` の `Generated Repo Checklist` では、generated repo の通常更新対象として root `DESIGN.md` を追加し、`docs/design/README.md` は template-maintained なので通常は更新しないと明記する
- `Generated Repo Checklist` は `docs/ai/repo-contract.md` 内の canonical section として扱い、別文書へ責務を逃がさない
- `docs/ai/repo-contract.md` には、`template-maintained` は generated repo への自動同期を意味せず、必要時は maintainer が手動取り込みすること、`manual cherry-pick` はその代表例であることを明記する
- `docs/design/README.md` には、design guidance の canonical 補助面であり、sync policy の正本は `docs/ai/repo-contract.md` だと 1 文でだけ記す
- `README.md` と `CONTRIBUTING.md` には、`docs/ai/repo-contract.md` の mirror として同趣旨を展開する
- `README.md` と `CONTRIBUTING.md` には、`repo-contract` で定義した読書順と checklist を展開する形で `DESIGN.md` 更新を追加し、`docs/design/README.md` は template-maintained で通常更新しない方針にそろえる

### 2. Supporting Docs

- `docs/design/README.md` を追加し、次を定義する
  - `docs/design/README.md` 自体は reference-only ではなく、root `DESIGN.md` を支える canonical な補助面であること
  - `docs/design/README.md` の責務は「design guidance の canonical な補助面であり、sync policy の正本ではない」に固定すること
  - root `DESIGN.md` が canonical であること
  - `docs/design/samples/**/DESIGN.sample.md` は reference-only であること
  - root starter は generated repo が最初に満たすべき最小 visual contract、generic sample はそれを使った完成例 / 応用例であること
  - generated repo 作成後に最初に見直すべきポイント
  - sync policy と generated repo の更新責務の正本は `docs/ai/repo-contract.md` であり、本書では参照だけに留めること
  - `DESIGN.md` を更新する責務と review 観点
  - root `DESIGN.md` の書き方・読書順・review 観点の template 契約を変えるときだけ template 側で `docs/design/README.md` も更新すること
  - design 文書に対する略語ルールは `docs/standards/communication.md` を正本とし、ここでは `DESIGN.md` 向けの補足だけを持つこと
  - 略語ルールの適用対象が root `DESIGN.md`、`docs/design/README.md`、public sample の `DESIGN.sample.md` であること
  - public template に含める sample と private overlay で配る sample の境界
- `docs/architecture/overview.md` と `docs/architecture/knowledge-architecture.md` に `DESIGN.md` / `docs/design/` の置き場を追記する

### 3. Starter and Samples

- root `DESIGN.md` は Stitch 互換の 9 セクション構成で starter を同梱する
- starter はブランド非依存の B2B / AI 企業向けとし、hex、font stack、line-height、spacing、component token を明示する
- root starter の責務は「generated repo が最初に満たすべき最小 visual contract」に限定し、構成は短く、すぐ書き換えやすいものにする
- `docs/design/samples/starter-b2b-corporate/` に汎用 sample を置く
- public template に同梱する sample は上記 1 件だけにする
- generic sample の責務は「starter を実案件寄りに展開した完成例 / 応用例」を示すことに限定し、starter の焼き直しにしない
- `AGen I.` 現ブランド刷新向け sample は、この public repo には置かず、private companion overlay に同じファイル形（`DESIGN.sample.md` と `preview.html`）で保持する
- ここでいう `private companion overlay` は、この repo の `templates/manifest.yaml` と `scripts/template/apply_overlay.py` が扱う public overlay catalog には載せない別配布物を指す
- public template 側の sample は `DESIGN.sample.md` と `preview.html` を 1 セットで持つ
- `preview.html` には `reference-only` の明示、source note、reviewed date、同期ルールの注記を必須で入れる
- sample を root に昇格するときは、sample の `DESIGN.sample.md` をそのまま読ませず、root `DESIGN.md` に転記して canonical 化する

### 4. Validation

- `scripts/ci/validate_template.py` の `REQUIRED_PATHS` には glob を入れず、`DESIGN.md`、`docs/design/README.md`、`docs/design/samples/starter-b2b-corporate/`、`docs/design/samples/starter-b2b-corporate/DESIGN.sample.md`、`docs/design/samples/starter-b2b-corporate/preview.html` を具体パスで追加する
- `scripts/ci/validate_template.py` の `PRIMARY_DOCS` に root `DESIGN.md` と `docs/design/README.md` を追加する
- `scripts/ci/validate_template.py` の `run_checks()` では、repo 内の root 以外すべての `DESIGN.md` を禁止し、探索スコープを sample 配下に限定しない
- `scripts/ci/validate_template.py` の `run_checks()` では、少なくとも `docs/design/samples/**/DESIGN.md` のような root 以外の `DESIGN.md` が存在したら fail する
- `scripts/ci/validate_template.py` の `run_checks()` では、`docs/ai/repo-contract.md` の `Reading Order` または design 系作業時の追加読書順に `docs/design/README.md` があり、`Repository Roles` で canonical な補助面として説明されていることを検査する
- `scripts/ci/validate_template.py` の `run_checks()` では、`docs/ai/repo-contract.md` にある「design 系作業では root の `DESIGN.md` を先に読む」契約自体も検査し、この文言が消えた場合は fail する
- `scripts/ci/validate_template.py` の `run_checks()` では、`docs/ai/repo-contract.md` を `template-maintained` / 非自動同期ポリシーの唯一の正本として扱い、自動同期しないことと手動取り込み方針が残っていることを検査する
- `scripts/ci/validate_template.py` の `run_checks()` では、`docs/ai/repo-contract.md` の `Generated Repo Checklist` section 自体に root `DESIGN.md` の更新対象追加があり、`docs/design/README.md` は通常更新対象ではないことが残っていることを検査する
- `scripts/ci/validate_template.py` の `run_checks()` では、`docs/design/README.md` が design guidance の canonical 補助面であり、sync policy の正本は `docs/ai/repo-contract.md` だと読める最小責務記述を保っていることを検査する
- `scripts/ci/validate_template.py` の自動検査範囲は canonical surface に限定し、`README.md` と `CONTRIBUTING.md` に展開した mirror 文言までは機械検査しない
- `scripts/ci/validate_template.py` の自動検査範囲から外す mirror 文言には `Generated Repo Checklist` を含めない
- design 系文書向けには design 専用の略語契約を追加し、少なくとも `B2B`、`LP`、`CTA`、`UI` を正式名または平易な日本語と併記するルールを自動検査する
- 実装は、既存の `TERM_EXPANSIONS` を無差別に広げるのではなく、design 文書集合にだけ追加適用する `DESIGN_TERM_EXPANSIONS` 相当の定義と、別責務の専用 checker を追加する方針にする
- design 専用略語チェックの適用対象は root `DESIGN.md`、`docs/design/README.md`、public sample の `DESIGN.sample.md` とし、validator と canonical docs の対象範囲を一致させる
- design 専用略語契約の優先関係は、既存の「1 回しか出ない語は略さない」を維持したうえで、design 文書では初出展開を最低限要求する追加ルールとする
- したがって、たとえば `ユーザーインターフェース（UI）` を 1 回だけ書いたケースは pass ではなく、原則として略さない形へ書き換える対象にする
- 合否例は次で固定する
  - fail: `UI` を説明なしで使う
  - fail: `ユーザーインターフェース（UI）` を 1 回だけ書いて以後使わない
  - pass: `ユーザーインターフェース（UI）` を初出で書き、その後に `UI` を再度使う
  - pass: 略さずに `ユーザーインターフェース` だけを書く
- 入口文書が `DESIGN.md` に言及していることを template contract で検査する
- `.github/workflows/template-health.yml`、`.github/workflows/ci.yml`、`.github/workflows/test-all-subsystems.yml` の trigger と path filter では root `DESIGN.md` を明示的に拾う
- `docs/design/**` については literal な文字列追加を必須にせず、次のいずれかを満たせば許容する契約にする
  - event の path filter に `docs/design/**` がある
  - event の path filter に `docs/**` がある
  - event の path filter に `**` がある
  - 対象 event に path filter 自体がなく、workflow 全体が常時起動される
- `scripts/ci/validate_template.py` に workflow contract 用の専用チェックを追加し、上記 3 workflow が root `DESIGN.md` を明示的に拾い、かつ `docs/design/**` について上記許容パターンのいずれかを満たすことを自動検査する
- `docs/architecture/base-harness-set.toml` と `docs/architecture/base-harness-set.md` に `DESIGN.md` と `docs/design/` を反映し、base harness の正本にも昇格させる
- `tests/test_template_contract.py` に `DESIGN.md` 関連の検査ケースを追加し、required path 欠落と workflow path filter 欠落の両方で `run_checks()` が失敗することを確認する
- `tests/test_template_contract.py` には、root 以外の場所へ `DESIGN.md` を追加すると `run_checks()` が失敗する mutation test を追加し、sample 配下はその代表例として扱う
- `tests/test_template_contract.py` には、design 専用 checker による `B2B`、`LP`、`CTA`、`UI` の pass / fail 例と、`docs/design/README.md` が `PRIMARY_DOCS` として既存の共通用語契約にも入ることを確認するケースを追加する
- `tests/test_template_contract.py` には、`repo-contract` から `docs/design/README.md` への読書導線または `Repository Roles` の canonical 補助面記述を削ると `run_checks()` が失敗するケースも追加する
- `tests/test_template_contract.py` には、`repo-contract` から「design 系作業では root の `DESIGN.md` を先に読む」文言を削ると `run_checks()` が失敗する mutation test も追加する
- `tests/test_template_contract.py` には、`docs/ai/repo-contract.md` から `template-maintained` / 非自動同期ポリシーを削ると `run_checks()` が失敗する mutation test も追加する
- `tests/test_template_contract.py` には、`docs/ai/repo-contract.md` の `Generated Repo Checklist` section から root `DESIGN.md` 更新対象または `docs/design/README.md` 非更新方針を削ると `run_checks()` が失敗する mutation test も追加する
- `tests/test_template_contract.py` には、`docs/design/README.md` から「design guidance の canonical 補助面であり、sync policy の正本ではない」という責務記述または `docs/ai/repo-contract.md` 参照を削ると `run_checks()` が失敗する mutation test も追加する

## Sample Direction

### Generic Starter

- 業種は日本語 B2B / AI consulting 寄り
- ブランド固有名詞は使わない
- generated repo が即日で仮の visual contract を持てることを優先する
- 目的は最小契約であり、完成例ではない

### `AGen I.` Refresh Sample

- 現ブランドの会社名、主要メッセージ、AI Agent / Consulting の訴求は維持する
- 情報設計、余白、タイポグラフィ、CTA、カード、レイアウト密度をモダン化する
- 完全なブランド再定義ではなく、「現ブランド刷新」の叩き台として使えることを優先する
- 配布スコープは internal / private companion overlay に限定し、この public template repo の常設 sample には含めない

## Test Plan

- `make doctor` で `DESIGN.md` と `docs/design/**` を含む template contract が通る
- `make test` で `tests/test_template_contract.py` の `DESIGN.md` 関連追加ケースが通る
- public template に含める sample について、`DESIGN.sample.md` と `preview.html` が対で存在すること、preview に `reference-only`、source note、reviewed date、同期ルール注記があることを静的に確認する
- `ci.yml`、`test-all-subsystems.yml`、`template-health.yml` が root `DESIGN.md` を明示的に拾い、`docs/design/**` を `docs/**` または同等条件で拾うことを確認する
- `run_checks()` が 3 workflow の path filter を実効カバレッジ基準で自動検査し、root `DESIGN.md` の欠落または `docs/design/**` カバレッジ欠落時に失敗することを確認する
- `run_checks()` が repo 内の root 以外すべての `DESIGN.md` を禁止し、sample 配下を含む任意の root 以外の場所に `DESIGN.md` が混入した場合に失敗することを確認する
- `run_checks()` が `repo-contract` 上の `docs/design/README.md` 導線も検査し、`Reading Order` または `Repository Roles` から当該導線が消えた場合に失敗することを確認する
- `run_checks()` が `repo-contract` 上の「design 系作業では root の `DESIGN.md` を先に読む」契約も検査し、この read-first 文言が消えた場合に失敗することを確認する
- `run_checks()` が `docs/ai/repo-contract.md` を `template-maintained` / 非自動同期ポリシーの正本として検査し、自動同期しないことまたは手動取り込み方針が消えた場合に失敗することを確認する
- `run_checks()` が `docs/ai/repo-contract.md` の `Generated Repo Checklist` section 自体を検査し、root `DESIGN.md` の更新対象追加または `docs/design/README.md` 非更新方針が消えた場合に失敗することを確認する
- `run_checks()` が `docs/design/README.md` の最小責務記述も検査し、この文書が design guidance の canonical 補助面であり、sync policy の正本ではないこと、正本参照先が `docs/ai/repo-contract.md` であることが消えた場合に失敗することを確認する
- `DESIGN.md` の design 専用略語契約が動作し、`B2B`、`LP`、`CTA`、`UI` を説明なしで使った場合に失敗することを確認する
- design 系文書全体に同じ略語チェックが掛かり、root `DESIGN.md` だけでなく `docs/design/README.md` と public sample の `DESIGN.sample.md` でも drift を検知できることを確認する
- `docs/design/README.md` が `PRIMARY_DOCS` の一部として既存の共通用語契約にも入り、`ADR`、`TDD`、`CI`、`MCP`、`CLI`、`OAuth` の既存ルールから外れていないことを確認する
- `tests/test_template_contract.py` に、`repo-contract` から `docs/design/README.md` への導線を削る mutation test があり、fail することを確認する
- `tests/test_template_contract.py` に、root 以外の場所へ `DESIGN.md` を追加した mutation と、`repo-contract` から root `DESIGN.md` read-first 文言を削る mutation があり、どちらも fail することを確認する
- design 専用略語契約が `docs/standards/communication.md` と `docs/design/README.md` に反映され、validator の hidden policy になっていないことを確認する
- `AGENTS.md` が詳細一覧を抱えず、参照レベルの記述に留まっていることを確認する
- 「1 回しか出ない語は略さない」と design 初出展開ルールの優先関係どおりに validator が動作することを確認する
- 略語ルールの代表例として、単発使用は fail、複数回利用で初出展開ありは pass、略さない記述は pass、の 3 系統を test に含める
- `docs/architecture/base-harness-set.toml` と `docs/architecture/base-harness-set.md` に `DESIGN.md` / `docs/design/` が反映されていることを確認する
- 手動確認として、`README.md` と `CONTRIBUTING.md` が `docs/ai/repo-contract.md` の mirror として、`template-maintained` は非自動同期であり、必要時は手動取り込みする方針を一貫して説明していることを確認する
- 手動確認として、`manual cherry-pick` が唯一方式としては書かれず、手動取り込みの例として一貫して扱われていることを確認する

## Assumptions

- v1 の対象は single-product repo である
- root `DESIGN.md` だけが agent に読ませる正本であり、sample は root に昇格するまでは正本ではない
- sample 側の名前は `DESIGN.sample.md` に固定し、repo 内に複数の `DESIGN.md` を置かない
- preview は curated static artifact とし、`DESIGN.md` からの自動生成は v1 の対象外とする
- `AGen I.` sample は公開サイトをベースにした刷新叩き台であり、完全なブランドガイドラインを前提にしない
- この public repo にはブランド固有 sample を常設せず、`AGen I.` sample は private companion overlay で管理する

## Review Focus

- root `DESIGN.md` を canonical にする方針で十分か
- `docs/design/` を新設しても knowledge surface が過剰に増えないか
- sample 2 系統の切り分けが適切か
- v1 で preview を static artifact に留める判断が妥当か
- template contract に含める検査範囲が適切か
