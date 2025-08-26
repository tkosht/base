from __future__ import annotations

import gradio as gr

from app.features.search import (
    chips_html,
    neutralize_email,
    on_change,
    suggest,
)
from app.services.settings_service import SettingsService
from app.ui.avatars import prepare_avatars
from app.ui.head import build_head_html
from app.ui.html.threads_html import build_threads_html
from app.ui.tabs.threads_tab import setup_threads_tab
from app.ui.threads_ui import (
    create_thread as ui_create_thread,
    list_messages as ui_list_messages,
    list_threads as ui_list_threads,
    toggle_sidebar_visibility,
)

DEFAULT_STATUS_TEXT = "準備OK! いつでもチャットを開始できます。"


def create_blocks() -> gr.Blocks:
    USER_AVATAR_PATH, BOT_AVATAR_PATH = prepare_avatars()
    settings = SettingsService().get()
    with gr.Blocks(title="でもあぷり", head=build_head_html()) as demo:
        gr.Markdown("### デモアプリ")

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
                    sidebar_col = gr.Column(scale=1, min_width=260, visible=settings.show_thread_sidebar, elem_id="sidebar_col")  # type: ignore[index]
                    with sidebar_col:
                        with gr.Row(elem_id="sidebar-toggle-row"):
                            new_btn = gr.Button(
                                "＋ 新規", scale=1, elem_id="new_btn_main"
                            )
                            toggle_btn_left = gr.Button(
                                "≡",
                                scale=0,
                                min_width=36,
                                elem_id="sidebar_toggle_btn",
                            )
                        threads_state = gr.State([])
                        threads_html = gr.HTML("", elem_id="threads_list")

                    edge_col = gr.Column(scale=0, min_width=24, visible=not settings.show_thread_sidebar, elem_id="edge_col")  # type: ignore[index]
                    with edge_col:
                        toggle_btn_edge = gr.Button("≡", scale=0, min_width=24)
                        new_btn_edge = gr.Button(
                            "＋", scale=0, min_width=24, elem_id="new_btn_edge"
                        )
                    gr.HTML("<div class='v-sep'></div>", elem_id="vsep")

                    with gr.Column(scale=4):
                        chat = gr.Chatbot(
                            height=580,
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
                                "⏹",
                                elem_id="stopbtn",
                                visible=False,
                                interactive=False,
                            )
                            send = gr.Button(
                                "↑", elem_id="sendbtn", visible=True
                            )

                        status = gr.Markdown(
                            DEFAULT_STATUS_TEXT, elem_id="status"
                        )

                        go_flag = gr.State(False)
                        prompt_st = gr.State("")

                        from app.ui.tabs.chat_tab import (
                            setup_chat_tab as _setup_chat,
                        )

                        chat_hooks = _setup_chat(
                            settings=settings,
                            sidebar_col=sidebar_col,
                            edge_col=edge_col,
                            new_btn=new_btn,
                            toggle_btn_left=toggle_btn_left,
                            toggle_btn_edge=toggle_btn_edge,
                            threads_state=threads_state,
                            threads_html=threads_html,
                            current_thread_id=current_thread_id,
                            chat=chat,
                            msg=msg,
                            stop=stop,
                            send=send,
                            status=status,
                            go_flag=go_flag,
                            prompt_st=prompt_st,
                            ui_create_thread=ui_create_thread,
                            ui_list_threads=ui_list_threads,
                            ui_list_messages=ui_list_messages,
                            build_threads_html=build_threads_html,
                            toggle_sidebar_visibility=toggle_sidebar_visibility,
                        )

                def _refresh_threads(selected_tid: str = ""):
                    items = ui_list_threads()
                    html = build_threads_html(items, selected_tid)
                    return gr.update(value=html), items

                def _on_new():
                    items = ui_list_threads()
                    html = build_threads_html(items, "")
                    return gr.update(value=html), items, "", []

                _evt_new = chat_hooks["evt_new"]

                def _open_by_id(tid: str):
                    tid = (tid or "").strip()
                    history = ui_list_messages(tid) if tid else []
                    return tid, history

                def _dispatch_action_common(
                    kind: str, tid: str, cur_tid: str, arg: str
                ):
                    kind = (kind or "").strip()
                    tid = (tid or "").strip()
                    arg = (arg or "").strip()

                    def no_changes():
                        return cur_tid, gr.update(), gr.update()

                    if kind == "open" and tid:
                        new_tid, history = _open_by_id(tid)
                        return new_tid, history, gr.update()

                    if kind == "rename" and tid and arg:
                        from app.db.session import db_session
                        from app.repositories.thread_repo import (
                            ThreadRepository,
                        )

                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.rename(tid, arg)
                        items = ui_list_threads()
                        html = build_threads_html(items, cur_tid)
                        return cur_tid, gr.update(), gr.update(value=html)

                    if kind == "share" and tid:
                        try:
                            gr.Info("共有は現在未対応です。後日提供予定です。")
                        except Exception:
                            pass
                        return no_changes()

                    if kind == "owner" and tid:
                        try:
                            gr.Info(
                                "オーナー変更は現在未対応です。後日提供予定です。"
                            )
                        except Exception:
                            pass
                        return no_changes()

                    if kind == "delete" and tid:
                        from app.db.session import db_session
                        from app.repositories.thread_repo import (
                            ThreadRepository,
                        )

                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.archive(tid)
                        items = ui_list_threads()
                        new_cur = cur_tid if cur_tid != tid else ""
                        html = build_threads_html(items, new_cur)
                        new_history = (
                            [] if new_cur == "" else ui_list_messages(new_cur)
                        )
                        return new_cur, new_history, gr.update(value=html)

                    return no_changes()

                def _dispatch_action_chat(
                    kind: str, tid: str, cur_tid: str, arg: str
                ):
                    return _dispatch_action_common(kind, tid, cur_tid, arg)

                def _dispatch_action_both(
                    kind: str, tid: str, cur_tid: str, arg: str
                ):
                    new_cur, new_history, html = _dispatch_action_common(
                        kind, tid, cur_tid, arg
                    )
                    return new_cur, new_history, html, html

                # Sidebar toggle handlers are wired in chat_tab; avoid double-binding here (DRY)

                demo.load(
                    _refresh_threads,
                    [current_thread_id],
                    [threads_html, threads_state],
                )

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

                def _open_and_mark(tid: str):
                    new_tid, history = _open_by_id(tid)
                    items = ui_list_threads()
                    html = build_threads_html(items, new_tid)
                    return new_tid, history, gr.update(value=html)

                open_trigger.click(
                    _open_and_mark,
                    [action_thread_id],
                    [current_thread_id, chat, threads_html],
                )
                rename_trigger.click(_ctx_rename, [action_thread_id], None)
                share_trigger.click(_ctx_share, [action_thread_id], None)
                delete_trigger.click(_ctx_delete, [action_thread_id], None)
                demo.load(
                    lambda: None,
                    None,
                    None,
                    js="()=>{ try { if (window.threadsSetup) { window.threadsSetup(); } } catch(e) { try{console.error('[threads-ui] init error', e);}catch(_){} } }",
                )

            threads_tab = gr.TabItem("スレッド")  # type: ignore[index]
            with threads_tab:
                threads_state2 = gr.State([])
                threads_html_tab = gr.HTML("", elem_id="threads_list_tab")

                setup_threads_tab(
                    demo=demo,
                    current_thread_id=current_thread_id,
                    action_kind=action_kind,
                    action_thread_id=action_thread_id,
                    action_arg=action_arg,
                    chat=chat,
                    threads_html=threads_html,
                    evt_new=_evt_new,
                    threads_state=threads_state,
                    ui_list_threads=ui_list_threads,
                    ui_list_messages=ui_list_messages,
                    dispatch_action_both=_dispatch_action_both,
                    threads_html_tab=threads_html_tab,
                    threads_state2=threads_state2,
                    new_btn_edge=new_btn_edge,
                    on_new=_on_new,
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

                saved_state = gr.State(selected_state.value)
                save_btn = gr.Button("保存")
                save_hint = gr.Markdown("")

                from app.ui.tabs.settings_tab import setup_settings_tab

                setup_settings_tab(
                    search_box=search_box,
                    search_btn=search_btn,
                    combo=combo,
                    hit_info=hit_info,
                    chips=chips,
                    selected_state=selected_state,
                    saved_state=saved_state,
                    save_btn=save_btn,
                    save_hint=save_hint,
                    suggest=suggest,
                    on_change=on_change,
                    neutralize_email=neutralize_email,
                )

        demo.queue(max_size=16, default_concurrency_limit=4)
    return demo
