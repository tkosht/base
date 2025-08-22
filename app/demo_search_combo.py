# app_tabs_chat_md_avatar_file.py
import time
import os
import gradio as gr

# ====== 絵文字SVGを書き出して、ファイルパスを返す ======
def write_emoji_svg(emoji: str, dest_path: str, size: int = 64, bg: str | None = None) -> str:
    # 背景を丸く塗る（Noneなら透明）
    bg_rect = f"<rect width='{size}' height='{size}' rx='{size//2}' fill='{bg}'/>" if bg else ""
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  {bg_rect}
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        font-size="{int(size*0.72)}"
        font-family="Noto Color Emoji, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, Twemoji Mozilla, EmojiOne Color, Android Emoji, sans-serif">{emoji}</text>
</svg>"""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(svg)
    return dest_path

# ====== ダミー検索（実運用では MS Graph 等に置換） ======
def _search_users(query: str, top: int = 30) -> list[str]:
    if not query:
        return []
    q = query.lower()
    hits = []
    for i in range(1, 400):
        label = f"test{i}"
        mail = f"test{i}@test.com"
        if q in label.lower() or q in mail.lower():
            hits.append(label)
        if len(hits) >= top:
            break
    return hits

def chips_html(values):
    vals = values or []
    return "<div class='chips'>" + "".join(f"<span class='chip'>{v}</span>" for v in vals) + "</div>"

def suggest(q, current_dropdown_value, selected_state):
    q = (q or "").strip()
    if len(q) < 2:
        merged = sorted(set(selected_state or []))
        return gr.update(choices=merged, value=current_dropdown_value), "2文字以上で検索してください。"
    hits = _search_users(q)
    merged = sorted(set(hits) | set(selected_state or []))
    hint = f"{len(hits)}件ヒット｜候補例: " + ", ".join(hits[:3]) + (" …" if len(hits) > 3 else "")
    return gr.update(choices=merged, value=current_dropdown_value), hint

# ====== チャット ======
def llm_stream(_prompt):
    for t in [
        "了解です。 少しずつ返答をストリームします。",
        "\n\n- 箇条書き\n- もOK\n\n`code` にも対応します。"
    ]:
        time.sleep(0.25)
        yield t

def chat_respond(message, history):
    history = history or []
    history.append((message, "⌛ typing..."))
    yield history
    body = ""
    for tok in llm_stream(message):
        body += tok
        history[-1] = (history[-1][0], body)
        yield history

# ====== UI ======
# SVGファイルを用意（/tmp に書く）
USER_AVATAR_PATH = write_emoji_svg("💻", "/tmp/gradio_user_avatar.svg", bg="#DBEAFE")
BOT_AVATAR_PATH  = write_emoji_svg("🦜",  "/tmp/gradio_bot_avatar.svg",  bg="#E5E7EB")

with gr.Blocks(css=r"""
/* ===== Chatbot：白バブル＋黒文字（一重バブル） ===== */
.gr-chatbot .message {
  background: #ffffff !important;
  color: #111827 !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
.gr-chatbot .message * { color: #111827 !important; }
.gr-chatbot .message pre, .gr-chatbot .message code {
  background: #f8fafc !important;
  border: 1px solid #e5e7eb !important;
  color: #111827 !important;
}
.gr-chatbot .message-row { box-shadow: none !important; background: transparent !important; }

/* ===== 検索UI（上：入力＋ボタン／下：ドロップダウン） ===== */
.combo-field .wrap.svelte-1ipelgc { gap: .5rem; }
.combo-field .gr-textbox input { border-top-right-radius: 0; border-bottom-right-radius: 0; }
.combo-field .gr-button { border-top-left-radius: 0; border-bottom-left-radius: 0; }
.combo-field .chips { display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.25rem; }
.combo-field .chip { background:#e5e7eb; border-radius:9999px; padding:.2rem .6rem; font-size:.9rem; }
.combo-hint { opacity:.8; margin-top:.25rem; }
""") as demo:
    gr.Markdown("### チャット（黒文字・一重バブル・外側アイコン） と 検索")

    with gr.Tabs():
        # ---- タブ1: チャット ----
        with gr.TabItem("チャット"):
            # ★ 公式アバター機能に“ローカルSVGファイル”のパスを渡す
            chat = gr.Chatbot(height=420, avatar_images=(USER_AVATAR_PATH, BOT_AVATAR_PATH))
            msg = gr.Textbox(placeholder="Markdownで入力できます（**太字**、`code` など）")
            stop = gr.Button("停止")
            evt = msg.submit(chat_respond, [msg, chat], [chat]).then(lambda: "", None, [msg])
            stop.click(None, None, None, cancels=[evt])

        # ---- タブ2: 検索 ----
        with gr.TabItem("検索"):
            with gr.Group(elem_classes=["combo-field"]):
                gr.Markdown("**ユーザー検索（検索→選択）**")
                with gr.Row(equal_height=True):
                    search_box = gr.Textbox(
                        placeholder="キーワードを入力して Enter（2文字以上）",
                        show_label=False, scale=4
                    )
                    search_btn = gr.Button("検索", scale=1)

                combo = gr.Dropdown(choices=[], value=[], multiselect=True, show_label=True, label="候補（複数選択可）")
                hit_info = gr.Markdown("", elem_classes=["combo-hint"])
                chips = gr.HTML(chips_html([]))
                selected_state = gr.State([])

            search_box.submit(suggest, [search_box, combo, selected_state], [combo, hit_info])
            search_btn.click(suggest, [search_box, combo, selected_state], [combo, hit_info])

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
