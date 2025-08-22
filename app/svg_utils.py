"""SVG および favicon 関連ユーティリティ。

挙動は元の `app/demo.py` と同一となるよう、ロジック・デフォルト値を厳密に維持する。
"""

from __future__ import annotations

import os
import urllib.parse


def write_emoji_svg(
    emoji: str,
    dest_path: str,
    size: int = 128,
    bg: str | None = "#FFFFFF",
    pad: int = 0,
    emoji_scale: float = 0.90,
    dy_em: float = 0.00,
) -> str:
    """与えられた絵文字から円形背景付き SVG を生成して保存する。

    元の実装と同じ引数とデフォルト値を維持する。
    """
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


def make_favicon_data_uri(
    emoji: str = "💻",
    size: int = 64,
    circle_fill: str = "#111827",
    ring_color: str = "#ffffff",
    ring_width: int = 2,
    emoji_scale: float = 0.80,
    dy_em: float = 0.00,
) -> str:
    """小さな SVG favicon を data URI として構築して返す。"""
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
    """favicon 用の SVG 文字列を生成して返す。"""
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


