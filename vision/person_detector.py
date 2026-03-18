"""Person presence detection using MediaPipe Pose visibility."""

from __future__ import annotations

import importlib
from typing import Any


class PersonDetector:
    def __init__(
        self,
        visibility_threshold: float = 0.5,
        min_visible_keypoints: int = 6,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.visibility_threshold = visibility_threshold
        self.min_visible_keypoints = min_visible_keypoints

        self._mp = self._load_mediapipe()
        self._pose = self._mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    @staticmethod
    def _load_mediapipe() -> Any:
        try:
            return importlib.import_module("mediapipe")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("mediapipe is required for PersonDetector") from exc

    @staticmethod
    def _load_cv2() -> Any:
        try:
            return importlib.import_module("cv2")
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("OpenCV is required for PersonDetector") from exc

    def has_person(self, landmarks: list[dict[str, float]]) -> bool:
        visible = sum(1 for lm in landmarks if lm.get("visibility", 0.0) >= self.visibility_threshold)
        return visible >= self.min_visible_keypoints

    def detect(self, frame_bgr: Any) -> bool:
        landmarks = self.detect_with_landmarks(frame_bgr)
        return self.has_person(landmarks)

    def detect_with_landmarks(self, frame_bgr: Any) -> list[dict[str, float]]:
        cv2 = self._load_cv2()
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._pose.process(frame_rgb)

        if not results.pose_landmarks:
            return []

        return [
            {
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z),
                "visibility": float(lm.visibility),
            }
            for lm in results.pose_landmarks.landmark
        ]

    def close(self) -> None:
        self._pose.close()
