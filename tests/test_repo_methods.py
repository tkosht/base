from __future__ import annotations

import pytest

from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import db_session, reconfigure_engine
from app.repositories.thread_repo import ThreadRepository


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    reconfigure_engine()
    bootstrap_schema_and_seed()
    yield


def test_crud_and_list_recent():
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.create("t-000000000000000000000000", "Title")
        assert t.id.startswith("t-")

        got = repo.get(t.id)
        assert got is not None and got.id == t.id

        # Rename
        repo.rename(t.id, "New Title")
        assert repo.get(t.id).title == "New Title"

        # Archive
        assert repo.archive(t.id) is True
        assert repo.get(t.id).archived is True

        # Messages
        repo.add_message("m-000000000000000000000000", t.id, "user", "hi")
        repo.add_message("m-000000000000000000000001", t.id, "assistant", "ok")
        msgs = repo.list_messages(t.id)
        assert [m.role for m in msgs] == ["user", "assistant"]

        # List recent (should include our thread)
        recents = repo.list_recent(limit=10)
        assert any(x.id == t.id for x in recents)

        # Delete
        assert repo.delete(t.id) is True
        assert repo.get(t.id) is None


