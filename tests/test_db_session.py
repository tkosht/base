from __future__ import annotations

import pytest

from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.models import Thread
from app.db.session import db_session


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    bootstrap_schema_and_seed()
    yield


def test_db_session_rollback_on_exception():
    # Insert then raise -> should rollback
    with pytest.raises(RuntimeError):
        with db_session() as s:
            s.add(Thread(id="rollback-thread-000000000000", title="t"))
            raise RuntimeError("boom")

    # Thread should not exist after rollback
    with db_session() as s:
        assert s.get(Thread, "rollback-thread-000000000000") is None
