from __future__ import annotations


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_threads_html(items: list[dict], selected_tid: str = "") -> str:
    rows: list[str] = []
    for it in items:
        title = _esc(it.get("title") or "(新規)")
        tid = _esc(it.get("id") or "")
        has_msgs = bool(it.get("has_messages"))
        disabled = " data-empty='1'" if not has_msgs else ""
        sel_cls = " selected" if selected_tid and (tid == _esc(selected_tid)) else ""
        rows.append(
            f"<div class='thread-link{sel_cls}' data-tid='{tid}'{disabled}><span class='thread-title'>{title}</span></div>"
        )
    sel_attr = f" data-selected='{_esc(selected_tid)}'" if selected_tid else ""
    return f"<div class='threads-list'{sel_attr}>{''.join(rows)}</div>"


def build_threads_html_tab(items: list[dict], selected_tid: str = "") -> str:
    def btn(act: str, tid: str, label: str) -> str:
        return f"<button class='thread-btn' data-act='{_esc(act)}' data-tid='{_esc(tid)}'>{_esc(label)}</button>"

    rows: list[str] = []
    for it in items:
        tid = _esc(it.get("id") or "")
        title = _esc(it.get("title") or "(新規)")
        summary = _esc(it.get("summary") or "")
        has_msgs = bool(it.get("has_messages"))
        actions = (
            (btn("rename", tid, "名前変更") if has_msgs else "")
            + (btn("share", tid, "共有") if has_msgs else "")
            + (btn("owner", tid, "オーナー変更") if has_msgs else "")
            + btn("delete", tid, "削除")
        )
        sel_cls = " selected" if selected_tid and (tid == _esc(selected_tid)) else ""
        row_html = (
            "<div class='thread-link" + sel_cls + "' data-tid='" + tid + "'" + (" data-empty='1'" if not has_msgs else "") + ">"
            + "<div class='thread-row'>"
            + "<div class='thread-main'>"
            + f"<span class='thread-title'>{title}</span>"
            + (f"<span class='thread-summary'>{summary}</span>" if summary else "")
            + "</div>"
            + f"<div class='thread-actions'>{actions}</div>"
            + "</div>"
            + "</div>"
        )
        rows.append(row_html)
    sel_attr = f" data-selected='{_esc(selected_tid)}'" if selected_tid else ""
    return f"<div class='threads-list'{sel_attr}>{''.join(rows)}</div>"


