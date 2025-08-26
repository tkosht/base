from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        # Default to local SQLite under ./data
        os.makedirs("data", exist_ok=True)
        url = "sqlite:///./data/app.db"
    return url


ENGINE = None  # late-bound for test isolation
SessionLocal = None  # type: ignore[assignment]


def _init_engine(url: str | None = None) -> None:
    """(Re)initialize global ENGINE/SessionLocal.

    設計意図: テストで DATABASE_URL を切り替えた後に、
    グローバルENGINEを再バインドできるようにする。
    """
    global ENGINE, SessionLocal
    url = url or get_database_url()
    ENGINE = create_engine(url, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(
        bind=ENGINE, autoflush=False, expire_on_commit=False, future=True
    )


def get_engine():
    if ENGINE is None:
        _init_engine()
    return ENGINE


def reconfigure_engine(database_url: str | None = None) -> None:
    """外部用途: 新しいURLでENGINE/SessionLocalを再構成する。"""
    _init_engine(database_url)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        _init_engine()
    session = SessionLocal()  # type: ignore[operator]
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
