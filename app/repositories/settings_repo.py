from __future__ import annotations

"""Application settings repository.

設計意図:
- UI 表示切替のための `AppSettings` を永続化・取得する。
- シングルトン行（id=1）を前提とし、存在しない場合は作成する。
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.db.models import AppSettings


class SettingsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self) -> AppSettings:
        obj = self.session.get(AppSettings, 1)
        if obj is None:
            obj = AppSettings(
                id=1, show_thread_sidebar=True, show_threads_tab=True
            )
            self.session.add(obj)
            self.session.flush()
        return obj

    def update(
        self,
        *,
        show_thread_sidebar: Optional[bool] = None,
        show_threads_tab: Optional[bool] = None,
    ) -> AppSettings:
        obj = self.get_or_create()
        if show_thread_sidebar is not None:
            obj.show_thread_sidebar = show_thread_sidebar
        if show_threads_tab is not None:
            obj.show_threads_tab = show_threads_tab
        self.session.flush()
        return obj
