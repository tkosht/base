from __future__ import annotations

import pytest

from app.db import bootstrap
from app.db.models import AppSettings, Message, Thread
from app.db.session import db_session, get_database_url, reconfigure_engine


@pytest.fixture(autouse=True)
def _isolate_tmp_db(tmp_path, monkeypatch):
    # Ensure a unique SQLite file per test
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    reconfigure_engine()
    yield


def test_get_database_url_default_creates_data_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    url = get_database_url()
    assert url == "sqlite:///./data/app.db"
    assert (tmp_path / "data").exists()


def test_bootstrap_creates_schema_and_seed_idempotent():
    # First bootstrap
    bootstrap.bootstrap_schema_and_seed()

    with db_session() as s:
        settings = s.query(AppSettings).all()
        threads = s.query(Thread).order_by(Thread.id).all()
        messages = s.query(Message).order_by(Message.id).all()

        assert len(settings) == 1
        assert len(threads) == 2
        assert len(messages) == 2
        assert threads[0].title == "Welcome"
        assert threads[1].title == "Sample Research"

    # Second bootstrap should not duplicate
    bootstrap.bootstrap_schema_and_seed()

    with db_session() as s:
        assert s.query(AppSettings).count() == 1
        assert s.query(Thread).count() == 2
        assert s.query(Message).count() == 2


def test_message_relationships_loaded():
    bootstrap.bootstrap_schema_and_seed()
    with db_session() as s:
        t = s.query(Thread).filter_by(title="Welcome").first()
        assert t is not None
        # Relationship should load at least one message
        assert len(t.messages) >= 1
        assert t.messages[0].role in {"assistant", "user", "system"}
