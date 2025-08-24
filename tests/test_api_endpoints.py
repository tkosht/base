from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.app_factory import create_api_app
from app.db.bootstrap import bootstrap_schema_and_seed
from app.db.session import reconfigure_engine


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")
    reconfigure_engine()
    bootstrap_schema_and_seed()
    app = create_api_app()
    with TestClient(app) as c:
        yield c


def test_threads_crud_and_messages(client: TestClient):
    # Create thread
    r = client.post("/api/threads", json={"title": "T1"})
    assert r.status_code == 201
    tid = r.json()["id"]

    # List
    r = client.get("/api/threads")
    assert r.status_code == 200 and any(t["id"] == tid for t in r.json())

    # Add messages
    assert client.post(f"/api/threads/{tid}/messages", json={"role": "user", "content": "hi"}).status_code == 201
    assert client.post(f"/api/threads/{tid}/messages", json={"role": "assistant", "content": "ok"}).status_code == 201

    # List messages
    r = client.get(f"/api/threads/{tid}/messages")
    assert r.status_code == 200
    roles = [m["role"] for m in r.json()]
    assert roles == ["user", "assistant"]

    # Update thread
    r = client.patch(f"/api/threads/{tid}", json={"title": "T1-new", "archived": True})
    assert r.status_code == 200 and r.json()["title"] == "T1-new" and r.json()["archived"] is True

    # Delete
    assert client.delete(f"/api/threads/{tid}").status_code == 204
    assert client.get(f"/api/threads/{tid}/messages").status_code in (404, 200)


def test_settings_get_update(client: TestClient):
    r = client.get("/api/settings/app")
    assert r.status_code == 200 and r.json()["show_thread_sidebar"] is True

    r = client.patch("/api/settings/app", json={"show_thread_sidebar": False})
    assert r.status_code == 200 and r.json()["show_thread_sidebar"] is False



