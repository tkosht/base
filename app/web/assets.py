from __future__ import annotations

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.utils import svg as svg_utils


def ensure_public_assets(public_dir: Path) -> None:
    os.makedirs(public_dir, exist_ok=True)

    manifest_path = public_dir / "manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(
            (
                '{\n'
                '  "name": "でもあぷり",\n'
                '  "short_name": "でもあぷり",\n'
                '  "start_url": ".",\n'
                '  "display": "standalone",\n'
                '  "background_color": "#111827",\n'
                '  "theme_color": "#111827",\n'
                '  "icons": []\n'
                '}\n'
            ),
            encoding="utf-8",
        )

    favicon_path = public_dir / "favicon.ico"
    if not favicon_path.exists():
        svg = svg_utils.build_favicon_svg("🦜", size=64, circle_fill="#1f2937", ring_color="#fff", ring_width=2)
        (public_dir / "favicon.svg").write_text(svg, encoding="utf-8")
        favicon_path.write_text(svg, encoding="utf-8")


def mount_public_and_routes(api: FastAPI, public_dir: Path) -> None:
    """Mount static dir and register manifest/favicon routes (behavior-compatible)."""
    manifest_path = public_dir / "manifest.json"
    api.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    @api.get("/manifest.json")
    def _manifest_file():  # noqa: D401
        return FileResponse(str(manifest_path), media_type="application/manifest+json")

    favicon_path = public_dir / "favicon.ico"

    @api.get("/favicon.ico")
    def _favicon():  # noqa: D401
        return FileResponse(str(favicon_path), media_type="image/svg+xml")


