import time
import os
import urllib.parse
import gradio as gr
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import uvicorn


# ====== 絵文字SVG（ローカルSVGアバター用） ======
def write_emoji_svg(
    emoji: str,
    dest_path: str,
    size: int = 128,  # ← 大きめで作っておく（レンダ時に縮小されても滑らか）
    bg: str | None = "#FFFFFF",
    pad: int = 0,  # ← 余白ゼロ（外側の黒帯の原因を断つ）
    emoji_scale: float = 0.90,  # ← 絵文字自体を大きく
    dy_em: float = 0.00,
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


# ====== Favicon (data URI SVG) ======
def make_favicon_data_uri(
    emoji: str = "💻",
    size: int = 64,
    circle_fill: str = "#111827",
    ring_color: str = "#ffffff",
    ring_width: int = 2,
    emoji_scale: float = 0.80,
    dy_em: float = 0.00,
) -> str:
    """Build a small SVG favicon as a data URI.

    Using a data URI avoids setting up static file serving routes.
    """
    cx = cy = size / 2
    r = (size - ring_width * 2) / 2
    font_px = int(size * emoji_scale)
    svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>
  <circle cx='{cx}' cy='{cy}' r='{r}' fill='{circle_fill}' stroke='{ring_color}' stroke-width='{ring_width}'/>
  <text x='50%' y='50%' dominant-baseline='central' text-anchor='middle' font-size='{font_px}' dy='{dy_em}em'
        style='font-family: Noto Color Emoji, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, Twemoji Mozilla, EmojiOne Color, Android Emoji, sans-serif'>{emoji}</text>
</svg>""".strip()
    data = urllib.parse.quote(svg)
    return f"data:image/svg+xml;utf8,{data}"


def build_favicon_svg(
    emoji: str = "💻",
    size: int = 64,
    circle_fill: str = "#111827",
    ring_color: str = "#ffffff",
    ring_width: int = 2,
    emoji_scale: float = 0.80,
    dy_em: float = 0.00,
) -> str:
    cx = cy = size / 2
    r = (size - ring_width * 2) / 2
    font_px = int(size * emoji_scale)
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}'>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{circle_fill}' stroke='{ring_color}' stroke-width='{ring_width}'/>"
        f"<text x='50%' y='50%' dominant-baseline='central' text-anchor='middle' font-size='{font_px}' dy='{dy_em}em' "
        "style='font-family: Noto Color Emoji, Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, Twemoji Mozilla, EmojiOne Color, Android Emoji, sans-serif'>"
        f"{emoji}</text></svg>"
    )


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
    return (
        "<div class='chips'>"
        + "".join(f"<span class='chip'>{v}</span>" for v in vals)
        + "</div>"
    )


def neutralize_email(s: str) -> str:
    ZWSP = "\u200b"
    return s.replace("@", f"{ZWSP}@{ZWSP}")


def suggest(q, current_dropdown_value, selected_state):
    q = (q or "").strip()
    if len(q) < 2:
        merged = sorted(set(selected_state or []))
        return (
            gr.update(choices=merged, value=current_dropdown_value),
            "2文字以上で検索してください。",
        )
    hits = _search_users(q)
    merged = sorted(set(hits) | set(selected_state or []))
    hint = (
        f"{len(hits)}件ヒット｜候補例: "
        + ", ".join(neutralize_email(h) for h in hits[:3])
        + (" …" if len(hits) > 3 else "")
    )
    return gr.update(choices=merged, value=current_dropdown_value), hint


# ====== チャット ======
def llm_stream(_prompt):
    for t in (
        [
            "了解です。 ",
            "少しずつ返答をストリームします。",
            "\n\n- 箇条書き\n- もOK\n\n`code` にも対応します。",
        ]
        + (["."] * 20)
        + ["\n\n", "(回答完了)"]
    ):
        time.sleep(0.25)
        yield t


def guard_and_prep(message: str, history):
    history = history or []
    text = (message or "").strip()
    if not text:
        return (
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(),
            False,
            "",
        )
    history = history + [(message, "⌛ typing...")]
    return (
        history,
        "⌛ 回答生成中...",
        gr.update(visible=True, interactive=True),  # stop
        gr.update(visible=False),  # send
        "",  # msg clear
        True,  # go flag
        text,  # prompt
    )


def stream_llm(go: bool, prompt: str, history):
    if not go:
        yield gr.update(), gr.update(), gr.update(), gr.update()
        return
    history = history or []
    body = ""
    for tok in llm_stream(prompt):
        body += tok
        history[-1] = (history[-1][0], body)
        yield history, "⌛ 回答生成中...", gr.update(
            visible=True, interactive=True
        ), gr.update(visible=False)
    yield history, "回答生成完了", gr.update(
        visible=False, interactive=False
    ), gr.update(visible=True)


# ====== UI ======
USER_AVATAR_PATH = write_emoji_svg(
    "💻",
    "/tmp/gradio_user_avatar.svg",
    bg="#DBEAFE",
    pad=6,  # 円の内側に安全余白
    emoji_scale=0.82,  # 角欠け防止のため若干縮小
    dy_em=0.02,  # わずかに下げて上端の接触を回避
)
BOT_AVATAR_PATH = write_emoji_svg(
    "🦜", "/tmp/gradio_bot_avatar.svg", bg="#E5E7EB"
)

with gr.Blocks(
    css=r"""
/* =================== Tokens =================== */
:root{
  --avatar-base: 32px;     /* 内部が32pxでもOK：基準実寸（触らない） */
  --avatar-zoom: 1.1;      /* ← 見かけの拡大率（2.0〜3.2で調整） */
  --avatar-gap: .3rem;     /* アバターと本文の隙間 */
  --avatar-shift-y: -2px;  /* 上下微調整（負=上へ） */
  --avatar-ring: 0px;      /* ← 外周の白リングの太さ（見え方確認用） */

  --text:#111827; --card:#fff; --card-border:#e5e7eb; --code-bg:#f8fafc;
  --chat-btn-gap:10px; --stop-nudge:12px; --stop-diameter:36px;
  --stop-bg:#6b7280; --send-bg:#60A5FA; --stop-total-w:var(--stop-diameter);
  --chip-bg:#e5e7eb; --search-band-bg:#F1F5F9; --search-band-radius:10px; --search-band-pad:12px;
  --search-bg:#EEF2FF; --search-text:#111827; --search-border:#BFDBFE; --search-ph:#6B7280;
  --search-bg-focus:#fff; --search-outline:rgba(37,99,235,.25);
}

/* ===== Chat bubbles ===== */
.gr-chatbot .message{
  background:var(--card) !important; color:var(--text) !important;
  border:1px solid var(--card-border) !important; border-radius:14px !important; box-shadow:none !important;
}
.gr-chatbot .message-row{ box-shadow:none !important; background:transparent !important; }

/* ===== アバター列：列幅は拡大後寸法に合わせる ===== */
.gr-chatbot .message-row{
  display:grid !important;
  /* 列1 = 見かけ寸法（base × zoom）、列2 = 本文 */
  grid-template-columns: calc(var(--avatar-base) * var(--avatar-zoom)) 1fr !important;
  align-items:center !important;
  column-gap: var(--avatar-gap) !important;
  /* 行の高さも見かけ寸法に合わせる */
  min-height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  overflow:visible !important;
}

/* avatar sizing now handled by .avatar-container */

/* legacy inner selectors removed */

/* image centering is handled by .avatar-container > img */

/* avatar-image direct rule removed; .avatar-container covers it */

/* GradioのDOMで用いられる avatar-container を直接拡大（確実適用） */
.avatar-container{
  width: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  min-width: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  min-height: calc(var(--avatar-base) * var(--avatar-zoom)) !important;
  display:grid !important; place-items:center !important;
  border-radius:9999px !important; overflow:visible !important;
  background:#fff !important;
  box-shadow: 0 0 0 var(--avatar-ring) #fff !important;
}
.avatar-container > :is(img,svg){
  width:100% !important; height:100% !important; display:block !important;
  object-fit:contain !important;
  object-position: center calc(50% + var(--avatar-shift-y)) !important;
  border-radius:9999px !important;
}

/* fallbacks removed; container-based sizing is sufficient */

/* ===== 入力行（既存のまま） ===== */
#msgrow{ position:relative; width:100%; }
#msgrow .gr-button > button{ min-width:0 !important; }
#stopbtn,#sendbtn{
  position:absolute; top:50%; transform:translateY(-50%);
  right:calc(var(--chat-btn-gap) + var(--stop-nudge));
  width:var(--stop-diameter) !important; height:var(--stop-diameter) !important;
  border-radius:9999px !important; display:flex; align-items:center; justify-content:center;
  padding:0 !important; margin:0 !important; z-index:5;
}
#stopbtn{ background:var(--stop-bg) !important; } #sendbtn{ background:var(--send-bg) !important; }
#stopbtn > button,#sendbtn > button{
  width:100% !important; height:100% !important; background:transparent !important; color:#fff !important;
  border:none !important; box-shadow:none !important; font-size:14px; line-height:1;
  display:inline-flex; align-items:center; justify-content:center;
}
#msgrow input,#msgrow textarea{
  padding-right:calc(var(--stop-total-w) + var(--chat-btn-gap) + var(--stop-nudge)) !important;
}
#msgrow .gr-textbox{ margin-bottom:0 !important; }

/* ===== ステータス / 検索UI（省略可、既存どおり） ===== */
#status{ min-height:1.6em; line-height:1.6em; overflow:hidden !important; }
#status *{ overflow:hidden !important; margin:0 !important; }
#status .prose,#status .markdown,#status .gr-prose{ white-space:nowrap; text-overflow:ellipsis; }
.combo-field .wrap, .combo-field .wrap.svelte-1ipelgc{ gap:.5rem; }
.combo-field .gr-textbox input{ border-top-right-radius:0; border-bottom-right-radius:0; }
.combo-field .gr-button{ border-top-left-radius:0; border-bottom-left-radius:0; }
.combo-field .chips{ display:flex; flex-wrap:wrap; gap:.4rem; margin-top:.25rem; }
.combo-field .chip{ background:var(--chip-bg); border-radius:9999px; padding:.2rem .6rem; font-size:.9rem; }
.combo-hint{ opacity:.8; margin-top:.25rem; }
#search_band{ background:var(--search-band-bg) !important; border-radius:var(--search-band-radius); padding:var(--search-band-pad); }
#search_band .gr-textbox,#search_band .gr-button{ margin-top:0 !important; margin-bottom:0 !important; }
#searchbox input,#searchbox textarea{ background:var(--search-bg) !important; color:var(--search-text) !important; border-color:var(--search-border) !important; }
#searchbox input::placeholder,#searchbox textarea::placeholder{ color:var(--search-ph) !important; opacity:1; }
#searchbox input:focus,#searchbox textarea:focus{
  background:var(--search-bg-focus) !important; border-color:#2563EB !important;
  box-shadow:0 0 0 3px var(--search-outline) !important; outline:none !important;
}

""",
    title="でもあぷり",
    head=f"""
  <link rel=\"icon\" href=\"{make_favicon_data_uri('🦜', size=64, circle_fill='#1f2937', ring_color='#fff', ring_width=2)}\" />
""",
) as demo:

    gr.Markdown("### デモアプリ")

    with gr.Tabs():
        with gr.TabItem("チャット"):
            chat = gr.Chatbot(
                height=420,
                avatar_images=(USER_AVATAR_PATH, BOT_AVATAR_PATH),
                label="Bot",
            )

            gr.Markdown("**User**")
            with gr.Group(elem_id="msgrow"):
                msg = gr.Textbox(
                    placeholder="Markdownで入力できます（**太字**、`code` など）",
                    show_label=False,
                    lines=1,
                )
                stop = gr.Button(
                    "⏹", elem_id="stopbtn", visible=False, interactive=False
                )
                send = gr.Button("↑", elem_id="sendbtn", visible=True)

            status = gr.Markdown(
                "準備OK! いつでもチャットを開始できます。", elem_id="status"
            )

            go_flag = gr.State(False)
            prompt_st = gr.State("")

            guard_evt_enter = msg.submit(
                guard_and_prep,
                inputs=[msg, chat],
                outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
            )
            stream_evt_enter = guard_evt_enter.then(
                stream_llm,
                inputs=[go_flag, prompt_st, chat],
                outputs=[chat, status, stop, send],
            )

            guard_evt_send = send.click(
                guard_and_prep,
                inputs=[msg, chat],
                outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
            )
            stream_evt_send = guard_evt_send.then(
                stream_llm,
                inputs=[go_flag, prompt_st, chat],
                outputs=[chat, status, stop, send],
            )

            def stop_chat():
                return (
                    gr.update(visible=False, interactive=False),
                    gr.update(visible=True),
                    "実行中の処理を停止しました。",
                )

            stop.click(
                stop_chat,
                None,
                [stop, send, status],
                cancels=[stream_evt_enter, stream_evt_send],
            )

        with gr.TabItem("設定"):
            with gr.Group(elem_classes=["combo-field"]):
                with gr.Row(elem_id="search_title_band"):
                    gr.Markdown("**検索フォーム**")
                with gr.Row(equal_height=True, elem_id="search_band"):
                    search_box = gr.Textbox(
                        placeholder="キーワードを入力して Enter or 検索ボタンを押してください（2文字以上） ",
                        show_label=False,
                        scale=4,
                        elem_id="searchbox",
                    )
                    search_btn = gr.Button("検索", scale=1)

                selected = [
                    "テスト1(test1@test.com)",
                    "テスト2(test2@test.com)",
                    "テスト3(test3@test.com)",
                ]
                selected_state = gr.State(selected)
                hit_info = gr.Markdown("", elem_classes=["combo-hint"])
                combo = gr.Dropdown(
                    choices=selected_state.value,
                    value=selected_state.value,
                    multiselect=True,
                    show_label=True,
                    label="候補（複数選択可）",
                )
                chips = gr.HTML(chips_html([]))

            search_box.submit(
                suggest, [search_box, combo, selected_state], [combo, hit_info]
            )
            search_btn.click(
                suggest, [search_box, combo, selected_state], [combo, hit_info]
            )

            def on_change(new_value, _state):
                vals = sorted(set(new_value or []))
                return vals, chips_html(vals)

            combo.change(
                on_change, [combo, selected_state], [selected_state, chips]
            )

            save_btn = gr.Button("保存")
            out = gr.JSON()
            save_btn.click(
                lambda v: {"selected": v},
                inputs=[selected_state],
                outputs=[out],
            )

    # Gradio Queue はマウント前に有効化（重要）
    # 併走数は default_concurrency_limit で指定（各イベント未指定時のデフォルト）
    demo.queue(max_size=16, default_concurrency_limit=4)

    # --- Static manifest setup (extensible) ---
    public_dir = Path(__file__).resolve().parent.parent / "public"
    manifest_path = public_dir / "manifest.json"
    os.makedirs(public_dir, exist_ok=True)

    if not manifest_path.exists():
        # 初期テンプレートを自動生成（必要に応じて後から編集できます）
        manifest_path.write_text(
            (
                '{\n'
                '  "name": "でもあぷり",\n'
                '  "short_name": "でもあぷり",\n'
                '  "start_url": ".",\n'
                '  "display": "standalone",\n'
                '  "background_color": "#111827",\n'
                '  "theme_color": "#111827",\n'
                '  "icons": []\n'
                '}\n'
            ),
            encoding="utf-8",
        )

    # Gradio を FastAPI にマウントして拡張ルートを使えるようにする
    api = FastAPI()

    # /public/* を静的配信
    api.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    # ルートで要求される /manifest.json はファイルを返す
    @api.get("/manifest.json")
    def _manifest_file():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")

    # Gradio Blocks を /gradio にマウント（ルートを占有しない）
    gr.mount_gradio_app(api, demo, path="/gradio")

    # ルートは /gradio へリダイレクト
    @api.get("/")
    def _root():
        return RedirectResponse(url="/gradio")

    # /favicon.ico を提供（gunicornなどで自動アクセスされるため）
    favicon_path = public_dir / "favicon.ico"
    if not favicon_path.exists():
        # SVG → ICO 変換は避け、SVGを .ico として返す簡易対応（Chromium系はOK）
        svg = build_favicon_svg("🦜", size=64, circle_fill="#1f2937", ring_color="#fff", ring_width=2)
        (public_dir / "favicon.svg").write_text(svg, encoding="utf-8")
        # 拡張子 .ico にも同内容を置く（多くのブラウザはSVGを受理）
        favicon_path.write_text(svg, encoding="utf-8")

    @api.get("/favicon.ico")
    def _favicon():
        # SVGを ICO として返す（互換性十分、必要なら本物のICOに差し替え可能）
        return FileResponse(str(favicon_path), media_type="image/svg+xml")

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=7860)
