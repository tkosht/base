# UI Selection State Pattern (Gradio + FastAPI)

## 問題
- Gradio Blocks 上でスレッド一覧を再描画すると、選択状態が失われたり、クライアント側の保持値に上書きされる。
- サイドバー開閉やDOM差し替えのタイミングで、意図しないスレッドが選択済みに戻ることがある。

## 解決策（パターン）
1) サーバ側HTMLに選択状態を埋め込む
- スレッド一覧コンテナに `data-selected` を付与
- 選択中項目に `selected` クラスを事前付与

2) クライアント側の復元優先順位
- MutationObserverで差し替え検知
- `data-selected` を最優先で `markSelectedLists()` に適用
- フォールバックで `.thread-link.selected` → `window.__selectedTid`

3) 選択ID伝播
- Gradio の `State`（`current_thread_id`）を `demo.load`/`.change()` の inputs に渡す
- 一覧HTML生成で `selected_tid` を受けて `data-selected`/`selected` を反映

## 実装断片
```python
# app/app_factory.py
html = _build_threads_html(items, selected_tid)
return gr.update(value=html), items
```

```js
// public/scripts/threads_ui.js
const installListObserver = (rootSel) => {
  const el = qs(rootSel);
  const obs = new MutationObserver(() => {
    setTimeout(() => {
      const container = qsWithin(el, '.threads-list');
      const sel = (container?.getAttribute('data-selected') || '').trim();
      markSelectedLists(sel || (window.__selectedTid || '').trim());
    }, 30);
  });
  obs.observe(el, { childList: true, subtree: true });
};
```

## 検証ポイント
- サイドバー閉で新規→初回発話/自動タイトル確定→開: 新規が選択
- 既存選択中に新規→後で新規に選択移動
- リネームで選択維持

## 適用範囲
- Gradio 固有のShadow DOM配下でも動作
- 他のUIフレームワークでも `data-selected` 優先の復元思想は再利用可能

