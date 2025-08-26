from __future__ import annotations

import pytest

from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import reconfigure_engine
from app.services.settings_service import SettingsService


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    reconfigure_engine()
    bootstrap_schema_and_seed()
    yield


def test_get_and_update_settings():
    svc = SettingsService()
    s = svc.get()
    assert s.show_thread_sidebar is True and s.show_threads_tab is True

    s2 = svc.update(show_thread_sidebar=False)
    assert s2.show_thread_sidebar is False and s2.show_threads_tab is True
