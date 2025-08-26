from __future__ import annotations

import itertools

import gradio as gr

from app.features.chat import guard_and_prep, stream_llm, stop_chat, llm_stream


def test_guard_and_prep_empty_and_nonempty():
    # Empty input returns no-op updates
    out = guard_and_prep(" ", [])
    assert out[-2] is False  # go_flag

    # Non-empty input appends user + assistant placeholder
    hist, status, *_ = guard_and_prep("hello", [])
    assert hist[-2]["role"] == "user"
    assert hist[-1]["role"] == "assistant"
    assert "typing" in hist[-1]["content"]
    assert "生成中" in status


def test_stream_llm_branches():
    # go=False branch
    gen = stream_llm(False, "", [])
    first = next(gen)
    assert isinstance(first, tuple)

    # token stream branch (limit to first 3 tokens for speed)
    gen = stream_llm(True, "short", [{"role": "assistant", "content": ""}])
    for _ in itertools.islice(gen, 3):
        pass


def test_llm_stream_direct_sampling():
    # Consume a few tokens directly to cover generator body
    g = llm_stream("x")
    next(g)
    next(g)


def test_stop_chat():
    s = stop_chat()
    assert len(s) == 3
