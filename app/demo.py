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
    pad: int = 6,
    emoji_scale: float = 0.66,
    dy_em: float = 0.06
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


# ====== ダミー検索 ======
def _search_users(query: str, top: int = 30) -> list[str]:
    if not query:
        return []
    q = query.lower()
    hits = []
    for i in range(1, 400):
        mail = f"test{i}@test.com"
        label = f"テスト{i}({mail})"
        if q in label.lower() or q in mail.lower():
            hits.append(label)
        if len(hits) >= top:
            break
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
    for t in [
        "了解です。 ",
        "少しずつ返答をストリームします。",
        "\n\n- 箇条書き\n- もOK\n\n`code` にも対応します。"
    ] + (["."] * 20) + ["\n\n", "(回答完了)"]:
        time.sleep(0.25)
        yield t

# 第1段：ガード＆準備（非ストリーム）
# 出力: chat, status, stop, msg, go_flag, prompt
def guard_and_prep(message: str, history):
    history = history or []
    text = (message or "").strip()

    if not text:
        # 空のときは完全に無反応（全アウトプット no-op）
        return gr.update(), gr.update(), gr.update(), gr.update(), False, ""

    # 非空：履歴に下書き・停止有効化・Textbox即クリア
    history = history + [(message, "⌛ typing...")]
    return history, "⌛ 回答生成中...", gr.update(interactive=True), "", True, text

# 第2段：ストリーム（generator）
# 入出力: go_flag, prompt, history -> chat, status, stop
def stream_llm(go: bool, prompt: str, history):
    if not go:
        # 空経路：UI変更なしで即終了
        yield gr.update(), gr.update(), gr.update()
        return

    history = history or []
    body = ""
    for tok in llm_stream(prompt):
        body += tok
        history[-1] = (history[-1][0], body)
        yield history, "⌛ 回答生成中...", gr.update()

    yield history, "回答生成完了", gr.update(interactive=False)


# ====== UI ======
USER_AVATAR_PATH = write_emoji_svg("💻", "/tmp/gradio_user_avatar.svg", bg="#DBEAFE")
BOT_AVATAR_PATH  = write_emoji_svg("🦜",  "/tmp/gradio_bot_avatar.svg",  bg="#E5E7EB")

with gr.Blocks(css=r"""
/* =================== Design Tokens =================== */
:root{
  /* ベース */
  --text: #111827;
  --card: #ffffff;
  --card-border: #e5e7eb;
  --code-bg: #f8fafc;

  /* アバター */
  --avatar-size: 48px;
  --avatar-ring: 6px;

  /* チャット入力（停止ボタン） */
  --chat-btn-gap: 10px;       /* 入力右端とのベース距離 */
  --stop-nudge: 12px;         /* 右端ボーダーから少し左へ寄せる量（px） */
  --stop-diameter: 36px;      /* ★ 円の直径（これで大きさ決定） */
  --stop-bg: #6b7280;         /* 円の色 */
  --stop-total-w: var(--stop-diameter); /* 入力欄パディング計算用 */

  /* 検索UI */
  --chip-bg: #e5e7eb;

  /* 設定タブ：検索フォーム帯＆検索ボックス */
  --search-band-bg: #F1F5F9;
  --search-band-radius: 10px;
  --search-band-pad: 12px;

  --search-bg:        #EEF2FF;
  --search-text:      #111827;
  --search-border:    #BFDBFE;
  --search-ph:        #6B7280;
  --search-bg-focus:  #FFFFFF;
  --search-outline:   rgba(37,99,235,.25);
}

/* ---------- Chatbot バブル ---------- */
.gr-chatbot .message{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--card-border) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
}
.gr-chatbot .message pre,
.gr-chatbot .message code{
  background: var(--code-bg) !important;
  border: 1px solid var(--card-border) !important;
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

/* ---------- 検索UI（共通） ---------- */
.combo-field .wrap, .combo-field .wrap.svelte-1ipelgc{ gap:.5rem; }
.combo-field .gr-textbox input{ border-top-right-radius:0; border-bottom-right-radius:0; }
.combo-field .gr-button{ border-top-left-radius:0; border-bottom-left-radius:0; }
.combo-field .chips{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.25rem; }
.combo-field .chip{ background:var(--chip-bg); border-radius:9999px; padding:.2rem .6rem; font-size:.9rem; }
.combo-hint{ opacity:.8; margin-top:.25rem; }

/* ---------- チャット入力行（停止ボタンを“円”で右内側に） ---------- */
#msgrow{ position: relative; width:100%; }
#msgrow .gr-button > button{ min-width:0 !important; }

/* 円形のバッジはラッパー側（#stopbtn）に背景を付ける */
#stopbtn{
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: calc(var(--chat-btn-gap) + var(--stop-nudge)); /* ← ここで“ほんの少し左へ”寄せられる */
  width: var(--stop-diameter) !important;
  height: var(--stop-diameter) !important;
  border-radius: 9999px !important;
  background: var(--stop-bg) !important;
  display: flex; align-items: center; justify-content: center;
  padding: 0 !important; margin: 0 !important;
  z-index: 5;
}

/* 内側ボタンは円いっぱいをクリック可能に（透明） */
#stopbtn > button{
  width: 100% !important;
  height: 100% !important;
  background: transparent !important;
  color: #fff !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 14px; line-height: 1;
  display: inline-flex; align-items: center; justify-content: center;
}

/* 入力テキストが円に重ならないよう右パディング確保 */
#msgrow input, #msgrow textarea{
  padding-right: calc(var(--stop-total-w) + var(--chat-btn-gap) + var(--stop-nudge)) !important;
}
#msgrow .gr-textbox{ margin-bottom: 0 !important; }

/* ステータス：1行・スクロール禁止 */
#status{ min-height:1.6em; line-height:1.6em; overflow:hidden !important; }
#status *{ overflow:hidden !important; margin:0 !important; }
#status .prose, #status .markdown, #status .gr-prose{ white-space:nowrap; text-overflow:ellipsis; }

/* ---------- 設定タブ：検索フォーム帯＆検索ボックス ---------- */
#search_band{
  background: var(--search-band-bg) !important;
  border-radius: var(--search-band-radius);
  padding: var(--search-band-pad);
}
#search_band .gr-textbox, #search_band .gr-button{
  margin-top:0 !important; margin-bottom:0 !important;
}
#searchbox input, #searchbox textarea{
  background: var(--search-bg) !important;
  color: var(--search-text) !important;
  border-color: var(--search-border) !important;
}
#searchbox input::placeholder, #searchbox textarea::placeholder{
  color: var(--search-ph) !important; opacity:1;
}
#searchbox input:focus, #searchbox textarea:focus{
  background: var(--search-bg-focus) !important;
  border-color: #2563EB !important;
  box-shadow: 0 0 0 3px var(--search-outline) !important;
  outline: none !important;
}
""") as demo:

    gr.Markdown("### デモアプリ")

    with gr.Tabs():
        # ---- タブ1: チャット ----
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

            # Enter → guard（空は no-op）→ stream（go=False は 1 回 no-op）
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

            def stop_chat():
                return gr.update(interactive=False), "実行中の処理を停止しました。"
            stop.click(stop_chat, None, [stop, status], cancels=[stream_evt])

        # ---- タブ2: 検索 ----
        with gr.TabItem("設定"):
            with gr.Group(elem_classes=["combo-field"]):
                with gr.Row(elem_id="search_title_band"):
                    gr.Markdown("**検索フォーム**")

                with gr.Row(equal_height=True, elem_id="search_band"):
                    search_box = gr.Textbox(
                        placeholder="キーワードを入力して Enter or 検索ボタンを押してください（2文字以上） ",
                        show_label=False, scale=4, elem_id="searchbox"
                    )
                    search_btn = gr.Button("検索", scale=1)

                selected = ["テスト1(test1@test.com)", "テスト2(test2@test.com)", "テスト3(test3@test.com)"]
                selected_state = gr.State(selected)
                hit_info = gr.Markdown("", elem_classes=["combo-hint"])
                combo = gr.Dropdown(choices=selected_state.value, value=selected_state.value,
                                    multiselect=True, show_label=True, label="候補（複数選択可）")
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
