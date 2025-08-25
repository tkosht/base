"""検索機能（ダミー）ロジックの集約（移設）。

`app/search_feature.py` から挙動を変更せずに移設。
"""

from __future__ import annotations

import gradio as gr


def _search_users(query: str, top: int = 30) -> list[str]:
    if not query:
        return []
    q = query.lower()
    hits: list[str] = []
    for i in range(1, 400):
        mail = f"test{i}@test.com"
        label = f"テスト{i}({mail})"
        if q in label.lower() or q in mail.lower():
            hits.append(label)
        if len(hits) >= top:
            break
    return hits


def chips_html(values):
    vals = values or []
    return (
        "<div class='chips'>"
        + "".join(f"<span class='chip'>{v}</span>" for v in vals)
        + "</div>"
    )


def neutralize_email(s: str) -> str:
    ZWSP = "\u200b"
    return s.replace("@", f"{ZWSP}@{ZWSP}")


def suggest(q, current_dropdown_value, selected_state):
    q = (q or "").strip()
    if len(q) < 2:
        merged = sorted(set(selected_state or []))
        return (
            gr.update(choices=merged, value=current_dropdown_value),
            "2文字以上で検索してください。",
        )
    hits = _search_users(q)
    merged = sorted(set(hits) | set(selected_state or []))
    hint = (
        f"{len(hits)}件ヒット｜候補例: "
        + ", ".join(neutralize_email(h) for h in hits[:3])
        + (" …" if len(hits) > 3 else "")
    )
    return gr.update(choices=merged, value=current_dropdown_value), hint


def on_change(new_value, _state):
    vals = sorted(set(new_value or []))
    return vals, chips_html(vals)
