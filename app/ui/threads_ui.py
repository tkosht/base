from __future__ import annotations

"""Threads / Settings UI controllers.

設計意図:
- Gradio ハンドラから呼ばれる純粋関数群として実装し、テスト容易性を最大化する。
- 永続化は service 層に委譲し、ここでは入出力整形に専念する。
"""

from dataclasses import dataclass
from typing import List, Dict

from app.services.thread_service import ThreadService
from app.services.settings_service import SettingsService, AppSettingsDTO
from app.db.session import db_session
from app.repositories.thread_repo import ThreadRepository


def get_app_settings() -> dict:
    s = SettingsService().get()
    return {
        "show_thread_sidebar": s.show_thread_sidebar,
        "show_threads_tab": s.show_threads_tab,
    }


def update_app_settings(*, show_thread_sidebar: bool | None = None, show_threads_tab: bool | None = None) -> dict:
    s = SettingsService().update(
        show_thread_sidebar=show_thread_sidebar,
        show_threads_tab=show_threads_tab,
    )
    return {
        "show_thread_sidebar": s.show_thread_sidebar,
        "show_threads_tab": s.show_threads_tab,
    }


def list_threads() -> list[dict]:
    with db_session() as s:
        repo = ThreadRepository(s)
        items = repo.list_recent(limit=100)
        def build_summary_and_flag(thread_id: str) -> tuple[str, bool]:
            # 最新メッセージの先頭部分を概要として返し、空スレッドかのフラグも返す
            msgs = repo.list_messages(thread_id, limit=3)
            if not msgs:
                return "", False
            # 末尾から user/assistant 優先で拾う。なければ最後のメッセージ。
            pick = None
            for m in reversed(msgs):
                if m.role in ("user", "assistant"):
                    pick = m
                    break
            if pick is None:
                pick = msgs[-1]
            text = (pick.content or "").strip()
            if len(text) > 120:
                return text[:120] + "…", True
            return text, True

        return [
            {
                "id": t.id,
                "title": t.title,
                "archived": t.archived,
                "summary": build_summary_and_flag(t.id)[0],
                "has_messages": build_summary_and_flag(t.id)[1],
            }
            for t in items
        ]


def create_thread(title_hint: str | None = None) -> dict:
    # スレッドはユーザーが最初のメッセージを送る直前にのみ作成する（無駄な空スレッドを作らない）
    created = ThreadService().create_thread(title_hint=title_hint)
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.get(created.thread_id)
        return {"id": t.id, "title": t.title, "archived": t.archived}


def rename_thread(thread_id: str, new_title: str) -> dict:
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.get(thread_id)
        if not t:
            return {}
        repo.rename(thread_id, new_title)
        return {"id": t.id, "title": t.title, "archived": t.archived}


def archive_thread(thread_id: str) -> bool:
    with db_session() as s:
        repo = ThreadRepository(s)
        return repo.archive(thread_id)


def delete_thread(thread_id: str) -> bool:
    with db_session() as s:
        repo = ThreadRepository(s)
        return repo.delete(thread_id)


def list_messages(thread_id: str) -> list[dict]:
    with db_session() as s:
        repo = ThreadRepository(s)
        msgs = repo.list_messages(thread_id)
        return [{"role": m.role, "content": m.content} for m in msgs]


def toggle_sidebar_visibility() -> dict:
    """Toggle show_thread_sidebar and return updated flags.

    設計意図:
    - Gradioの開閉トグルから呼ばれ、設定値をDBに永続化する。
    - UI側は戻り値をもとに表示状態を反映する。
    """
    s = SettingsService().get()
    updated = SettingsService().update(show_thread_sidebar=not s.show_thread_sidebar)
    return {
        "show_thread_sidebar": updated.show_thread_sidebar,
        "show_threads_tab": updated.show_threads_tab,
    }


# ---- Dummy context menu actions (MVP placeholders) ----
def dummy_rename(thread_id: str) -> dict:
    return {"ok": True, "action": "rename", "thread_id": thread_id}


def dummy_share(thread_id: str) -> dict:
    return {"ok": True, "action": "share", "thread_id": thread_id}


def dummy_delete(thread_id: str) -> dict:
    return {"ok": True, "action": "delete", "thread_id": thread_id}



def dummy_change_owner(thread_id: str) -> dict:
    return {"ok": True, "action": "change_owner", "thread_id": thread_id}



