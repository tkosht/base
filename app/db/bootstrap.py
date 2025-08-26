from __future__ import annotations

from typing import Iterable

from .models import AppSettings, Base, Message, Thread
from .session import get_engine, db_session


def create_all() -> None:
    Base.metadata.create_all(get_engine())


def seed_if_empty() -> None:
    with db_session() as s:
        has_settings = s.query(AppSettings).first()
        if not has_settings:
            s.add(
                AppSettings(
                    id=1, show_thread_sidebar=True, show_threads_tab=True
                )
            )

        has_threads = s.query(Thread).count()
        if has_threads == 0:
            t1 = Thread(id="00000000000000000000000000", title="Welcome")
            t2 = Thread(
                id="00000000000000000000000001", title="Sample Research"
            )
            s.add_all([t1, t2])
            s.flush()
            s.add_all(
                [
                    Message(
                        id="00000000000000000000000002",
                        thread_id=t1.id,
                        role="assistant",
                        content="こんにちは！ここから会話を始めましょう。",
                    ),
                    Message(
                        id="00000000000000000000000003",
                        thread_id=t2.id,
                        role="assistant",
                        content="このスレッドはリサーチのサンプルです。",
                    ),
                ]
            )


def bootstrap_schema_and_seed() -> None:
    create_all()
    seed_if_empty()
