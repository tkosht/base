from __future__ import annotations

from pathlib import Path

from app.features.search import _search_users, chips_html, neutralize_email, suggest, on_change
from app.utils.svg import build_favicon_svg, make_favicon_data_uri, write_emoji_svg
import gradio as gr


def test_search_and_suggest_and_on_change(tmp_path):
    # _search_users basic
    hits = _search_users("test1")
    assert any("テスト1(" in h for h in hits)

    # suggest requires 2+ chars
    # コンポーネント生成を避け、辞書形式のUpdateを検証
    update, hint = suggest("a", {"choices": [], "value": []}, [])
    assert "2文字以上" in hint

    update, hint = suggest("te", {"choices": [], "value": []}, [])
    assert isinstance(update, dict) and "choices" in update

    vals, chips = on_change(["a", "b", "a"], [])
    assert vals == ["a", "b"]
    assert "chips" in chips


def test_svg_utils(tmp_path):
    # build + data uri
    svg = build_favicon_svg("🦜")
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    data_uri = make_favicon_data_uri("🦜")
    assert data_uri.startswith("data:image/svg+xml;utf8,")

    # write file
    dest = Path(tmp_path) / "x.svg"
    p = write_emoji_svg("🙂", str(dest))
    assert Path(p).exists()


