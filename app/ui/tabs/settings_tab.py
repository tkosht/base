from __future__ import annotations

import gradio as gr


def setup_settings_tab(
    *,
    search_box: gr.Textbox,
    search_btn: gr.Button,
    combo: gr.Dropdown,
    hit_info: gr.Markdown,
    chips: gr.HTML,
    selected_state: gr.State,
    saved_state: gr.State,
    save_btn: gr.Button,
    save_hint: gr.Markdown,
    suggest,
    on_change,
    neutralize_email,
):
    search_box.submit(
        suggest, [search_box, combo, selected_state], [combo, hit_info]
    )
    search_btn.click(
        suggest, [search_box, combo, selected_state], [combo, hit_info]
    )

    combo.change(on_change, [combo, selected_state], [selected_state, chips])

    def _save_selected(current_list, previous_list):
        cur = [str(x) for x in (current_list or [])]
        prev = [str(x) for x in (previous_list or [])]
        added = [x for x in cur if x not in prev]
        removed = [x for x in prev if x not in cur]
        added_cnt = len(added)
        removed_cnt = len(removed)
        added_part = "｜追加 %d 件" % added_cnt + (
            ": " + ", ".join(neutralize_email(x) for x in added)
            if added_cnt
            else ""
        )
        removed_part = "｜削除 %d 件" % removed_cnt + (
            ": " + ", ".join(neutralize_email(x) for x in removed)
            if removed_cnt
            else ""
        )
        summary = "保存しました" + added_part + removed_part
        try:
            gr.Info(summary)
        except Exception:
            pass
        return cur, summary

    save_btn.click(
        _save_selected, [selected_state, saved_state], [saved_state, save_hint]
    )

    return {
        "save_handler": _save_selected,
    }
