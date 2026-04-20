# DESIGN.md

## 1. Design System Overview

この starter は、日本語の企業間取引（B2B）向け AI サービスを前提にした visual contract です。B2B の検討者が数分で価値、信頼性、導入導線を把握できることを最優先にします。

ユーザーインターフェース（UI）は、装飾の多さよりも読みやすい階層と操作の明快さを優先します。UI の密度は高すぎず、hero、比較表、導入手順、実績、FAQ の順に理解が進む構成を基本にします。

## 2. Brand Personality

- 印象は `calm`, `credible`, `precise`, `modern`
- 語り口は断定しすぎず、技術的な信頼感を出す
- ビジュアルは華美に寄せず、整列、余白、情報の順序で強さを出す
- 主行動喚起（CTA）は「相談する」「資料を受け取る」など、業務文脈で自然な表現にする

## 3. Typography

### 3.1 Primary Japanese Sans

- `font-family: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif`
- 本文の標準サイズは `16px`
- 本文の標準 `line-height` は `1.8`

### 3.2 Secondary Latin Sans

- `font-family: "Inter", "Helvetica Neue", Arial, sans-serif`
- 数値、タグ、短い英単語、UI label で使う

### 3.3 Display Style

- hero 見出しは `40px`、`line-height: 1.2`、`font-weight: 700`
- section 見出しは `28px`、`line-height: 1.35`、`font-weight: 700`
- card 見出しは `20px`、`line-height: 1.4`、`font-weight: 600`

### 3.4 Body Style

- 本文は `16px`、`line-height: 1.8`、`font-weight: 400`
- 補足文は `14px`、`line-height: 1.7`
- 長文では `max-width: 42rem` を超えない

### 3.5 Letter Spacing

- 和文本文は `letter-spacing: 0`
- 欧文の大文字 label は `0.04em`
- 見出しは詰めすぎず、負の `letter-spacing` は使わない

### 3.6 Font Fallback

- 日本語優先の stack を先に置き、未知の環境でも字幅が崩れにくい順で並べる
- 欧文 fallback は `Inter` から system sans へ落とす

### 3.7 OpenType Features

- 本文では追加 feature を前提にしない
- 数字が並ぶ KPI は `font-variant-numeric: tabular-nums`

### 3.8 Writing Direction

- v1 は横書きのみ
- 縦書きや mixed writing mode は sample にも入れない

## 4. Color System

- `--color-bg: #f4f7f6`
- `--color-surface: #ffffff`
- `--color-surface-muted: #ebf1ef`
- `--color-text: #162321`
- `--color-text-muted: #526563`
- `--color-border: #cfdad6`
- `--color-accent: #0f766e`
- `--color-accent-strong: #115e59`
- `--color-accent-soft: #d9f0eb`
- `--color-danger: #b93838`

背景はわずかに緑みを含む neutral にし、寒すぎる青白さを避けます。CTA は `--color-accent` を基調にし、CTA hover では `--color-accent-strong` へ暗くします。

## 5. Layout and Spacing

- ページ全体の `max-width` は `1200px`
- 本文 column は `720px`
- section の縦余白は `96px`
- card の内側余白は `24px`
- grid gap は `24px`
- mobile では section 縦余白を `64px` に落とす

hero は左にテキスト、右にプロダクト図または図解を置く 2 column を基本にします。B2B の比較検討で必要な情報を 1 画面目から落としすぎないようにし、scroll 前から要点を 3 つ以上見せます。

## 6. Components

- primary CTA button: 高さ `48px`、左右 padding `20px`、角丸 `999px`
- secondary CTA button: surface 背景、`1px` border、text は accent color
- info card: border あり、shadow は `0 12px 30px rgba(17, 41, 38, 0.08)`
- metric block: 数値 `36px`、label `13px`
- quote block: 左 border `4px solid #0f766e`
- table: header 背景を `#ebf1ef`、row border を `#cfdad6`

CTA は hero、比較表の直後、ページ末尾の 3 箇所を基本配置にします。UI の主要操作は button、link、form field の見分けが一目でつくようにし、見た目だけで機能差を曖昧にしません。

## 7. Content and Imagery

- 画像は抽象的な 3D より、図解、画面断片、導入フローを優先する
- 見出しは利益訴求と信頼訴求を混ぜすぎない
- B2B の検討者が知りたい導入条件、セキュリティ、運用体制を隠さない
- 箇条書きは 3 から 5 項目に絞る

## 8. Interaction and Motion

- hover transition は `160ms ease`
- section reveal は `240ms ease-out` 以内
- scroll-linked animation は使わない
- motion は理解補助に限り、UI の意味を motion 依存にしない

## 9. Implementation Notes

- root の `DESIGN.md` だけを canonical な visual contract として扱う
- sample は `docs/design/samples/**/DESIGN.sample.md` を使い、repo 内で canonical 名の `DESIGN.md` を増やさない
- brand 未確定の generated repo は、この starter を初期値として採用し、早い段階で実ブランド向けに更新する
