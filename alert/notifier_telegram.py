"""Telegram Bot API notifier."""

from __future__ import annotations

from typing import Any


class TelegramNotifier:
    def __init__(self, bot_token: str = "", chat_id: str = "", timeout: float = 5.0) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout

    def send(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False

        requests = self._load_requests()
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            return bool(response.ok)
        except Exception:
            return False

    @staticmethod
    def _load_requests() -> Any:
        import requests

        return requests
