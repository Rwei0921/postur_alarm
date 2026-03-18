"""Shared utility helpers."""

from __future__ import annotations

import logging
from datetime import datetime, timezone


def now_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def setup_logger(name: str = "posture_alarm", level: int = logging.INFO) -> logging.Logger:
    """Create and configure a consistent console logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)

    return logger
