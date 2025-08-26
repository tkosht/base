"""互換レイヤ（委譲）。

外部互換のために `create_app()` を公開し、内部の実装は `app/web/factory.py` と
`app/ui/app_ui.py` に委譲する。挙動は変更しない（ルート、マニフェスト、favicon、/gradio 等）。
"""

from __future__ import annotations

from fastapi import FastAPI
import gradio as gr


def create_app() -> FastAPI:
    from app.web.factory import create_api_app as _create_api_app
    from app.ui.app_ui import create_blocks as _create_blocks

    api = _create_api_app()
    demo = _create_blocks()
    gr.mount_gradio_app(api, demo, path="/gradio")
    return api
