"""Thread/Message persistence operations (repository layer).

設計意図:
- サービス層からDB操作を分離し、移行（PostgreSQL）・テスト容易性を高める。
- ここではビジネスルールは持たず、単純なCRUDとクエリに徹する。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Message, Thread


class ThreadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # Threads
    def create(self, thread_id: str, title: str | None) -> Thread:
        t = Thread(id=thread_id, title=title)
        self.session.add(t)
        # セッション内で即時取得できるよう flush する
        self.session.flush()
        return t

    def get(self, thread_id: str) -> Thread | None:
        return self.session.get(Thread, thread_id)

    def list_recent(self, limit: int = 50) -> list[Thread]:
        stmt = (
            select(Thread)
            .where(Thread.archived.is_(False))
            .order_by(
                Thread.last_message_at.desc().nullslast(),
                Thread.created_at.desc(),
            )
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def rename(self, thread_id: str, title: str) -> Thread | None:
        t = self.get(thread_id)
        if not t:
            return None
        t.title = title
        return t

    def archive(self, thread_id: str) -> bool:
        t = self.get(thread_id)
        if not t:
            return False
        t.archived = True
        return True

    def delete(self, thread_id: str) -> bool:
        t = self.get(thread_id)
        if not t:
            return False
        self.session.delete(t)
        self.session.flush()
        return True

    # Messages
    def add_message(
        self, msg_id: str, thread_id: str, role: str, content: str
    ) -> Message:
        m = Message(id=msg_id, thread_id=thread_id, role=role, content=content)
        self.session.add(m)
        # 更新指標
        t = self.get(thread_id)
        if t:
            # last_message_at はDBのデフォルトを尊重し、ここでは未設定のままでも良い。
            ...
        # 即時に list で取得できるよう flush
        self.session.flush()
        return m

    def list_messages(
        self, thread_id: str, limit: int = 1000
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())
