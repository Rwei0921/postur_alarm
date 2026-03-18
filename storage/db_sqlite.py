"""SQLite event storage."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from core.utils import now_timestamp


class EventDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                event_type TEXT NOT NULL,
                state TEXT NOT NULL,
                payload TEXT
            )
            """
        )
        self.conn.commit()

    def log_event(
        self,
        event_type: str,
        state: str,
        payload: dict[str, Any] | None = None,
        ts: str | None = None,
    ) -> int:
        timestamp = ts or now_timestamp()
        payload_json = json.dumps(payload or {}, ensure_ascii=True)
        cursor = self.conn.execute(
            "INSERT INTO events (ts, event_type, state, payload) VALUES (?, ?, ?, ?)",
            (timestamp, event_type, state, payload_json),
        )
        self.conn.commit()
        row_id = cursor.lastrowid
        return int(row_id) if row_id is not None else -1

    def fetch_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id, ts, event_type, state, payload FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.conn.close()
