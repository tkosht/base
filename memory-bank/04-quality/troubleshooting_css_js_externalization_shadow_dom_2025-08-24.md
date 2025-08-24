# CSS/JS 外出しトラブルシューティング（Gradio/Shadow DOM 対応）

## 概要
- 対象: `app/app_factory.py`（Gradio Blocks の head 組み立て）、`public/styles/app.css`、`public/scripts/threads_ui.js`
- 目的: Python内のインライン CSS/JS を外部ファイルに移行しつつ、UI 挙動と見た目を完全維持
- 結果: 段階移行で全体のスタイルを外部化。最終的に head は `<link rel="stylesheet" href="/public/styles/app.css" />` のみで安定動作

## 発生した問題と原因分析

### 1) 境界線 `.v-sep` が消える
- 症状: サイドバーとチャットの間の縦線が表示されない
- 原因1（セレクタ不一致）: DOM は `#vsep`（ラッパ）内に `.v-sep`（中身）だが、`#vsep.v-sep` と同一要素指定にしていた
  - 修正: `#vsep .v-sep`（子孫セレクタ）へ変更
- 原因2（読み込み到達範囲）: Gradio のレンダリング状況により、head の `<link>` だけでは望む順序/特異性で作用しないケースがあった
  - 一時対策: head に `<style id="app_css_import">@import url('/public/styles/app.css');</style>` を追加し、後勝ち/確実適用を担保
  - 最終判断: セレクタ/スコープ確定後は `<link>` のみでも安定したため `@import` は削除

### 2) 「意味不明な Textbox/Run」増殖
- 症状: 非表示であるべき Gradio の隠しトリガが表示され、TextBox/Run が多数出現
- 原因: `.hidden-trigger` の非表示スタイルが一覧コンテナ内にスコープされ、他領域で効かなくなった
- 対応: `.hidden-trigger { display:none !important; visibility:hidden !important; width:0; height:0; }` をグローバルに定義

### 3) 「…」(ctx-dots) 表示はあるが、クリックでメニューが見えない
- 症状: クリックしてもメニューが表示されない一方、`document.querySelector('.ctx-menu')?.style.display` は `block`
- 原因: `.ctx-menu` は `document.body` 直下に生成されるため、`#threads_list` スコープの CSS が当たらない
- 対応: `.ctx-menu`, `.ctx-item` をグローバル定義（スコープを外す）。`.ctx-dots` に `cursor:pointer` を付与

### 4) スレッドタブだけボタン配置が崩れる
- 症状: タブ側でボタンがタイトル下に落ちる
- 原因: `#threads_list` にのみフレックス系スタイルが適用され、`#threads_list_tab` へ適用漏れ
- 対応: `#threads_list` と `#threads_list_tab` に同一スタイルを適用（複合セレクタで横展開）

## ブラウザConsole での構造的確認手順（再発防止）

1. ShadowRoot 有無と要素所在
```js
const ga = document.querySelector('gradio-app');
!!ga && !!ga.shadowRoot; // false なら Light DOM 側
const inShadow = ga?.shadowRoot?.querySelector('#vsep');
const inDoc = document.querySelector('#vsep');
console.log({ inShadow: !!inShadow, inDoc: !!inDoc });
```

2. スタイル適用状態
```js
const sep = document.querySelector('#vsep .v-sep');
getComputedStyle(sep).backgroundColor; // rgb(156, 163, 175)
getComputedStyle(sep).height; // calc(100vh - 180px) 相当
```

3. 外部 CSS 読み込み確認
```js
[...document.styleSheets].some(s => (s.href||'').includes('/public/styles/app.css'));
```

## 安全な段階移行パターン

- 小さな塊から移す（装飾→ボタン→レイアウト→コンテキストメニュー）
- セレクタは実 DOM 通りに（例: `#vsep .v-sep`, `#threads_list .thread-link`）
- 兄弟画面/タブがあれば同時適用（`#threads_list`, `#threads_list_tab`）
- グローバル生成ノード（`.ctx-menu`）はグローバルで定義
- 隠しコンポーネントは必ずグローバルで非表示（`.hidden-trigger`）
- 必要最小限の `!important`。まずは記述順/特異性で解決
- どうしても適用順が勝てない場合は、一時的に head の `<style>@import</style>` で後勝ちにし、安定後に撤去

## 実装要点（今回の最終状態）

- head（`app/app_factory.py`）
  - `<link rel="stylesheet" href="/public/styles/app.css" />` のみ
  - `<style id="app_css_import">@import ...</style>` は除去（不要にできた）
- `public/styles/app.css`
  - `#vsep .v-sep`（子孫セレクタ）
  - `#threads_list` と `#threads_list_tab` の複合セレクタ群（タイトル/サマリ/行/ボタン/hover/selectedなど）
  - `.ctx-menu`/`.ctx-item` のグローバル定義
  - `.hidden-trigger` のグローバル非表示
  - サイドバー系（トグル/overflow/max-height 等）

## 検証ログ（抜粋）

```js
getComputedStyle(document.querySelector('#threads_list .thread-link')).padding
// '8px 10px'
getComputedStyle(document.querySelector('#threads_list .thread-link')).borderRadius
// '6px'
```

## 教訓 / ベストプラクティス

1. DOM スコープと生成位置（Shadow/Light、body直下生成）を意識して CSS スコープを設計
2. まずは子孫/ID複合セレクタで特異性を上げすぎずに整合
3. 画面崩れ時は Console で「存在確認→computedStyle→styleSheets読み込み」の順で切り分け
4. 移行は 1〜2 ルールずつ。問題が出たら即ロールバックして原因特定
5. 安定後に `<style>@import</style>` のような暫定措置は撤去し、シンプルな `<link>` に統一

## 参照
- 実装: `app/app_factory.py`, `public/styles/app.css`
- JS 初期化: `public/scripts/threads_ui.js`（ctx-menu/dots の動作に影響）


