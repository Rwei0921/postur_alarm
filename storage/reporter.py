"""CSV report generator based on SQLite events."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from storage.db_sqlite import connect_event_db


class Reporter:
    def __init__(self, db_path: str, output_dir: str) -> None:
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(self, day: date | None = None) -> Path:
        target_day = day or date.today()
        start = datetime.combine(target_day, datetime.min.time())
        end = start + timedelta(days=1)
        rows = self._fetch_range(start.isoformat(), end.isoformat())
        output = self.output_dir / f"daily_{target_day.isoformat()}.csv"
        self._write_csv(output, rows)
        return output

    def generate_weekly_report(self, day: date | None = None) -> Path:
        target_day = day or date.today()
        week_start = target_day - timedelta(days=target_day.weekday())
        start = datetime.combine(week_start, datetime.min.time())
        end = start + timedelta(days=7)
        rows = self._fetch_range(start.isoformat(), end.isoformat())
        output = self.output_dir / f"weekly_{week_start.isoformat()}.csv"
        self._write_csv(output, rows)
        return output

    def generate_daily_summary_report(self, day: date | None = None) -> Path:
        target_day = day or date.today()
        start = datetime.combine(target_day, datetime.min.time())
        end = start + timedelta(days=1)
        rows = self._fetch_range(start.isoformat(), end.isoformat())
        summary = self._summarize(rows)
        output = self.output_dir / f"summary_{target_day.isoformat()}.csv"
        self._write_summary_csv(output, summary)
        return output

    def _fetch_range(self, start_iso: str, end_iso: str) -> list[dict[str, str]]:
        conn = connect_event_db(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT ts, event_type, state, payload
                FROM events
                WHERE ts >= ? AND ts < ?
                ORDER BY ts ASC
                """,
                (start_iso, end_iso),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=["ts", "event_type", "state", "payload"])
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _summarize(rows: list[dict[str, str]]) -> dict[str, int]:
        summary = {
            "total_events": len(rows),
            "fall_events": 0,
            "state_changes": 0,
            "lying_safe_events": 0,
            "sedentary_events": 0,
            "line_sent": 0,
            "discord_sent": 0,
            "message_sent": 0,
            "message_failed": 0,
        }

        for row in rows:
            event_type = row.get("event_type", "")
            state = row.get("state", "")
            if event_type == "fall":
                summary["fall_events"] += 1
            if event_type == "state_change":
                summary["state_changes"] += 1
            if state == "LYING_SAFE":
                summary["lying_safe_events"] += 1
            if state == "SEDENTARY":
                summary["sedentary_events"] += 1

            payload = Reporter._parse_payload(row.get("payload", ""))
            if payload.get("line_sent") is True:
                summary["line_sent"] += 1
            if payload.get("discord_sent") is True:
                summary["discord_sent"] += 1
            if payload.get("message_sent") is True:
                summary["message_sent"] += 1
            if event_type == "fall" and payload.get("message_sent") is False:
                summary["message_failed"] += 1

        return summary

    @staticmethod
    def _parse_payload(payload: str) -> dict[str, object]:
        try:
            value = json.loads(payload or "{}")
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _write_summary_csv(path: Path, summary: dict[str, int]) -> None:
        with path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=["metric", "value"])
            writer.writeheader()
            for metric, value in summary.items():
                writer.writerow({"metric": metric, "value": value})
