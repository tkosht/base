# app_tabs_chat_md_avatar_file.py
import time
import os
import gradio as gr

# ====== 絵文字SVG（ローカルSVGアバター用） ======
def write_emoji_svg(
    emoji: str,
    dest_path: str,
    size: int = 64,
    bg: str | None = "#FFFFFF",
    pad: int = 6,                 # 余白（白円を相対的に大きく見せる）
    emoji_scale: float = 0.66,    # 絵文字サイズ（上部欠け防止でやや小さめ）
    dy_em: float = 0.06           # 視覚中心補正（少し下へ）
) -> str:
    inner = max(4, size - 2 * pad)
    cx = cy = size / 2
    r = inner / 2
    font_px = int(inner * emoji_scale)
    circle = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}"/>' if bg else ""
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  {circle}
  <text x="50%" y="50%" dominant-baseline="central" text-anchor="middle"
        font-size="{font_px}" dy="{dy_em}em"
        style="font-family: Noto Color Emoji, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, Twemoji Mozilla, EmojiOne Color, Android Emoji, sans-serif">{emoji}</text>
</svg>"""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return dest_path


# ====== 検索ダミー ======
def _search_users(query: str, top: int = 30) -> list[str]:
    if not query: return []
    q = query.lower()
    hits = []
    for i in range(1, 400):
        mail = f"test{i}@test.com"
        label = f"テスト{i}({mail})"
        if q in label.lower() or q in mail.lower():
            hits.append(label)
        if len(hits) >= top: break
    return hits

def chips_html(values):
    vals = values or []
    return "<div class='chips'>" + "".join(f"<span class='chip'>{v}</span>" for v in vals) + "</div>"

def neutralize_email(s: str) -> str:
    ZWSP = "\u200B"
    return s.replace("@", f"{ZWSP}@{ZWSP}")

def suggest(q, current_dropdown_value, selected_state):
    q = (q or "").strip()
    if len(q) < 2:
        merged = sorted(set(selected_state or []))
        return gr.update(choices=merged, value=current_dropdown_value), "2文字以上で検索してください。"
    hits = _search_users(q)
    merged = sorted(set(hits) | set(selected_state or []))
    hint = f"{len(hits)}件ヒット｜候補例: " + ", ".join(neutralize_email(h) for h in hits[:3]) + (" …" if len(hits) > 3 else "")
    return gr.update(choices=merged, value=current_dropdown_value), hint

# ====== チャット ======
def llm_stream(_prompt):
    for t in ["了解です。 ", "少しずつ返答をストリームします。",
              "\n\n- 箇条書き\n- もOK\n\n`code` にも対応します."] + (["."] * 20) + ["\n\n", "(回答完了)"]:
        time.sleep(0.25); yield t

# 第1段：ガード＆準備（返り値：chat, status, stop, msg, go_flag, prompt）
def guard_and_prep(message: str, history):
    history = history or []
    text = (message or "").strip()
    if not text:
        # 空時 → とにかく現状の履歴を返す（これで“表示クリア”は起きない）
        return history, "メッセージを入力してください。", gr.update(), gr.update(), False, ""
    # 非空時 → 下書き追加・stop有効化・入力欄クリア
    history = history + [(message, "⌛ typing...")]
    return history, "⌛ 回答生成中...", gr.update(interactive=True), "", True, text

# 第2段：ストリーム（go, prompt, history -> chat, status, stop）
def stream_llm(go: bool, prompt: str, history):
    history = history or []
    if not go:
        # 空ケース：一度だけ現状返して終了（再描画は最小）
        yield history, gr.update(), gr.update(); return
    body = ""
    for tok in llm_stream(prompt):
        body += tok
        history[-1] = (history[-1][0], body)
        yield history, "⌛ 回答生成中...", gr.update()
    yield history, "回答生成完了", gr.update(interactive=False)

# ====== UI ======
USER_AVATAR_PATH = write_emoji_svg("💻", "/tmp/gradio_user_avatar.svg", bg="#DBEAFE")
BOT_AVATAR_PATH  = write_emoji_svg("🦜", "/tmp/gradio_bot_avatar.svg", bg="#E5E7EB")

with gr.Blocks(css=r"""
:root{
  --avatar-size: 48px;
  --avatar-ring: 6px;           /* 白い外輪を太くして“白円が大きく”見える */
  --chat-btn-size: 24px;
  --chat-btn-gap: 8px;
  --stop-nudge: 6px;            /* 右端から左へ少し寄せる量 */
  --chip-bg: #e5e7eb;
  --stop-bg: #6b7280;
  --text: #111827;
  --card: #ffffff;
  --card-border: #e5e7eb;
  --code-bg: #f8fafc;
}

/* Chatbot（白一重バブル） */
.gr-chatbot .message{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
.gr-chatbot .message *{ color: var(--text) !important; }
.gr-chatbot .message pre, .gr-chatbot .message code{
  background: var(--code-bg) !important;
  border: 1px solid var(--card-border) !important;
  color: var(--text) !important;
}
.gr-chatbot .message-row{ box-shadow:none !important; background:transparent !important; }

/* アバター：サイズ＋白い外輪 */
.gr-chatbot .avatar, .gr-chatbot .avatar-image{
  width: var(--avatar-size) !important;
  height: var(--avatar-size) !important;
  border-radius: 9999px !important;
  background: #fff !important;
  box-shadow: 0 0 0 var(--avatar-ring) #fff;
  overflow: hidden;
}
.gr-chatbot .avatar > img, .gr-chatbot .avatar-image > img{
  width: 100% !important; height: 100% !important; object-fit: contain;
}

/* 検索UI */
.combo-field .wrap, .combo-field .wrap.svelte-1ipelgc{ gap:.5rem; }
.combo-field .gr-textbox input{ border-top-right-radius:0; border-bottom-right-radius:0; }
.combo-field .gr-button{ border-top-left-radius:0; border-bottom-left-radius:0; }
.combo-field .chips{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.25rem; }
.combo-field .chip{ background:var(--chip-bg); border-radius:9999px; padding:.2rem .6rem; font-size:.9rem; }
.combo-hint{ opacity:.8; margin-top:.25rem; }

/* 入力欄内の停止ボタン */
#msgrow { position: relative; display: inline-block; width: 100%; }
#msgrow .gr-button > button { min-width: 0 !important; }
#stopbtn{
  position: absolute; top:50%; transform: translateY(-50%);
  right: calc(var(--chat-btn-gap) + var(--chat-btn-size) * 0.2 + var(--stop-nudge));
  margin:0 !important; padding:0 !important; width:auto !important; z-index:5;
}
#stopbtn > button{
  width: var(--chat-btn-size) !important; height: var(--chat-btn-size) !important;
  padding:0 !important; border-radius:6px !important;
  display:inline-flex; align-items:center; justify-content:center;
  font-size:14px; line-height:1;
  background: var(--stop-bg) !important; color:#fff !important;
}
/* 右側の余白（ボタンと重ならないように） */
#msgrow input, #msgrow textarea{
  padding-right: calc(var(--chat-btn-size) * 2 + var(--chat-btn-gap) * 4 + var(--stop-nudge)) !important;
}
#msgrow .gr-textbox{ margin-bottom:0 !important; }

/* ステータスは1行・スクロール禁止 */
#status{ min-height:1.6em; line-height:1.6em; overflow:hidden !important; }
#status *{ overflow:hidden !important; margin:0 !important; }
#status .prose, #status .markdown, #status .gr-prose{ white-space:nowrap; text-overflow:ellipsis; }
""") as demo:
    gr.Markdown("### デモアプリ")

    with gr.Tabs():
        # ---- チャット ----
        with gr.TabItem("チャット"):
            chat = gr.Chatbot(height=420, avatar_images=(USER_AVATAR_PATH, BOT_AVATAR_PATH), label="Bot")

            gr.Markdown("**User**")
            with gr.Group(elem_id="msgrow"):
                msg  = gr.Textbox(
                    placeholder="Markdownで入力できます（**太字**、`code` など）",
                    show_label=False, lines=1
                )
                stop = gr.Button("⏹", elem_id="stopbtn", interactive=False)

            status = gr.Markdown("準備OK! いつでもチャットを開始できます。", elem_id="status")

            # 送信フロー：Enter で guard → stream（空は guard が“現状返して”終了）
            go_flag   = gr.State(False)
            prompt_st = gr.State("")
            guard_evt = msg.submit(
                guard_and_prep,
                inputs=[msg, chat],
                outputs=[chat, status, stop, msg, go_flag, prompt_st],
            )
            stream_evt = guard_evt.then(
                stream_llm,
                inputs=[go_flag, prompt_st, chat],
                outputs=[chat, status, stop],
            )

            # 停止：実行中をキャンセル
            def stop_chat():
                return gr.update(interactive=False), "実行中の処理を停止しました。"
            stop.click(stop_chat, None, [stop, status], cancels=[stream_evt])

            # ★ 空 Enter をフォーム層で完全抑止（非空は素通し）
            # gr.HTML("""
# <script>
# (function blockEmptySubmit(){
#   function stopAll(e){ e.preventDefault(); e.stopPropagation(); if(e.stopImmediatePropagation) e.stopImmediatePropagation(); }
#   function wire(){
    # const app  = (window.gradioApp && window.gradioApp()) || document;
    # const box  = app.querySelector('#msgrow textarea, #msgrow input');
    # if(!box){ setTimeout(wire, 150); return; }
    # if(box.__wiredEmpty) return;
    # box.__wiredEmpty = true;
# 
    # let composing = false;
    # box.addEventListener('compositionstart', ()=> composing = true);
    # box.addEventListener('compositionend',   ()=> composing = false);
# 
    # const form = box.closest('form');
    # if(form && !form.__wired){
    #   form.__wired = true;
    #   form.addEventListener('submit', (e)=>{
        # if(composing || e.isComposing) return;
        # const val = (box.value || '').trim();
        # if(!val) stopAll(e);             // 空 → 完全キャンセル（Gradio へ届かない）
    #   }, {capture:true});
    # }
# 
    # // 見た目のチラつき防止（任意）
    # box.addEventListener('keydown', (e)=>{
    #   if(e.key !== 'Enter' || e.shiftKey) return;
    #   if(composing || e.isComposing) return;
    #   const val = (box.value || '').trim();
    #   if(!val) stopAll(e);
    # }, {capture:true});
#   }
#   document.addEventListener('gradio:ready', wire);
#   wire();
# })();
# </script>
# """)
# 
        # ---- 設定（検索） ----
        with gr.TabItem("設定"):
            with gr.Group(elem_classes=["combo-field"]):
                gr.Markdown("**検索フォーム**")
                with gr.Row(equal_height=True):
                    search_box = gr.Textbox(placeholder="キーワードを入力して Enter or 検索ボタンを押してください（2文字以上） ", show_label=False, scale=4)
                    search_btn = gr.Button("検索", scale=1)

                selected = ["テスト1(test1@test.com)", "テスト2(test2@test.com)", "テスト3(test3@test.com)"]
                selected_state = gr.State(selected)
                combo = gr.Dropdown(choices=selected_state.value, value=selected_state.value,
                                    multiselect=True, show_label=True, label="候補（複数選択可）")
                hit_info = gr.Markdown("", elem_classes=["combo-hint"])
                chips = gr.HTML(chips_html([]))

            search_box.submit(suggest, [search_box, combo, selected_state], [combo, hit_info])
            search_btn.click(suggest,  [search_box, combo, selected_state], [combo, hit_info])

            def on_change(new_value, _state):
                vals = sorted(set(new_value or []))
                return vals, chips_html(vals)
            combo.change(on_change, [combo, selected_state], [selected_state, chips])

            save_btn = gr.Button("保存")
            out = gr.JSON()
            save_btn.click(lambda v: {"selected": v}, inputs=[selected_state], outputs=[out])

    demo.queue(max_size=16)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
