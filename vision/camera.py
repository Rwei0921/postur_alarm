"""Camera adapter supporting OpenCV and Picamera2 backends."""

from __future__ import annotations

import importlib
from typing import Any, Tuple


class Camera:
    def __init__(
        self,
        source: int | str = 0,
        width: int | None = None,
        height: int | None = None,
        backend: str = "auto",
    ) -> None:
        self.source = int(source) if isinstance(source, str) and source.isdigit() else source
        self.width = width
        self.height = height
        self.backend = backend.lower()

        self._cv2 = None
        self.cap = None
        self._picamera2 = None
        self._using_backend = ""

        if self.backend not in {"auto", "opencv", "picamera2"}:
            raise ValueError("backend must be one of: auto, opencv, picamera2")

        if self.backend == "picamera2":
            self._open_picamera2(strict=True)
        elif self.backend == "opencv":
            self._open_opencv(strict=True)
        else:
            # auto mode: prefer picamera2 (best for Raspberry Pi Camera Module 3), then fallback to OpenCV.
            if not self._open_picamera2(strict=False):
                self._open_opencv(strict=True)

    @staticmethod
    def _load_cv2():
        try:
            return importlib.import_module("cv2")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenCV is required for Camera") from exc

    @staticmethod
    def _load_picamera2() -> Any:
        try:
            return getattr(importlib.import_module("picamera2"), "Picamera2")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("picamera2 is required for Camera backend 'picamera2'") from exc

    def _open_opencv(self, strict: bool) -> bool:
        try:
            self._cv2 = self._load_cv2()
            cap = self._cv2.VideoCapture(self.source)

            if self.width is not None:
                cap.set(self._cv2.CAP_PROP_FRAME_WIDTH, self.width)
            if self.height is not None:
                cap.set(self._cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            if not cap.isOpened():
                cap.release()
                if strict:
                    raise RuntimeError(f"Cannot open OpenCV camera source: {self.source}")
                return False

            self.cap = cap
            self._using_backend = "opencv"
            return True
        except Exception:
            if strict:
                raise
            return False

    def _open_picamera2(self, strict: bool) -> bool:
        try:
            Picamera2 = self._load_picamera2()
            picam2 = Picamera2()
            main_cfg: dict[str, Any] = {}
            if self.width is not None and self.height is not None:
                main_cfg["size"] = (self.width, self.height)

            config = picam2.create_preview_configuration(main=main_cfg or None)
            picam2.configure(config)
            picam2.start()

            self._picamera2 = picam2
            self._using_backend = "picamera2"
            return True
        except Exception:
            if strict:
                raise
            return False

    def is_opened(self) -> bool:
        if self._using_backend == "picamera2":
            return self._picamera2 is not None
        return bool(self.cap and self.cap.isOpened())

    def read_frame(self) -> Tuple[bool, Any]:
        if not self.is_opened():
            return False, None

        if self._using_backend == "picamera2":
            if self._picamera2 is None:
                return False, None
            frame = self._picamera2.capture_array()
            # Picamera2 returns RGB; rest of pipeline expects BGR.
            frame_bgr = frame[..., ::-1].copy()
            return True, frame_bgr

        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
        if self._picamera2 is not None:
            try:
                self._picamera2.stop()
            finally:
                self._picamera2.close()
