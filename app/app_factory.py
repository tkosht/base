"""FastAPI + Gradio のアプリ組み立て。

`app/demo.py` の組立ロジックを移設し、公開 API として `create_app()` を提供する。
挙動は変更しない（ルート、マニフェスト、favicon、/gradio マウント等）。
"""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import gradio as gr

from .svg_utils import make_favicon_data_uri, build_favicon_svg, write_emoji_svg
from .chat_feature import guard_and_prep, stream_llm, stop_chat
from .search_feature import suggest, on_change, chips_html


def create_blocks() -> gr.Blocks:
    USER_AVATAR_PATH = write_emoji_svg(
        "💻",
        "/tmp/gradio_user_avatar.svg",
        bg="#DBEAFE",
        pad=6,
        emoji_scale=0.82,
        dy_em=0.02,
    )
    BOT_AVATAR_PATH = write_emoji_svg(
        "🦜", "/tmp/gradio_bot_avatar.svg", bg="#E5E7EB"
    )

    with gr.Blocks(
        title="でもあぷり",
        head=f"""
  <link rel=\"icon\" href=\"{make_favicon_data_uri('🦜', size=64, circle_fill='#1f2937', ring_color='#fff', ring_width=2)}\" />
  <link rel=\"stylesheet\" href=\"/public/styles/app.css\" />
""",
    ) as demo:
        gr.Markdown("### デモアプリ")

        with gr.Tabs():
            with gr.TabItem("チャット"):
                chat = gr.Chatbot(
                    height=420,
                    avatar_images=(USER_AVATAR_PATH, BOT_AVATAR_PATH),
                    label="Bot",
                    type="messages",
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

        demo.queue(max_size=16, default_concurrency_limit=4)
    return demo


def create_app() -> FastAPI:
    demo = create_blocks()

    public_dir = Path(__file__).resolve().parent.parent / "public"
    manifest_path = public_dir / "manifest.json"
    os.makedirs(public_dir, exist_ok=True)

    if not manifest_path.exists():
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

    api = FastAPI()
    api.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    @api.get("/manifest.json")
    def _manifest_file():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")

    gr.mount_gradio_app(api, demo, path="/gradio")

    @api.get("/")
    def _root():
        return RedirectResponse(url="/gradio")

    favicon_path = public_dir / "favicon.ico"
    if not favicon_path.exists():
        svg = build_favicon_svg("🦜", size=64, circle_fill="#1f2937", ring_color="#fff", ring_width=2)
        (public_dir / "favicon.svg").write_text(svg, encoding="utf-8")
        favicon_path.write_text(svg, encoding="utf-8")

    @api.get("/favicon.ico")
    def _favicon():
        return FileResponse(str(favicon_path), media_type="image/svg+xml")

    return api


