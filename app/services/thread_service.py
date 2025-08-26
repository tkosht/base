"""Thread/Message service layer.

設計意図:
- UI/Handlers から直接 Repository を叩かず、ユースケース単位のAPIで集約。
- ID生成や簡単なビジネスルール（初回タイトル推定など）をここで担う。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.db.session import db_session
from app.repositories.thread_repo import ThreadRepository


def _generate_new_id() -> str:
    """Generate a 26-char unique-like id (UUID4 based, truncated).

    設計意図:
    - SQLite/PostgreSQL両対応の文字列PK。
    - 短期MVPのためULID実装は避け、UUID4を26文字に切詰め採用。
    """
    return uuid.uuid4().hex[:26]


def _simple_ulid(_seed: str = "") -> str:
    """Compatibility helper used by tests/call sites.

    For MVP we reuse the same 26-char UUID4-based ID.
    """
    return _generate_new_id()


@dataclass
class CreateThreadResult:
    thread_id: str


class ThreadService:
    def create_thread(
        self, title_hint: str | None = None, fixed_id: str | None = None
    ) -> CreateThreadResult:
        with db_session() as s:
            repo = ThreadRepository(s)
            thread_id = fixed_id or _generate_new_id()
            # 衝突回避: 最大10回再生成（理論上ほぼ発生しない）
            attempts = 0
            while repo.get(thread_id) is not None and attempts < 10:
                thread_id = _generate_new_id()
                attempts += 1
            title = (title_hint or "").strip() or None
            repo.create(thread_id=thread_id, title=title)
            return CreateThreadResult(thread_id=thread_id)

    def add_user_message(
        self, thread_id: str, content: str, fixed_id: str | None = None
    ) -> str:
        with db_session() as s:
            repo = ThreadRepository(s)
            msg_id = fixed_id or _simple_ulid(content[:26])
            repo.add_message(
                msg_id=msg_id,
                thread_id=thread_id,
                role="user",
                content=content,
            )
            return msg_id

    def add_assistant_message(
        self, thread_id: str, content: str, fixed_id: str | None = None
    ) -> str:
        with db_session() as s:
            repo = ThreadRepository(s)
            msg_id = fixed_id or _simple_ulid(content[:26])
            repo.add_message(
                msg_id=msg_id,
                thread_id=thread_id,
                role="assistant",
                content=content,
            )
            return msg_id

    def get_history(self, thread_id: str) -> list[dict]:
        with db_session() as s:
            repo = ThreadRepository(s)
            msgs = repo.list_messages(thread_id)
            return [{"role": m.role, "content": m.content} for m in msgs]
