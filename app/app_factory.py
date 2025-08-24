"""FastAPI + Gradio のアプリ組み立て。

`app/demo.py` の組立ロジックを移設し、公開 API として `create_app()` を提供する。
挙動は変更しない（ルート、マニフェスト、favicon、/gradio マウント等）。
"""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import gradio as gr

from app.svg_utils import make_favicon_data_uri, build_favicon_svg, write_emoji_svg
from app.chat_feature import guard_and_prep, stream_llm, stop_chat
from app.search_feature import suggest, on_change, chips_html
from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import db_session
from app.repositories.thread_repo import ThreadRepository
from app.services.thread_service import ThreadService
from app.services.settings_service import SettingsService
from app.ui.threads_ui import (
    get_app_settings,
    update_app_settings,
    list_threads as ui_list_threads,
    create_thread as ui_create_thread,
    rename_thread as ui_rename_thread,
    archive_thread as ui_archive_thread,
    delete_thread as ui_delete_thread,
    toggle_sidebar_visibility,
    list_messages as ui_list_messages,
)
from typing import Literal


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

    settings = get_app_settings()
    with gr.Blocks(
        title="でもあぷり",
        head=f"""
  <link rel=\"icon\" href=\"{make_favicon_data_uri('🦜', size=64, circle_fill='#1f2937', ring_color='#fff', ring_width=2)}\" />
  <link rel=\"stylesheet\" href=\"/public/styles/app.css\" />
  <script src=\"/public/scripts/threads_ui.js\" defer></script>
  <style>
    .v-sep{{width:2px;height:calc(100vh - 180px);background:#9ca3af;margin:6px 8px;}}
    #sidebar-toggle-row button{{min-width:36px;}}
    #sidebar_toggle_btn{{margin-left:auto;}}
    .threads-list{{display:block}}
    .thread-link{{padding:8px 10px; cursor:pointer; border-radius:6px;}}
    .thread-link:hover{{background:#374151}}
    .thread-link.selected{{background:#1f2937; outline:1px solid #6b7280}}
    .thread-title{{display:block; text-align:left; color:#e5e7eb}}
    .ctx-menu{{position:fixed; z-index:9999; background:#111827; border:1px solid #374151; border-radius:8px; box-shadow:0 8px 16px rgba(0,0,0,.35);}}
    .ctx-item{{padding:8px 12px; color:#e5e7eb; cursor:pointer;}}
    .ctx-item:hover{{background:#374151}}
    .hidden-trigger{{display:none !important; visibility:hidden !important; width:0; height:0;}}
  </style>
""",
    ) as demo:
        gr.Markdown("### デモアプリ")

        # グローバル（全タブ共通）で利用する隠しトリガとスレッドID/アクション保持
        action_thread_id = gr.Textbox(value="", visible=True, elem_id="th_action_id", elem_classes=["hidden-trigger", "th_action_id"])  # type: ignore[arg-type]
        action_kind = gr.Textbox(value="", visible=True, elem_id="th_action_kind", elem_classes=["hidden-trigger", "th_action_kind"])  # type: ignore[arg-type]
        action_arg = gr.Textbox(value="", visible=True, elem_id="th_action_arg", elem_classes=["hidden-trigger", "th_action_arg"])  # type: ignore[arg-type]
        open_trigger = gr.Button(visible=True, elem_id="th_open_trigger", elem_classes=["hidden-trigger", "th_open_trigger"])  # type: ignore[arg-type]
        rename_trigger = gr.Button(visible=True, elem_id="th_rename_trigger", elem_classes=["hidden-trigger", "th_rename_trigger"])  # type: ignore[arg-type]
        share_trigger = gr.Button(visible=True, elem_id="th_share_trigger", elem_classes=["hidden-trigger", "th_share_trigger"])  # type: ignore[arg-type]
        delete_trigger = gr.Button(visible=True, elem_id="th_delete_trigger", elem_classes=["hidden-trigger", "th_delete_trigger"])  # type: ignore[arg-type]
        current_thread_id = gr.State("")

        with gr.Tabs():
            with gr.TabItem("チャット"):
                with gr.Row():
                    # 左サイドバー（スレッド一覧、設定で表示切替）
                    sidebar_col = gr.Column(scale=1, min_width=260, visible=settings["show_thread_sidebar"])  # type: ignore[index]
                    with sidebar_col:
                        with gr.Row(elem_id="sidebar-toggle-row"):
                            new_btn = gr.Button("＋ 新規", scale=1)
                            toggle_btn_left = gr.Button("≡", scale=0, min_width=36, elem_id="sidebar_toggle_btn")
                        threads_state = gr.State([])
                        threads_html = gr.HTML("", elem_id="threads_list")

                    # サイドバー非表示時にだけ表示されるエッジトグル
                    edge_col = gr.Column(scale=0, min_width=24, visible=not bool(settings["show_thread_sidebar"]))  # type: ignore[index]
                    with edge_col:
                        toggle_btn_edge = gr.Button("≡", scale=0, min_width=24)

                    gr.HTML("<div class='v-sep'></div>", elem_id="vsep")

                    with gr.Column(scale=4):
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
                            inputs=[msg, chat, current_thread_id],
                            outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
                        )
                        stream_evt_enter = guard_evt_enter.then(
                            stream_llm,
                            inputs=[go_flag, prompt_st, chat, current_thread_id],
                            outputs=[chat, status, stop, send],
                        )

                        guard_evt_send = send.click(
                            guard_and_prep,
                            inputs=[msg, chat, current_thread_id],
                            outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
                        )
                        stream_evt_send = guard_evt_send.then(
                            stream_llm,
                            inputs=[go_flag, prompt_st, chat, current_thread_id],
                            outputs=[chat, status, stop, send],
                        )

                        stop.click(
                            stop_chat,
                            None,
                            [stop, send, status],
                            cancels=[stream_evt_enter, stream_evt_send],
                        )

                # サイドバーイベント
                def _build_threads_html(items: list[dict]) -> str:
                    def esc(s: str) -> str:
                        return (
                            s.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                        )
                    rows = []
                    for it in items:
                        title = esc(it.get("title") or "(新規)")
                        tid = esc(it.get("id") or "")
                        rows.append(f"<div class='thread-link' data-tid='{tid}'><span class='thread-title'>{title}</span></div>")
                    return f"<div class='threads-list'>{''.join(rows)}</div>"

                def _refresh_threads():
                    items = ui_list_threads()
                    html = _build_threads_html(items)
                    return gr.update(value=html), items

                def _on_new():
                    created = ui_create_thread(None)
                    items = ui_list_threads()
                    html = _build_threads_html(items)
                    tid = created.get('id') or ''
                    history = ui_list_messages(tid) if tid else []
                    return gr.update(value=html), items, tid, history

                _evt_new = new_btn.click(_on_new, None, [threads_html, threads_state, current_thread_id, chat])

                def _open_by_id(tid: str):
                    tid = (tid or "").strip()
                    history = ui_list_messages(tid) if tid else []
                    return tid, history

                def _dispatch_action_common(kind: str, tid: str, cur_tid: str, arg: str):
                    kind = (kind or "").strip()
                    tid = (tid or "").strip()
                    arg = (arg or "").strip()
                    # 既定の戻り値（current_thread_id, chat, threads_html）
                    def no_changes():
                        return cur_tid, gr.update(), gr.update()

                    if kind == "open" and tid:
                        new_tid, history = _open_by_id(tid)
                        return new_tid, history, gr.update()

                    if kind == "rename" and tid and arg:
                        from app.repositories.thread_repo import ThreadRepository
                        from app.db.session import db_session
                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.rename(tid, arg)
                        items = ui_list_threads()
                        html = _build_threads_html(items)
                        return cur_tid, gr.update(), gr.update(value=html)

                    if kind == "share" and tid:
                        gr.Info(f"共有: {tid}")
                        return no_changes()

                    if kind == "delete" and tid:
                        from app.repositories.thread_repo import ThreadRepository
                        from app.db.session import db_session
                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.archive(tid)
                        # 即時UI反映: 現行HTMLから対象項目を除去（再フェッチに依存せず反映）
                        def remove_item(html: str) -> str:
                            return html.replace(f"<div class='thread-link' data-tid='{tid}'", "<div class='thread-link removed' data-tid='REMOVED-" + tid + "'")
                        # サイドバー側は再フェッチで更新。
                        items = ui_list_threads()
                        html = _build_threads_html(items)
                        new_cur = cur_tid if cur_tid != tid else ""
                        new_history = [] if new_cur == "" else ui_list_messages(new_cur)
                        return new_cur, new_history, gr.update(value=html)

                    return no_changes()

                def _dispatch_action_chat(kind: str, tid: str, cur_tid: str, arg: str):
                    return _dispatch_action_common(kind, tid, cur_tid, arg)

                def _dispatch_action_both(kind: str, tid: str, cur_tid: str, arg: str):
                    new_cur, new_history, html = _dispatch_action_common(kind, tid, cur_tid, arg)
                    # サイドバーも更新したいが、このバインドはタブ内でのみ有効。サイドバー側は次回 reload で反映。
                    return new_cur, new_history, html, html

                def _toggle_sidebar_left():
                    s = toggle_sidebar_visibility()
                    return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

                def _toggle_sidebar_edge():
                    s = toggle_sidebar_visibility()
                    return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

                toggle_btn_left.click(_toggle_sidebar_left, None, [sidebar_col, edge_col])
                toggle_btn_edge.click(_toggle_sidebar_edge, None, [sidebar_col, edge_col])

                # 初期ロードで一覧を表示
                # JS初期化は外部ファイルで実施（/public/scripts/threads_ui.js）
                
                demo.load(_refresh_threads, None, [threads_html, threads_state])
                # open/rename/share/delete の隠しトリガ（常に存在・反応させる）
                def _ctx_rename(tid: str):
                    from app.ui.threads_ui import dummy_rename
                    dummy_rename(tid)
                    try:
                        gr.Info(f"名前変更(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                def _ctx_share(tid: str):
                    from app.ui.threads_ui import dummy_share
                    dummy_share(tid)
                    try:
                        gr.Info(f"共有(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                def _ctx_delete(tid: str):
                    from app.ui.threads_ui import dummy_delete
                    dummy_delete(tid)
                    try:
                        gr.Info(f"削除(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                open_trigger.click(lambda tid: _open_by_id(tid), [action_thread_id], [current_thread_id, chat])
                rename_trigger.click(_ctx_rename, [action_thread_id], None)
                share_trigger.click(_ctx_share, [action_thread_id], None)
                delete_trigger.click(_ctx_delete, [action_thread_id], None)
                # ここではバインドしない（threads_html_tab 定義後に1本化してバインド）
                demo.load(lambda: None, None, None, js="()=>{ try { if (window.threadsSetup) { window.threadsSetup(); } } catch(e) { try{console.error('[threads-ui] init error', e);}catch(_){} } }")

            threads_tab = gr.TabItem("スレッド", visible=settings["show_threads_tab"])  # type: ignore[index]
            with threads_tab:
                # サイドバーと同様の縦並び
                threads_state2 = gr.State([])
                threads_html_tab = gr.HTML("", elem_id="threads_list_tab")

                def _refresh_threads_tab():
                    items = ui_list_threads()
                    html = _build_threads_html(items)
                    return gr.update(value=html), items

                def _open_by_index_tab(items, idx: int):
                    if not items or idx >= len(items):
                        return "", []
                    tid = items[idx].get('id') or ''
                    history = ui_list_messages(tid) if tid else []
                    return tid, history

                demo.load(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

                # ここでのみ1本のバインド（kind変更）でディスパッチし、両方の一覧を更新（同一HTML）
                _evt_kind = action_kind.change(
                    _dispatch_action_both,
                    inputs=[action_kind, action_thread_id, current_thread_id, action_arg],
                    outputs=[current_thread_id, chat, threads_html, threads_html_tab],
                )
                # 念のため、rename/delete直後も確実にタブ側を再フェッチ
                _evt_kind.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])
                # サイドバーの「＋ 新規」後にタブ側の一覧も即更新
                _evt_new.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

                # サイドバーの「＋ 新規」後にタブ側の一覧も即更新
                _evt_new.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

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

                gr.Markdown("**表示設定**")
                display_mode = gr.Radio(
                    choices=["サイドバー", "タブ"],
                    value=("サイドバー" if settings["show_thread_sidebar"] else "タブ"),
                    label="スレッドの表示方法",
                )
                save_btn = gr.Button("保存")
                hint = gr.Markdown("")

                def _apply_settings(mode):
                    s = update_app_settings(
                        show_thread_sidebar=(mode == "サイドバー"),
                        show_threads_tab=(mode == "タブ"),
                    )
                    return (
                        gr.update(visible=s["show_thread_sidebar"]),
                        gr.update(visible=s["show_threads_tab"]),
                        "設定を保存しました。",
                    )

                save_btn.click(_apply_settings, [display_mode], [sidebar_col, threads_tab, hint])

        demo.queue(max_size=16, default_concurrency_limit=4)
    return demo


def create_api_app() -> FastAPI:
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

    # Ensure DB schema and seed data are prepared on startup
    bootstrap_schema_and_seed()

    api = FastAPI()
    api.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    @api.get("/manifest.json")
    def _manifest_file():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")

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

    # --- REST API (minimum) ---

    @api.get("/api/threads")
    def list_threads():
        with db_session() as s:
            repo = ThreadRepository(s)
            items = repo.list_recent(limit=100)
            return [
                {"id": t.id, "title": t.title, "archived": t.archived}
                for t in items
            ]

    @api.post("/api/threads", status_code=201)
    def create_thread(payload: dict):  # {title?: str}
        title = (payload.get("title") or "").strip() or None
        svc = ThreadService()
        created = svc.create_thread(title_hint=title)
        with db_session() as s:
            repo = ThreadRepository(s)
            t = repo.get(created.thread_id)
            return {"id": t.id, "title": t.title, "archived": t.archived}

    @api.get("/api/threads/{thread_id}/messages")
    def list_messages(thread_id: str):
        with db_session() as s:
            repo = ThreadRepository(s)
            t = repo.get(thread_id)
            if t is None:
                raise HTTPException(status_code=404, detail="thread not found")
            msgs = repo.list_messages(thread_id)
            return [{"role": m.role, "content": m.content} for m in msgs]

    @api.post("/api/threads/{thread_id}/messages", status_code=201)
    def add_message(thread_id: str, payload: dict):  # {role, content}
        role: str = payload.get("role")
        content: str = payload.get("content")
        if role not in ("user", "assistant", "system"):
            raise HTTPException(status_code=422, detail="invalid role")
        svc = ThreadService()
        if role == "user":
            svc.add_user_message(thread_id, content)
        else:
            svc.add_assistant_message(thread_id, content)
        return {"ok": True}

    @api.patch("/api/threads/{thread_id}")
    def update_thread(thread_id: str, payload: dict):  # {title?, archived?}
        with db_session() as s:
            repo = ThreadRepository(s)
            t = repo.get(thread_id)
            if t is None:
                raise HTTPException(status_code=404, detail="thread not found")
            if "title" in payload and payload["title"] is not None:
                repo.rename(thread_id, (payload["title"] or "").strip())
            if payload.get("archived") is True:
                repo.archive(thread_id)
            return {"id": t.id, "title": t.title, "archived": t.archived}

    @api.delete("/api/threads/{thread_id}", status_code=204)
    def delete_thread(thread_id: str):
        with db_session() as s:
            repo = ThreadRepository(s)
            ok = repo.delete(thread_id)
            if not ok:
                raise HTTPException(status_code=404, detail="thread not found")
            return None

    @api.get("/api/settings/app")
    def get_settings():
        svc = SettingsService()
        s = svc.get()
        return {
            "show_thread_sidebar": s.show_thread_sidebar,
            "show_threads_tab": s.show_threads_tab,
        }

    @api.patch("/api/settings/app")
    def patch_settings(payload: dict):  # {show_thread_sidebar?, show_threads_tab?}
        svc = SettingsService()
        s = svc.update(
            show_thread_sidebar=payload.get("show_thread_sidebar"),
            show_threads_tab=payload.get("show_threads_tab"),
        )
        return {
            "show_thread_sidebar": s.show_thread_sidebar,
            "show_threads_tab": s.show_threads_tab,
        }

    return api


def create_app() -> FastAPI:
    api = create_api_app()
    demo = create_blocks()
    gr.mount_gradio_app(api, demo, path="/gradio")
    return api


