"""Application settings service.

設計意図:
- 表示制御設定の取得/更新をユースケース単位のAPIで提供する。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.session import db_session
from app.repositories.settings_repo import SettingsRepository


@dataclass
class AppSettingsDTO:
    show_thread_sidebar: bool
    show_threads_tab: bool


class SettingsService:
    def get(self) -> AppSettingsDTO:
        with db_session() as s:
            repo = SettingsRepository(s)
            obj = repo.get_or_create()
            return AppSettingsDTO(
                show_thread_sidebar=obj.show_thread_sidebar,
                show_threads_tab=obj.show_threads_tab,
            )

    def update(
        self,
        *,
        show_thread_sidebar: bool | None = None,
        show_threads_tab: bool | None = None,
    ) -> AppSettingsDTO:
        with db_session() as s:
            repo = SettingsRepository(s)
            obj = repo.update(
                show_thread_sidebar=show_thread_sidebar,
                show_threads_tab=show_threads_tab,
            )
            return AppSettingsDTO(
                show_thread_sidebar=obj.show_thread_sidebar,
                show_threads_tab=obj.show_threads_tab,
            )
