# Gradio + FastAPI Threads UI 知見集約（トラブルシューティング/設計ルール）

## 目的
本書は、Gradio UI（Shadow DOM）と FastAPI／SQLAlchemy によるスレッド機能実装で遭遇した課題と、その解決パターンを整理したもの。今後の変更時の指針・チェックリストの根拠とする。

---

## 設計ルール（要点）

- Shadow DOM 対応
  - 直接 `document.querySelector` に依存しない。`gradio-app.shadowRoot` 起点で走査する deep query ユーティリティ（qsDeep/qsWithin）を用意する。
  - クリック検知は document で委譲し、`event.composedPath()` から `.thread-link` を特定する。

- State 書き換えと change 発火（Gradio）
  - 値設定順は「kind を一時クリア → id/arg → kind=操作名」。2回目以降のクリックでも確実に change を発火させるための必須手順。
  - 連続操作時は `setTimeout(..., 0)` などで最小遅延を挟み、描画タイミングずれを吸収する。

- タブ遷移（Threads → Chat）
  - role=tab="チャット" を検索し、未選択なら `click()`。最大 3 回の軽量リトライで十分。過剰なループは作らない。

- 一覧の即時反映（サイドバー/タブ）
  - サーバで生成した同一 HTML をサイドバー／タブの両方に反映する設計を基本とする。
  - 右クリックのリネーム/削除は「サーバ更新」＋「イベントチェーンでタブ側も再描画」を1経路に統一。DOM 直書きは補助に留める。

- 右クリックメニュー UX
  - メニュー外クリック/ESC で閉じる。削除は confirm を挟む。リネームは現タイトルを初期値に提示。

- チャット履歴の保存
  - `guard_and_prep` でユーザ投稿、`stream_llm` 完了時にアシスタント発話を DB 保存。`current_thread_id` を確実に渡す。
  - メッセージ ID 生成関数をサービス内に集約（例: `_simple_ulid()`）。漏れがあると保存されない。

- DB/Repository 方針
  - 論理削除は UI 側フィルタではなく SELECT 側（`archived=False`）で排除し、UIの複雑化を避ける。

---

## 代表的な不具合と対策

1) 「2回目以降のクリックで反応しない」
- 原因: hidden の State に同じ値が連続で入り change が発火しない。
- 対策: kind を一旦空にしてから id/arg → kind=操作名 の順で設定。

2) 「タブ遷移しない／不安定」
- 原因: Shadow DOM 配下の role=tab 取得や選択状態の確認が不確実。
- 対策: role=tab だけを対象に検索→未選択なら click→再確認（最大 3 回）。

3) 「スレッドタブに即時反映されない」
- 原因: サイドバー側のみ再描画していた／イベントチェーン未接続。
- 対策: `action_kind.change(...).then(_refresh_threads_tab, ...)` を追加し、常に双方再描画。

4) 「チャットが保存されない」
- 原因: メッセージ ID 生成関数未定義（`_simple_ulid`）。
- 対策: サービス層で ID 生成関数を提供し、ユーザ/アシスタント双方で利用。

---

## デバッグ手順（Console 用スニペット）

- hidden 値の監視
```js
(() => {
  const sel = c => (window.qsDeep?.(c) || document.querySelector(c))?.querySelector('textarea, input');
  const k = sel('.th_action_kind'), i = sel('.th_action_id');
  ['input','change'].forEach(ev => {
    k?.addEventListener(ev, e => console.log(`[dbg] kind=${e.target.value}`));
    i?.addEventListener(ev, e => console.log(`[dbg] id=${e.target.value}`));
  });
})();
```

- タブ選択状態の確認
```js
(() => {
  const tabs = (window.qsaDeep?.('[role="tab"]') || Array.from(document.querySelectorAll('[role="tab"]')));
  tabs.forEach((t, i) => console.log(i, (t.textContent||'').trim(), t.getAttribute('aria-selected')));
})();
```

- スレッドタブの HTML 先頭断片（Shadow DOM）
```js
document.querySelector('gradio-app')?.shadowRoot?.getElementById('threads_list_tab')?.innerHTML.slice(0,200)
```

- メッセージ保存の確認
```bash
curl -s http://localhost:7860/api/threads/<TID>/messages | jq .
```

---

## 運用指針（最小で安全な変更）

- 1経路主義: 値設定→イベントチェーン→サーバ出力を両 UI に反映、の一本化。DOM 直書きは補助に限定。
- リトライ最小: タブ遷移のリトライは 3 回程度。増やしても価値が薄く複雑になる。
- UI の即時性は「then での再描画」で担保。個別の要素書き換えは最小限。

---

## 実装抜粋コード（最小セット）

> ここでは、今回の安定動作に至った実装の「要点のみ」をコード例として記録します。

### 1) JS: Shadow DOM対応のクリック検知とタブ遷移、hidden更新

```html
<!-- app_factory.py 内の head: deep query は Python 側でIIFE文字列として埋込み -->
<script>
// deep query (概略)
const qsDeep = (sel) => { /* gradio-app.shadowRoot を再帰探索して1つ返す */ };
const qsWithin = (root, sel) => { /* root配下をshadowRoot含め再帰探索 */ };

// hidden を安全に更新（2回目以降も反応するよう）
const setValueC = (cls, value) => {
  const root = qsDeep('.' + cls) || document.querySelector('.' + cls);
  const inp = root?.querySelector('textarea, input');
  if (!inp) return false;
  inp.value = value;
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  return true;
};

// スレッドクリック → hidden(kind/id) 更新 → openトリガ →（Threadsタブなら）Chatタブ選択
document.addEventListener('click', (e) => {
  const path = e.composedPath?.() || [e.target];
  let el = null; for (const n of path) { if (n?.closest) { el = n.closest('.thread-link'); if (el) break; } }
  if (!el) return;
  const tid = el.getAttribute('data-tid') || '';
  setValueC('th_action_kind', '');
  setTimeout(() => { setValueC('th_action_id', tid); setValueC('th_action_kind', 'open'); }, 0);

  // Threadsタブ上なら Chat タブへ（最大3回程度）
  const ensureChatTab = (n=3) => {
    if (n <= 0) return;
    const tabs = (qsDeep('[role="tab"]') && [qsDeep('[role="tab"]')]) || Array.from(document.querySelectorAll('[role="tab"]'));
    const chat = tabs.find(t => (t.textContent||'').includes('チャット'));
    if (chat && chat.getAttribute('aria-selected') !== 'true') {
      try { chat.click(); } catch {}
      setTimeout(() => ensureChatTab(n-1), 80);
    }
  };
  const inThreadsTab = path.some(n => n && n.id === 'threads_list_tab');
  if (inThreadsTab) ensureChatTab(3);
});

// 右クリックメニュー: リネームは現タイトルを初期値、削除は確認ダイアログ
document.addEventListener('contextmenu', (e) => {
  // ... ensureCtx で .ctx-menu を作成し、クリック時に以下:
  // rename → prompt(currentTitle) → setValueC('th_action_arg', newTitle) → id → kind=rename
  // delete → confirm(title) OKなら → id → kind=delete
});
</script>
```

### 2) Python: イベントチェーンで一括再描画（サイドバー/タブ）

```python
# app_factory.py 主要部（概略）

def _build_threads_html(items: list[dict]) -> str: ...
def _refresh_threads_tab():
    items = ui_list_threads()
    html = _build_threads_html(items)
    return gr.update(value=html), items

# kind 変化で rename/delete を処理し、両リストへ同一HTML出力
def _dispatch_action_common(kind: str, tid: str, cur_tid: str, arg: str):
    if kind == 'rename' and tid and arg:
        with db_session() as s:
            ThreadRepository(s).rename(tid, arg)
        html = _build_threads_html(ui_list_threads())
        return cur_tid, gr.update(), gr.update(value=html)
    if kind == 'delete' and tid:
        with db_session() as s:
            ThreadRepository(s).archive(tid)
        # 選択解除と再描画
        new_cur = '' if cur_tid == tid else cur_tid
        html = _build_threads_html(ui_list_threads())
        new_hist = [] if new_cur == '' else ui_list_messages(new_cur)
        return new_cur, new_hist, gr.update(value=html)
    # open など他は省略

def _dispatch_action_both(kind: str, tid: str, cur_tid: str, arg: str):
    new_cur, new_hist, html = _dispatch_action_common(kind, tid, cur_tid, arg)
    return new_cur, new_hist, html, html  # サイドバー/タブ 両方に同一HTML

# Threadsタブ構築時に、kind変更のイベントにタブ再描画を then で接続
_evt_kind = action_kind.change(
    _dispatch_action_both,
    inputs=[action_kind, action_thread_id, current_thread_id, action_arg],
    outputs=[current_thread_id, chat, threads_html, threads_html_tab],
)
_evt_kind.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

# サイドバーの「＋ 新規」も then でタブ側に反映
_evt_new = new_btn.click(_on_new, None, [threads_html, threads_state, current_thread_id, chat])
_evt_new.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])
```

### 3) Python: チャット保存（ユーザ/アシスタント）

```python
# chat_feature.py（概略）
from app.services.thread_service import ThreadService

def guard_and_prep(message: str, history, thread_id: str = ''):
    # ... 省略
    if thread_id:
        ThreadService().add_user_message(thread_id, text)
    return history, status, stop, send, msg, go, prompt

def stream_llm(go: bool, prompt: str, history, thread_id: str = ''):
    # ... ストリーム更新 ...
    if thread_id and body:
        ThreadService().add_assistant_message(thread_id, body)
    yield history, status, stop, send
```

### 4) Python: リポジトリの論理削除フィルタ

```python
# repositories/thread_repo.py（概略）
def list_recent(self, limit: int = 50) -> list[Thread]:
    stmt = (
        select(Thread)
        .where(Thread.archived.is_(False))  # ← UI側でのフィルタではなくSQLで排除
        .order_by(Thread.last_message_at.desc().nullslast(), Thread.created_at.desc())
        .limit(limit)
    )
    return list(self.session.scalars(stmt).all())
```


