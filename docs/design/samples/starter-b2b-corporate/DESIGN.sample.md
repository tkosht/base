# Starter B2B Corporate Sample

Status: Reference-only

Source note: This sample is a generic corporate starter created for this template. It is not extracted from a specific public site.

Reviewed date: 2026-04-19

Sync note: root `DESIGN.md` remains canonical. Update generated repos through root `DESIGN.md`, not by copying this sample verbatim.

## 1. Design System Overview

この sample は、日本語の企業間取引（B2B）向けコーポレートサイトとサービス紹介ページを想定した完成例です。B2B の比較検討で必要な信用情報、導入フロー、問い合わせ導線を 1 本のページで読ませる構成を示します。

ランディングページ（LP）は、hero、proof、offer、FAQ、footer CTA の順で進めます。LP の各 section は横幅をそろえ、1 画面ごとに判断材料を 1 つずつ増やす作りにします。

## 2. Brand Personality

- impression: `steady`, `competent`, `clear`
- copy tone: 誇張よりも実務の確かさ
- visual motif: rounded panel, soft border, muted accent

## 3. Typography

### 3.1 Primary Japanese Sans

- `font-family: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif`
- body `16px / 1.85`

### 3.2 Secondary Latin Sans

- `font-family: "Inter", "Helvetica Neue", Arial, sans-serif`
- metric、tag、短い操作 label に使う

### 3.3 Display Style

- hero title `44px / 1.15 / 700`
- section title `30px / 1.3 / 700`
- eyebrow `13px / 1.4 / 600 / 0.08em`

### 3.4 Body Style

- body `16px / 1.85 / 400`
- small `14px / 1.7 / 400`

### 3.5 Letter Spacing

- 和文本文 `0`
- 英字 label `0.08em`

### 3.6 Font Fallback

- 日本語 stack を先頭に固定し、欧文 fallback は system sans へ落とす

### 3.7 OpenType Features

- KPI は `tabular-nums`

### 3.8 Writing Direction

- 横書きのみ

## 4. Color System

- `--bg: #f6f5f1`
- `--surface: #ffffff`
- `--surface-strong: #eef0e7`
- `--text: #1f2322`
- `--text-muted: #616867`
- `--border: #d8ddd7`
- `--accent: #1f6a5c`
- `--accent-strong: #174f45`
- `--accent-soft: #dceee8`

## 5. Layout and Spacing

- page `max-width: 1180px`
- section padding `88px`
- card padding `24px`
- grid gap `24px`
- mobile section padding `60px`

## 6. Components

- primary button は主行動喚起（CTA）専用にし、塗りつぶし accent を使う
- secondary button は CTA の優先度を落としたい場所だけに置く
- proof card は数値、ラベル、短い説明の 3 段
- pricing teaser は border box で独立させる

CTA は hero、middle proof、footer の 3 箇所に置きます。CTA の文言は「相談する」「導入事例を見る」「資料を受け取る」のように、次の行動が分かる表現へ寄せます。

## 7. Content and Imagery

- LP の hero では product screenshot よりも、課題と解決の図解を優先する
- B2B の意思決定で効く導入体制、セキュリティ、サポート窓口を早めに見せる
- testimonial は肩書きと業種を必ず添える

## 8. Interaction and Motion

- hover `160ms ease`
- panel reveal `220ms ease-out`
- parallax や長い loading animation は使わない

## 9. Implementation Notes

- root の `DESIGN.md` を優先し、この sample は reference-only として扱う
- LP と CTA の配置は sample のまま固定せず、実ブランドの情報量に合わせて再構成する
