"""Histórico em memória das últimas 50 buscas."""
from collections import deque
from datetime import datetime

_history: deque = deque(maxlen=50)


def add(entry: dict) -> None:
    entry["ts"] = datetime.utcnow().isoformat() + "Z"
    _history.appendleft(entry)


def all() -> list[dict]:
    return list(_history)


def get(search_id: str) -> dict | None:
    for h in _history:
        if h["search_id"] == search_id:
            return h
    return None
