from __future__ import annotations

import os

import pytest

from app.db.bootstrap import bootstrap_schema_and_seed
from app.services.thread_service import ThreadService
from app.db.session import reconfigure_engine


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    reconfigure_engine()
    bootstrap_schema_and_seed()
    yield


def test_create_thread_and_add_messages_and_read_history():
    svc = ThreadService()
    created = svc.create_thread(
        title_hint="My Thread", fixed_id="thread-000000000000000000"
    )
    assert created.thread_id.startswith("thread-")

    uid = svc.add_user_message(
        created.thread_id, "hello", fixed_id="msg-u-00000000000000000000"
    )
    aid = svc.add_assistant_message(
        created.thread_id, "world", fixed_id="msg-a-00000000000000000000"
    )

    assert uid.startswith("msg-u-")
    assert aid.startswith("msg-a-")

    hist = svc.get_history(created.thread_id)
    assert [m["role"] for m in hist] == ["user", "assistant"]
    assert [m["content"] for m in hist] == ["hello", "world"]
