"""LINE Notify sender."""

from __future__ import annotations

from typing import Any


class LineNotifier:
    def __init__(self, token: str = "", timeout: float = 5.0) -> None:
        self.token = token
        self.timeout = timeout

    def send(self, message: str) -> bool:
        if not self.token:
            return False
        requests = self._load_requests()
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"message": message}
        try:
            response = requests.post(
                "https://notify-api.line.me/api/notify",
                headers=headers,
                data=data,
                timeout=self.timeout,
            )
            return bool(response.ok)
        except Exception:
            return False

    @staticmethod
    def _load_requests() -> Any:
        import requests

        return requests
