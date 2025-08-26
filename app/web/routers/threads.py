from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.db.session import db_session
from app.repositories.thread_repo import ThreadRepository
from app.services.thread_service import ThreadService


router = APIRouter()


@router.get("/threads")
def list_threads():
    with db_session() as s:
        repo = ThreadRepository(s)
        items = repo.list_recent(limit=100)
        return [
            {"id": t.id, "title": t.title, "archived": t.archived}
            for t in items
        ]


@router.post("/threads", status_code=201)
def create_thread(payload: dict):  # {title?: str}
    title = (payload.get("title") or "").strip() or None
    svc = ThreadService()
    created = svc.create_thread(title_hint=title)
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.get(created.thread_id)
        return {"id": t.id, "title": t.title, "archived": t.archived}


@router.get("/threads/{thread_id}/messages")
def list_messages(thread_id: str):
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.get(thread_id)
        if t is None:
            raise HTTPException(status_code=404, detail="thread not found")
        msgs = repo.list_messages(thread_id)
        return [{"role": m.role, "content": m.content} for m in msgs]


@router.post("/threads/{thread_id}/messages", status_code=201)
def add_message(thread_id: str, payload: dict):  # {role, content}
    role: str = payload.get("role")
    content: str = payload.get("content")
    if role not in ("user", "assistant", "system"):
        raise HTTPException(status_code=422, detail="invalid role")
    svc = ThreadService()
    if role == "user":
        svc.add_user_message(thread_id, content)
    else:
        svc.add_assistant_message(thread_id, content)
    return {"ok": True}


@router.patch("/threads/{thread_id}")
def update_thread(thread_id: str, payload: dict):  # {title?, archived?}
    with db_session() as s:
        repo = ThreadRepository(s)
        t = repo.get(thread_id)
        if t is None:
            raise HTTPException(status_code=404, detail="thread not found")
        if "title" in payload and payload["title"] is not None:
            repo.rename(thread_id, (payload["title"] or "").strip())
        if payload.get("archived") is True:
            repo.archive(thread_id)
        return {"id": t.id, "title": t.title, "archived": t.archived}


@router.delete("/threads/{thread_id}", status_code=204)
def delete_thread(thread_id: str):
    with db_session() as s:
        repo = ThreadRepository(s)
        ok = repo.delete(thread_id)
        if not ok:
            raise HTTPException(status_code=404, detail="thread not found")
        return None
