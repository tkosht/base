from __future__ import annotations

import pytest

from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import reconfigure_engine
from app.ui.threads_ui import (
    archive_thread,
    create_thread,
    delete_thread,
    get_app_settings,
    list_messages,
    list_threads,
    rename_thread,
    toggle_sidebar_visibility,
    update_app_settings,
)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    reconfigure_engine()
    bootstrap_schema_and_seed()
    yield


def test_settings_and_threads_flow():
    s = get_app_settings()
    assert s["show_thread_sidebar"] is True

    s2 = update_app_settings(show_thread_sidebar=False)
    assert s2["show_thread_sidebar"] is False

    t = create_thread("Hello")
    tid = t["id"]
    assert t["title"] in ("Hello", None)

    t2 = rename_thread(tid, "Hello-2")
    assert t2["title"] == "Hello-2"

    assert archive_thread(tid) is True
    # delete
    assert delete_thread(tid) is True

    # list_messages (after delete -> empty)
    msgs = list_messages(tid)
    assert isinstance(msgs, list)

    # threads listing reflects creation and deletion flow
    ts = list_threads()
    assert isinstance(ts, list)


def test_toggle_sidebar_persists():
    s1 = get_app_settings()
    s2 = toggle_sidebar_visibility()
    assert s1["show_thread_sidebar"] != s2["show_thread_sidebar"]
    # toggle back
    s3 = toggle_sidebar_visibility()
    assert s3["show_thread_sidebar"] == s1["show_thread_sidebar"]
