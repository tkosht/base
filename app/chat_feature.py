"""チャット機能のロジック集約。

`app/demo.py` から挙動を変更せず移設。
"""

from __future__ import annotations

import time
import gradio as gr
from app.services.thread_service import ThreadService


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


def guard_and_prep(message: str, history, thread_id: str = ""):
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
    user_msg = {"role": "user", "content": text}
    assistant_placeholder = {"role": "assistant", "content": "⌛ typing..."}
    history = history + [user_msg, assistant_placeholder]
    # persist user message if thread selected
    if thread_id:
        try:
            ThreadService().add_user_message(thread_id, text)
        except Exception:
            pass
    return (
        history,
        "⌛ 回答生成中...",
        gr.update(visible=True, interactive=True),
        gr.update(visible=False),
        "",
        True,
        text,
    )


def stream_llm(go: bool, prompt: str, history, thread_id: str = ""):
    if not go:
        yield gr.update(), gr.update(), gr.update(), gr.update()
        return
    history = history or []
    body = ""
    for tok in llm_stream(prompt):
        body += tok
        if history and history[-1].get("role") == "assistant":
            history[-1]["content"] = body
        yield history, "⌛ 回答生成中...", gr.update(
            visible=True, interactive=True
        ), gr.update(visible=False)
    # persist assistant final content
    if thread_id and body:
        try:
            ThreadService().add_assistant_message(thread_id, body)
        except Exception:
            pass
    yield history, "回答生成完了", gr.update(
        visible=False, interactive=False
    ), gr.update(visible=True)


def stop_chat():
    return (
        gr.update(visible=False, interactive=False),
        gr.update(visible=True),
        "実行中の処理を停止しました。",
    )


