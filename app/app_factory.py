"""FastAPI + Gradio のアプリ組み立て。

`app/demo.py` の組立ロジックを移設し、公開 API として `create_app()` を提供する。
挙動は変更しない（ルート、マニフェスト、favicon、/gradio マウント等）。
"""

from __future__ import annotations

from pathlib import Path
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import gradio as gr

from app.ui.head import build_head_html
from app.ui.avatars import prepare_avatars
from app.features.chat import guard_and_prep, stream_llm, stop_chat
from app.features.search import suggest, on_change, chips_html, neutralize_email
from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import db_session
from app.repositories.thread_repo import ThreadRepository
from app.services.thread_service import ThreadService
from app.services.settings_service import SettingsService
from app.services.title_service import TitleService
from app.ui.threads_ui import (
    list_threads as ui_list_threads,
    create_thread as ui_create_thread,
    rename_thread as ui_rename_thread,
    archive_thread as ui_archive_thread,
    delete_thread as ui_delete_thread,
    toggle_sidebar_visibility,
    list_messages as ui_list_messages,
)
from typing import Literal
from fastapi import APIRouter
from app.web.assets import ensure_public_assets, mount_public_and_routes
from app.web.routers.threads import router as threads_router
from app.web.routers.settings import router as settings_router
from app.web.assets import ensure_public_assets, mount_public_and_routes
from app.ui.html.threads_html import build_threads_html, build_threads_html_tab


DEFAULT_STATUS_TEXT = "準備OK! いつでもチャットを開始できます。"


def create_blocks() -> gr.Blocks:
    USER_AVATAR_PATH, BOT_AVATAR_PATH = prepare_avatars()

    settings = SettingsService().get()
    with gr.Blocks(title="でもあぷり", head=build_head_html()) as demo:
        gr.Markdown("### デモアプリ")

        # グローバル（全タブ共通）で利用する隠しトリガとスレッドID/アクション保持
        action_thread_id = gr.Textbox(value="", visible=True, elem_id="th_action_id", elem_classes=["hidden-trigger", "th_action_id"])  # type: ignore[arg-type]
        action_kind = gr.Textbox(value="", visible=True, elem_id="th_action_kind", elem_classes=["hidden-trigger", "th_action_kind"])  # type: ignore[arg-type]
        action_arg = gr.Textbox(value="", visible=True, elem_id="th_action_arg", elem_classes=["hidden-trigger", "th_action_arg"])  # type: ignore[arg-type]
        open_trigger = gr.Button(visible=True, elem_id="th_open_trigger", elem_classes=["hidden-trigger", "th_open_trigger"])  # type: ignore[arg-type]
        rename_trigger = gr.Button(visible=True, elem_id="th_rename_trigger", elem_classes=["hidden-trigger", "th_rename_trigger"])  # type: ignore[arg-type]
        share_trigger = gr.Button(visible=True, elem_id="th_share_trigger", elem_classes=["hidden-trigger", "th_share_trigger"])  # type: ignore[arg-type]
        delete_trigger = gr.Button(visible=True, elem_id="th_delete_trigger", elem_classes=["hidden-trigger", "th_delete_trigger"])  # type: ignore[arg-type]
        current_thread_id = gr.State("")

        with gr.Tabs():
            with gr.TabItem("チャット"):
                with gr.Row():
                    # 左サイドバー（スレッド一覧）
                    sidebar_col = gr.Column(scale=1, min_width=260, visible=settings.show_thread_sidebar, elem_id="sidebar_col")  # type: ignore[index]
                    with sidebar_col:
                        with gr.Row(elem_id="sidebar-toggle-row"):
                            new_btn = gr.Button("＋ 新規", scale=1, elem_id="new_btn_main")
                            toggle_btn_left = gr.Button("≡", scale=0, min_width=36, elem_id="sidebar_toggle_btn")
                        threads_state = gr.State([])
                        threads_html = gr.HTML("", elem_id="threads_list")

                    # サイドバー非表示時にだけ表示されるエッジトグル
                    edge_col = gr.Column(scale=0, min_width=24, visible=not settings.show_thread_sidebar, elem_id="edge_col")  # type: ignore[index]
                    with edge_col:
                        toggle_btn_edge = gr.Button("≡", scale=0, min_width=24)
                        new_btn_edge = gr.Button("＋", scale=0, min_width=24, elem_id="new_btn_edge")

                    gr.HTML("<div class='v-sep'></div>", elem_id="vsep")

                    with gr.Column(scale=4):
                        chat = gr.Chatbot(
                            height=580,
                            avatar_images=(USER_AVATAR_PATH, BOT_AVATAR_PATH),
                            label="Bot",
                            type="messages",
                        )

                        gr.Markdown("**User**")
                        with gr.Group(elem_id="msgrow"):
                            msg = gr.Textbox(
                                placeholder="Markdownで入力できます（**太字**、`code` など）",
                                show_label=False,
                                lines=1,
                            )
                            stop = gr.Button(
                                "⏹", elem_id="stopbtn", visible=False, interactive=False
                            )
                            send = gr.Button("↑", elem_id="sendbtn", visible=True)

                        status = gr.Markdown(
                            DEFAULT_STATUS_TEXT, elem_id="status"
                        )

                        go_flag = gr.State(False)
                        prompt_st = gr.State("")

                        # 初回メッセージ時のみスレッドを作成（＋新規でも同様の挙動）
                        def _ensure_thread_on_message(message_text: str, cur_tid: str):
                            text = (message_text or "").strip()
                            tid = (cur_tid or "").strip()
                            if tid or not text:
                                return tid
                            created = ui_create_thread(None)
                            return created.get('id') or ''

                        # 多重バインド防止: 既存ハンドラがあれば一旦キャンセルするため、専用hiddenトリガでderegは不要（gradioの特性）。
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
                        # 初回メッセージ時の自動タイトルリネーム（軽量ヘューリスティック版）
                        def _maybe_rename_title(prompt_text: str, tid: str):
                            tid = (tid or "").strip()
                            if not tid:
                                return
                            from app.db.session import db_session
                            from app.repositories.thread_repo import ThreadRepository
                            with db_session() as s:
                                repo = ThreadRepository(s)
                                msgs = repo.list_messages(tid, limit=2)
                                # user 1件のみ（assistantレスが無い）= 初回とみなす
                                if len(msgs) == 1 and msgs[0].role == "user":
                                    title = TitleService().suggest_title_via_llm(prompt_text)
                                    repo.rename(tid, title)
                        def _maybe_rename_title_and_refresh(prompt_text: str, tid: str):
                            tid = (tid or "").strip()
                            from app.db.session import db_session
                            from app.repositories.thread_repo import ThreadRepository
                            renamed = False
                            if tid:
                                with db_session() as s:
                                    repo = ThreadRepository(s)
                                    msgs = repo.list_messages(tid, limit=2)
                                    if len(msgs) == 1 and msgs[0].role == "user":
                                        title = TitleService().suggest_title_via_llm(prompt_text)
                                        repo.rename(tid, title)
                                        renamed = True
                            # サイドバー一覧を常に再構築（軽量）。タブ側は後段で別途更新される。
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
                        # 回答生成完了の数秒後にステータスを初期表示へ戻す
                        def _reset_status_after_delay():
                            time.sleep(3)
                            return DEFAULT_STATUS_TEXT
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

                # サイドバーイベント
                # HTMLビルダー（純関数）呼び出しに置換

                def _refresh_threads(selected_tid: str = ""):
                    items = ui_list_threads()
                    html = build_threads_html(items, selected_tid)
                    return gr.update(value=html), items

                def _on_new():
                    # スレッドは作成しない。空チャットにリセットし、選択も解除。
                    items = ui_list_threads()
                    html = build_threads_html(items, "")
                    return gr.update(value=html), items, "", []

                _evt_new = new_btn.click(_on_new, None, [threads_html, threads_state, current_thread_id, chat])
                # JSで選択解除（視覚のみ DRY/YAGNI）
                _evt_new.then(lambda: None, None, None, js="()=>{ try { if (window.clearSelection) window.clearSelection(); } catch(_){} }")

                def _open_by_id(tid: str):
                    tid = (tid or "").strip()
                    history = ui_list_messages(tid) if tid else []
                    return tid, history

                def _dispatch_action_common(kind: str, tid: str, cur_tid: str, arg: str):
                    kind = (kind or "").strip()
                    tid = (tid or "").strip()
                    arg = (arg or "").strip()
                    # 既定の戻り値（current_thread_id, chat, threads_html）
                    def no_changes():
                        return cur_tid, gr.update(), gr.update()

                    if kind == "open" and tid:
                        new_tid, history = _open_by_id(tid)
                        return new_tid, history, gr.update()
                    # send 分岐はメッセージ送信直前に作成する方針へ移行したため不要

                    if kind == "rename" and tid and arg:
                        from app.repositories.thread_repo import ThreadRepository
                        from app.db.session import db_session
                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.rename(tid, arg)
                        items = ui_list_threads()
                        html = build_threads_html(items, cur_tid)
                        html_tab = build_threads_html_tab(items, cur_tid)
                        return cur_tid, gr.update(), gr.update(value=html)

                    if kind == "share" and tid:
                        try:
                            gr.Info("共有は現在未対応です。後日提供予定です。")
                        except Exception:
                            pass
                        return no_changes()

                    if kind == "owner" and tid:
                        try:
                            gr.Info("オーナー変更は現在未対応です。後日提供予定です。")
                        except Exception:
                            pass
                        return no_changes()

                    if kind == "delete" and tid:
                        from app.repositories.thread_repo import ThreadRepository
                        from app.db.session import db_session
                        with db_session() as s:
                            repo = ThreadRepository(s)
                            repo.archive(tid)
                        # 即時UI反映: 現行HTMLから対象項目を除去（再フェッチに依存せず反映）
                        def remove_item(html: str) -> str:
                            return html.replace(f"<div class='thread-link' data-tid='{tid}'", "<div class='thread-link removed' data-tid='REMOVED-" + tid + "'")
                        # サイドバー側は再フェッチで更新。
                        items = ui_list_threads()
                        new_cur = cur_tid if cur_tid != tid else ""
                        html = build_threads_html(items, new_cur)
                        new_cur = cur_tid if cur_tid != tid else ""
                        new_history = [] if new_cur == "" else ui_list_messages(new_cur)
                        return new_cur, new_history, gr.update(value=html)

                    return no_changes()

                def _dispatch_action_chat(kind: str, tid: str, cur_tid: str, arg: str):
                    return _dispatch_action_common(kind, tid, cur_tid, arg)

                def _dispatch_action_both(kind: str, tid: str, cur_tid: str, arg: str):
                    new_cur, new_history, html = _dispatch_action_common(kind, tid, cur_tid, arg)
                    # サイドバーも更新したいが、このバインドはタブ内でのみ有効。サイドバー側は次回 reload で反映。
                    return new_cur, new_history, html, html

                def _toggle_sidebar_left():
                    s = toggle_sidebar_visibility()
                    return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

                def _toggle_sidebar_edge():
                    s = toggle_sidebar_visibility()
                    return gr.update(visible=s["show_thread_sidebar"]), gr.update(visible=not s["show_thread_sidebar"])  # type: ignore[index]

                toggle_btn_left.click(_toggle_sidebar_left, None, [sidebar_col, edge_col])
                toggle_btn_edge.click(_toggle_sidebar_edge, None, [sidebar_col, edge_col])

                # 初期ロードで一覧を表示
                # JS初期化は外部ファイルで実施（/public/scripts/threads_ui.js）
                
                demo.load(_refresh_threads, [current_thread_id], [threads_html, threads_state])
                # open/rename/share/delete の隠しトリガ（常に存在・反応させる）
                def _ctx_rename(tid: str):
                    from app.ui.threads_ui import dummy_rename
                    dummy_rename(tid)
                    try:
                        gr.Info(f"名前変更(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                def _ctx_share(tid: str):
                    from app.ui.threads_ui import dummy_share
                    dummy_share(tid)
                    try:
                        gr.Info(f"共有(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                def _ctx_delete(tid: str):
                    from app.ui.threads_ui import dummy_delete
                    dummy_delete(tid)
                    try:
                        gr.Info(f"削除(ダミー): {tid}")
                    except Exception:
                        pass
                    return

                open_trigger.click(lambda tid: _open_by_id(tid), [action_thread_id], [current_thread_id, chat])
                rename_trigger.click(_ctx_rename, [action_thread_id], None)
                share_trigger.click(_ctx_share, [action_thread_id], None)
                delete_trigger.click(_ctx_delete, [action_thread_id], None)
                # ここではバインドしない（threads_html_tab 定義後に1本化してバインド）
                demo.load(lambda: None, None, None, js="()=>{ try { if (window.threadsSetup) { window.threadsSetup(); } } catch(e) { try{console.error('[threads-ui] init error', e);}catch(_){} } }")

            threads_tab = gr.TabItem("スレッド")  # type: ignore[index]
            with threads_tab:
                # サイドバーと同様の縦並び
                threads_state2 = gr.State([])
                threads_html_tab = gr.HTML("", elem_id="threads_list_tab")

                def _refresh_threads_tab(selected_tid: str = ""):
                    items = ui_list_threads()
                    html = build_threads_html_tab(items, selected_tid)
                    return gr.update(value=html), items

                def _open_by_index_tab(items, idx: int):
                    if not items or idx >= len(items):
                        return "", []
                    tid = items[idx].get('id') or ''
                    history = ui_list_messages(tid) if tid else []
                    return tid, history

                demo.load(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])

                # コンテキストメニューのアクション設定
                # ここでのみ1本のバインド（kind変更）でディスパッチし、両方の一覧を更新（同一HTML）
                _evt_kind = action_kind.change(
                    _dispatch_action_both,
                    inputs=[action_kind, action_thread_id, current_thread_id, action_arg],
                    outputs=[current_thread_id, chat, threads_html, threads_html_tab],
                )
                # 念のため、rename/delete直後も確実にタブ側を再フェッチ
                _evt_kind.then(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
                # サイドバー側のリネーム即時反映に追随して、タブ側も定期的に追従
                threads_html.change(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
                # サイドバーの「＋ 新規」後にタブ側の一覧も即更新
                _evt_new.then(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])

                # サイドバーの「＋ 新規」後にタブ側の一覧も即更新
                _evt_new.then(_refresh_threads_tab, None, [threads_html_tab, threads_state2])

                # エッジ列の「＋」で新規作成
                try:
                    new_btn_edge.click(_on_new, None, [threads_html, threads_state, current_thread_id, chat])
                    new_btn_edge.click(_refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2])
                except Exception:
                    pass

                # current_thread_id が変更されたら、両方の一覧を即時更新（自動作成時の即時反映）
                current_thread_id.change(_refresh_threads, [current_thread_id], [threads_html, threads_state]).then(
                    _refresh_threads_tab, [current_thread_id], [threads_html_tab, threads_state2]
                )

            with gr.TabItem("設定"):
                with gr.Group(elem_classes=["combo-field"]):
                    with gr.Row(elem_id="search_title_band"):
                        gr.Markdown("**検索フォーム**")
                    with gr.Row(equal_height=True, elem_id="search_band"):
                        search_box = gr.Textbox(
                            placeholder="キーワードを入力して Enter or 検索ボタンを押してください（2文字以上） ",
                            show_label=False,
                            scale=4,
                            elem_id="searchbox",
                        )
                        search_btn = gr.Button("検索", scale=1)

                    selected = [
                        "テスト1(test1@test.com)",
                        "テスト2(test2@test.com)",
                        "テスト3(test3@test.com)",
                    ]
                    selected_state = gr.State(selected)
                    hit_info = gr.Markdown("", elem_classes=["combo-hint"])
                    combo = gr.Dropdown(
                        choices=selected_state.value,
                        value=selected_state.value,
                        multiselect=True,
                        show_label=True,
                        label="候補（複数選択可）",
                    )
                    chips = gr.HTML(chips_html([]))

                search_box.submit(
                    suggest, [search_box, combo, selected_state], [combo, hit_info]
                )
                search_btn.click(
                    suggest, [search_box, combo, selected_state], [combo, hit_info]
                )

                combo.change(
                    on_change, [combo, selected_state], [selected_state, chips]
                )
                # 保存ボタン: 選択の差分（追加/削除）を表示
                saved_state = gr.State(selected_state.value)
                save_btn = gr.Button("保存")
                save_hint = gr.Markdown("")

                def _save_selected(current_list, previous_list):
                    cur = [str(x) for x in (current_list or [])]
                    prev = [str(x) for x in (previous_list or [])]
                    added = [x for x in cur if x not in prev]
                    removed = [x for x in prev if x not in cur]
                    added_cnt = len(added)
                    removed_cnt = len(removed)
                    added_part = f"｜追加 {added_cnt} 件" + (": " + ", ".join(neutralize_email(x) for x in added) if added_cnt else "")
                    removed_part = f"｜削除 {removed_cnt} 件" + (": " + ", ".join(neutralize_email(x) for x in removed) if removed_cnt else "")
                    summary = "保存しました" + added_part + removed_part
                    try:
                        gr.Info(summary)
                    except Exception:
                        pass
                    return cur, summary

                save_btn.click(_save_selected, [selected_state, saved_state], [saved_state, save_hint])

        demo.queue(max_size=16, default_concurrency_limit=4)
    return demo


def create_api_app() -> FastAPI:
    public_dir = Path(__file__).resolve().parent.parent / "public"

    # Ensure DB schema and seed data are prepared on startup
    bootstrap_schema_and_seed()

    api = FastAPI()
    ensure_public_assets(public_dir)
    mount_public_and_routes(api, public_dir)

    @api.get("/")
    def _root():
        return RedirectResponse(url="/gradio")

    # --- REST API (via routers) ---
    api_router = APIRouter(prefix="/api")
    api_router.include_router(threads_router)
    api_router.include_router(settings_router)
    api.include_router(api_router)

    return api


def create_app() -> FastAPI:
    api = create_api_app()
    demo = create_blocks()
    gr.mount_gradio_app(api, demo, path="/gradio")
    return api


