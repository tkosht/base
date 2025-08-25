from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi import APIRouter

from app.db.bootstrap import bootstrap_schema_and_seed
from app.web.assets import ensure_public_assets, mount_public_and_routes
from app.web.routers.threads import router as threads_router
from app.web.routers.settings import router as settings_router


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


