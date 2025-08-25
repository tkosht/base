from __future__ import annotations

from app.utils.svg import make_favicon_data_uri


def build_head_html(
    *,
    emoji: str = "🦜",
    size: int = 64,
    circle_fill: str = "#1f2937",
    ring_color: str = "#fff",
    ring_width: int = 2,
) -> str:
    """Return <head> injection HTML for Gradio Blocks.

    Note: Keeps behavior identical to previous inline definition in app_factory.
    """
    favicon = make_favicon_data_uri(
        emoji,
        size=size,
        circle_fill=circle_fill,
        ring_color=ring_color,
        ring_width=ring_width,
    )
    return (
        f"\n  <link rel=\"icon\" href=\"{favicon}\" />\n"
        "  <style id=\"app_css_import\">@import url('/public/styles/app.css');</style>\n"
        "  <script src=\"/public/scripts/threads_ui.js\" defer></script>\n"
        "  <script src=\"/public/scripts/theme_bridge.js\" defer></script>\n"
        "  <link rel=\"stylesheet\" href=\"/public/styles/app.css\" />\n"
    )


