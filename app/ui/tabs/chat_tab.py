from __future__ import annotations

import time
import gradio as gr

from app.features.chat import guard_and_prep, stream_llm, stop_chat
from app.services.title_service import TitleService


def setup_chat_tab(
    *,
    settings,
    sidebar_col: gr.Column,
    edge_col: gr.Column,
    new_btn: gr.Button,
    toggle_btn_left: gr.Button,
    toggle_btn_edge: gr.Button,
    threads_state: gr.State,
    threads_html: gr.HTML,
    current_thread_id: gr.State,
    chat: gr.Chatbot,
    msg: gr.Textbox,
    stop: gr.Button,
    send: gr.Button,
    status: gr.Markdown,
    go_flag: gr.State,
    prompt_st: gr.State,
    ui_create_thread,
    ui_list_threads,
    ui_list_messages,
    build_threads_html,
    toggle_sidebar_visibility,
):
    def _ensure_thread_on_message(message_text: str, cur_tid: str):
        text = (message_text or "").strip()
        tid = (cur_tid or "").strip()
        if tid or not text:
            return tid
        created = ui_create_thread(None)
        return created.get("id") or ""

    pre_enter = msg.submit(
        _ensure_thread_on_message,
        inputs=[msg, current_thread_id],
        outputs=[current_thread_id],
    )
    guard_evt_enter = pre_enter.then(
        guard_and_prep,
        inputs=[msg, chat, current_thread_id],
        outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
    )

    def _maybe_rename_title_and_refresh(prompt_text: str, tid: str):
        tid = (tid or "").strip()
        from app.db.session import db_session
        from app.repositories.thread_repo import ThreadRepository

        if tid:
            with db_session() as s:
                repo = ThreadRepository(s)
                msgs = repo.list_messages(tid, limit=2)
                if len(msgs) == 1 and msgs[0].role == "user":
                    title = TitleService().suggest_title_via_llm(prompt_text)
                    repo.rename(tid, title)
        items = ui_list_threads()
        html = build_threads_html(items, tid)
        return gr.update(value=html)

    rename_evt_enter = guard_evt_enter.then(
        _maybe_rename_title_and_refresh,
        inputs=[prompt_st, current_thread_id],
        outputs=[threads_html],
    )
    stream_evt_enter = rename_evt_enter.then(
        stream_llm,
        inputs=[go_flag, prompt_st, chat, current_thread_id],
        outputs=[chat, status, stop, send],
    )

    def _reset_status_after_delay():
        time.sleep(3)
        return "準備OK! いつでもチャットを開始できます。"

    stream_evt_enter.then(
        _reset_status_after_delay,
        None,
        [status],
    )

    pre_send = send.click(
        _ensure_thread_on_message,
        inputs=[msg, current_thread_id],
        outputs=[current_thread_id],
    )
    guard_evt_send = pre_send.then(
        guard_and_prep,
        inputs=[msg, chat, current_thread_id],
        outputs=[chat, status, stop, send, msg, go_flag, prompt_st],
    )
    rename_evt_send = guard_evt_send.then(
        _maybe_rename_title_and_refresh,
        inputs=[prompt_st, current_thread_id],
        outputs=[threads_html],
    )
    stream_evt_send = rename_evt_send.then(
        stream_llm,
        inputs=[go_flag, prompt_st, chat, current_thread_id],
        outputs=[chat, status, stop, send],
    )
    stream_evt_send.then(
        _reset_status_after_delay,
        None,
        [status],
    )

    stop.click(
        stop_chat,
        None,
        [stop, send, status],
        cancels=[stream_evt_enter, stream_evt_send],
    )

    def _toggle_sidebar_left():
        s = toggle_sidebar_visibility()
        return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

    def _toggle_sidebar_edge():
        s = toggle_sidebar_visibility()
        return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

    toggle_btn_left.click(_toggle_sidebar_left, None, [sidebar_col, edge_col])
    toggle_btn_edge.click(_toggle_sidebar_edge, None, [sidebar_col, edge_col])

    def _refresh_threads(selected_tid: str = ""):
        items = ui_list_threads()
        html = build_threads_html(items, selected_tid)
        return gr.update(value=html), items

    def _on_new():
        items = ui_list_threads()
        html = build_threads_html(items, "")
        return gr.update(value=html), items, "", []

    evt_new = new_btn.click(
        _on_new, None, [threads_html, threads_state, current_thread_id, chat]
    )
    evt_new.then(
        lambda: None,
        None,
        None,
        js="()=>{ try { if (window.clearSelection) window.clearSelection(); } catch(_){} }",
    )

    return {
        "refresh_threads": _refresh_threads,
        "on_new": _on_new,
        "evt_new": evt_new,
    }
