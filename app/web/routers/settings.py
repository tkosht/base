from __future__ import annotations

from fastapi import APIRouter

from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/settings/app")
def get_settings():
    svc = SettingsService()
    s = svc.get()
    return {
        "show_thread_sidebar": s.show_thread_sidebar,
        "show_threads_tab": s.show_threads_tab,
    }


@router.patch("/settings/app")
def patch_settings(payload: dict):  # {show_thread_sidebar?, show_threads_tab?}
    svc = SettingsService()
    s = svc.update(
        show_thread_sidebar=payload.get("show_thread_sidebar"),
        show_threads_tab=payload.get("show_threads_tab"),
    )
    return {
        "show_thread_sidebar": s.show_thread_sidebar,
        "show_threads_tab": s.show_threads_tab,
    }
