from __future__ import annotations


def healthcheck(name: str = "template") -> str:
    return f"{name}:ok"
