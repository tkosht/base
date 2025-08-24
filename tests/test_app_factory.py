from __future__ import annotations

import os

from fastapi.testclient import TestClient
from app.db.session import reconfigure_engine
from app.app_factory import create_api_app


def test_create_app_and_endpoints(tmp_path, monkeypatch):
    # Use isolated DB
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/app.db")

    reconfigure_engine()
    app = create_api_app()
    with TestClient(app) as client:
        # manifest route works
        r = client.get("/manifest.json")
        assert r.status_code == 200

        assert r.headers["content-type"].startswith("application/manifest+json")

        # Favicon provided
        r = client.get("/favicon.ico")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/")


