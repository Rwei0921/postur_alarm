"""Posture state machine for high-level behavior."""

from __future__ import annotations

import time
from enum import Enum


class PostureState(str, Enum):
    NORMAL = "NORMAL"
    SUSPECT_FALL = "SUSPECT_FALL"
    FALLEN = "FALLEN"
    SEDENTARY = "SEDENTARY"


class PostureStateMachine:
    def __init__(
        self,
        suspect_timeout: float = 2.0,
        fall_confirm_seconds: float = 1.2,
        sedentary_seconds: float = 1800.0,
        recovery_seconds: float = 5.0,
    ) -> None:
        self.suspect_timeout = suspect_timeout
        self.fall_confirm_seconds = fall_confirm_seconds
        self.sedentary_seconds = sedentary_seconds
        self.recovery_seconds = recovery_seconds

        self.state = PostureState.NORMAL
        self.state_since = time.monotonic()
        self.last_motion_ts = self.state_since

    def update(
        self,
        *,
        fall_detected: bool,
        impact_detected: bool = False,
        motion_detected: bool = True,
        now: float | None = None,
    ) -> PostureState:
        now_ts = now if now is not None else time.monotonic()

        if motion_detected:
            self.last_motion_ts = now_ts

        sedentary_detected = (now_ts - self.last_motion_ts) >= self.sedentary_seconds

        if self.state == PostureState.NORMAL:
            if impact_detected or fall_detected:
                self._transition(PostureState.SUSPECT_FALL, now_ts)
            elif sedentary_detected:
                self._transition(PostureState.SEDENTARY, now_ts)
            return self.state

        if self.state == PostureState.SUSPECT_FALL:
            elapsed = now_ts - self.state_since
            if fall_detected and elapsed >= self.fall_confirm_seconds:
                self._transition(PostureState.FALLEN, now_ts)
            elif not fall_detected and elapsed >= self.suspect_timeout:
                self._transition(PostureState.NORMAL, now_ts)
            return self.state

        if self.state == PostureState.FALLEN:
            elapsed = now_ts - self.state_since
            if not fall_detected and elapsed >= self.recovery_seconds:
                self._transition(PostureState.NORMAL, now_ts)
            return self.state

        if self.state == PostureState.SEDENTARY:
            if not sedentary_detected:
                self._transition(PostureState.NORMAL, now_ts)
            return self.state

        return self.state

    def _transition(self, new_state: PostureState, now: float) -> None:
        self.state = new_state
        self.state_since = now
