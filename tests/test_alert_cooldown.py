from __future__ import annotations

import json

import main as app
from storage.db_sqlite import EventDB


class _FakeSender:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.messages: list[str] = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return self.result


class _FakeLogger:
    def __init__(self) -> None:
        self.messages: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def info(self, *args: object, **kwargs: object) -> None:
        self.messages.append((args, kwargs))


def test_fall_alert_success_advances_cooldown_and_writes_event(monkeypatch):
    db = EventDB(":memory:")
    line = _FakeSender(False)
    discord = _FakeSender(True)
    logger = _FakeLogger()
    fixed_ts = "2026-04-09T02:14:32+08:00"
    fixed_display_ts = "2026年04月09日 02:14:32"

    monkeypatch.setattr(app, "now_timestamp", lambda: fixed_ts)
    monkeypatch.setattr(app, "display_timestamp_from_iso", lambda _ts: fixed_display_ts)

    try:
        last_alert_ts = 10.0
        now_ts = 70.0

        if app._send_fall_alert(
            db,
            line,
            discord,
            logger,
            {
                "trunk_angle_deg": 66.2,
                "hip_speed": 0.42,
                "fall_score": 0.8,
                "in_bed_roi": False,
            },
        ):
            last_alert_ts = now_ts

        rows = db.fetch_recent(limit=10)
    finally:
        db.close()

    assert last_alert_ts == now_ts
    assert rows[0]["event_type"] == "fall"
    assert rows[0]["state"] == app.PostureState.FALLEN.value
    assert rows[0]["ts"] == fixed_ts
    assert json.loads(rows[0]["payload"]) == {
        "source": "vision",
        "alert_level": "critical",
        "trunk_angle_deg": 66.2,
        "hip_speed": 0.42,
        "fall_score": 0.8,
        "in_bed_roi": False,
        "line_sent": False,
        "discord_sent": True,
        "message_sent": True,
    }
    assert line.messages == ["姿勢警報：偵測到跌倒，時間：2026年04月09日 02:14:32"]
    assert discord.messages == line.messages


def test_fall_alert_total_failure_keeps_cooldown_and_writes_event(monkeypatch):
    db = EventDB(":memory:")
    line = _FakeSender(False)
    discord = _FakeSender(False)
    logger = _FakeLogger()
    fixed_ts = "2026-04-09T02:14:32+08:00"
    fixed_display_ts = "2026年04月09日 02:14:32"

    monkeypatch.setattr(app, "now_timestamp", lambda: fixed_ts)
    monkeypatch.setattr(app, "display_timestamp_from_iso", lambda _ts: fixed_display_ts)

    try:
        last_alert_ts = 10.0
        now_ts = 70.0

        if app._send_fall_alert(db, line, discord, logger):
            last_alert_ts = now_ts

        rows = db.fetch_recent(limit=10)
    finally:
        db.close()

    assert last_alert_ts == 10.0
    assert rows[0]["event_type"] == "fall"
    assert rows[0]["state"] == app.PostureState.FALLEN.value
    assert rows[0]["ts"] == fixed_ts
    assert json.loads(rows[0]["payload"]) == {
        "source": "vision",
        "alert_level": "critical",
        "line_sent": False,
        "discord_sent": False,
        "message_sent": False,
    }
    assert line.messages == ["姿勢警報：偵測到跌倒，時間：2026年04月09日 02:14:32"]
    assert discord.messages == line.messages
