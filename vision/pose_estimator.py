"""MediaPipe Pose keypoint extraction."""

from __future__ import annotations

import importlib
from typing import Any


class PoseEstimator:
    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self._mp = self._load_mediapipe()
        self._pose = self._mp.solutions.pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    @staticmethod
    def _load_mediapipe() -> Any:
        try:
            return importlib.import_module("mediapipe")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("mediapipe is required for PoseEstimator") from exc

    def extract_landmarks(self, frame_bgr: Any) -> list[dict[str, float]]:
        cv2 = self._load_cv2()
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._pose.process(frame_rgb)

        if not results.pose_landmarks:
            return []

        landmarks: list[dict[str, float]] = []
        for lm in results.pose_landmarks.landmark:
            landmarks.append(
                {
                    "x": float(lm.x),
                    "y": float(lm.y),
                    "z": float(lm.z),
                    "visibility": float(lm.visibility),
                }
            )
        return landmarks

    def close(self) -> None:
        self._pose.close()

    @staticmethod
    def _load_cv2() -> Any:
        try:
            return importlib.import_module("cv2")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenCV is required for PoseEstimator") from exc
