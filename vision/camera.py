"""Camera adapter around OpenCV VideoCapture."""

from __future__ import annotations

import importlib
from typing import Any, Tuple


class Camera:
    def __init__(self, source: int | str = 0, width: int | None = None, height: int | None = None) -> None:
        self._cv2 = self._load_cv2()
        self.source = int(source) if isinstance(source, str) and source.isdigit() else source
        self.cap = self._cv2.VideoCapture(self.source)

        if width is not None:
            self.cap.set(self._cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            self.cap.set(self._cv2.CAP_PROP_FRAME_HEIGHT, height)

    @staticmethod
    def _load_cv2():
        try:
            return importlib.import_module("cv2")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenCV is required for Camera") from exc

    def is_opened(self) -> bool:
        return bool(self.cap and self.cap.isOpened())

    def read_frame(self) -> Tuple[bool, Any]:
        if not self.is_opened():
            return False, None
        return self.cap.read()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
