from __future__ import annotations

import gradio as gr
from app.ui.html.threads_html import build_threads_html_tab


def setup_threads_tab(
    *,
    demo: gr.Blocks,
    current_thread_id: gr.State,
    action_kind: gr.Textbox,
    action_thread_id: gr.Textbox,
    action_arg: gr.Textbox,
    chat: gr.Chatbot,
    threads_html: gr.HTML,
    evt_new,
    threads_state: gr.State,
    ui_list_threads,
    ui_list_messages,
    dispatch_action_both,
    threads_html_tab: gr.HTML,
    threads_state2: gr.State,
    new_btn_edge: gr.Button | None = None,
    on_new=None,
):
    def _refresh_threads_tab(selected_tid: str = ""):
        items = ui_list_threads()
        html = build_threads_html_tab(items, selected_tid)
        return gr.update(value=html), items

    def _open_by_index_tab(items, idx: int):
        if not items or idx >= len(items):
            return "", []
        tid = items[idx].get("id") or ""
        history = ui_list_messages(tid) if tid else []
        return tid, history

    demo.load(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])

    _evt_kind = action_kind.change(
        dispatch_action_both,
        inputs=[action_kind, action_thread_id, current_thread_id, action_arg],
        outputs=[current_thread_id, chat, threads_html, threads_html_tab],
    )
    _evt_kind.then(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
    threads_html.change(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
    evt_new.then(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
    evt_new.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

    if new_btn_edge is not None:
        try:
            # 新規作成の処理をサイドバー開時と同一シーケンスで実行
            if on_new is not None:
                edge_new = new_btn_edge.click(on_new, None, [threads_html, threads_state, current_thread_id, chat])
                # 選択状態の即時解除（スレッドタブ/サイドバーの両方を対象）
                edge_new.then(
                    lambda: None,
                    None,
                    None,
                    js="()=>{ try {\n                      const sels=['#threads_list','#threads_list_tab'];\n                      for (const id of sels) {\n                        const root = (window.qsDeep?window.qsDeep(id):document.querySelector(id));\n                        if (!root) continue;\n                        const cont = (window.qsWithin?window.qsWithin(root,'.threads-list'):root.querySelector('.threads-list'));\n                        if (cont && cont.removeAttribute) cont.removeAttribute('data-selected');\n                        try { root.querySelectorAll('.thread-link.selected').forEach(el=>el.classList.remove('selected')); } catch(e){}\n                      }\n                      if (window.clearSelection) window.clearSelection();\n                    } catch(_){} }",
                )
                # タブ側の一覧をリフレッシュ
                edge_new.then(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
            else:
                new_btn_edge.click(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
        except Exception:
            pass


