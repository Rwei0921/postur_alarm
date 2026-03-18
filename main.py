"""Main application loop for posture alarm."""

from __future__ import annotations

import importlib
import time

import config
from alert.buzzer_led import BuzzerLED
from alert.notifier_line import LineNotifier
from alert.notifier_telegram import TelegramNotifier
from core.state_machine import PostureState, PostureStateMachine
from core.utils import setup_logger
from sensors.imu_mpu6050 import IMU_MPU6050
from storage.db_sqlite import EventDB
from storage.reporter import Reporter
from ui.overlay import Overlay
from vision.camera import Camera
from vision.fall_classifier import FallClassifier
from vision.person_detector import PersonDetector
from vision.pose_estimator import PoseEstimator


def _load_cv2():
    return importlib.import_module("cv2")


def run() -> None:
    logger = setup_logger()

    cam = Camera(
        config.CAMERA_SOURCE,
        config.CAMERA_WIDTH,
        config.CAMERA_HEIGHT,
        backend=config.CAMERA_BACKEND,
        warmup_frames=config.CAMERA_WARMUP_FRAMES,
        read_retry=config.CAMERA_READ_RETRY,
    )
    person_detector = PersonDetector(
        visibility_threshold=config.POSE_VISIBILITY_THRESHOLD,
        min_visible_keypoints=config.MIN_VISIBLE_KEYPOINTS,
        min_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MP_MIN_TRACKING_CONFIDENCE,
    )
    pose_estimator = PoseEstimator(
        static_image_mode=config.MP_STATIC_IMAGE_MODE,
        model_complexity=config.MP_MODEL_COMPLEXITY,
        min_detection_confidence=config.MP_MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MP_MIN_TRACKING_CONFIDENCE,
    )
    fall_classifier = FallClassifier(
        angle_threshold_deg=config.FALL_TRUNK_ANGLE_THRESHOLD_DEG,
        hip_shoulder_diff_threshold=config.FALL_HIP_SHOULDER_DIFF_THRESHOLD,
        speed_threshold=config.FALL_SPEED_THRESHOLD,
    )
    state_machine = PostureStateMachine(
        suspect_timeout=config.SUSPECT_FALL_TIMEOUT,
        fall_confirm_seconds=config.FALL_CONFIRM_SECONDS,
        sedentary_seconds=config.SEDENTARY_SECONDS,
        recovery_seconds=config.FALL_RECOVERY_SECONDS,
    )
    imu = IMU_MPU6050(simulate=config.SIMULATE_IMU, shock_threshold_g=config.IMU_SHOCK_THRESHOLD_G)

    buzzer = BuzzerLED(simulate=config.SIMULATE_GPIO)
    line = LineNotifier(config.LINE_NOTIFY_TOKEN)
    telegram = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    db = EventDB(config.DB_PATH)
    reporter = Reporter(config.DB_PATH, str(config.REPORT_DIR))
    overlay = Overlay()

    cv2 = None
    if config.SHOW_WINDOW:
        cv2 = _load_cv2()

    previous_state = state_machine.state
    read_failures = 0
    logger.info("posture_alarm started")

    try:
        while True:
            ok, frame = cam.read_frame()
            if not ok:
                read_failures += 1
                if read_failures % 10 == 0:
                    logger.warning(
                        "camera frame unavailable (%s/%s)",
                        read_failures,
                        config.CAMERA_MAX_READ_FAILURES,
                    )
                if read_failures >= config.CAMERA_MAX_READ_FAILURES:
                    logger.warning("camera frame unavailable, stopping loop")
                    break
                time.sleep(0.05)
                continue
            read_failures = 0

            landmarks = pose_estimator.extract_landmarks(frame)
            person_present = person_detector.has_person(landmarks) if landmarks else False

            fall_detected = False
            hip_speed = 0.0
            if person_present:
                fall_detected, features = fall_classifier.classify(landmarks)
                hip_speed = features.hip_speed

            motion_detected = hip_speed > 0.02 if person_present else False
            impact_detected = imu.detect_impact()

            state = state_machine.update(
                fall_detected=fall_detected,
                impact_detected=impact_detected,
                motion_detected=motion_detected,
            )

            if state != previous_state:
                logger.info("state changed: %s -> %s", previous_state, state)
                db.log_event(
                    event_type="state_change",
                    state=state.value,
                    payload={"previous_state": previous_state.value},
                )
                previous_state = state

            if state == PostureState.FALLEN:
                buzzer.alert_on()
                db.log_event(event_type="fall", state=state.value, payload={"impact": impact_detected})
                alert_msg = "Posture alarm: fall detected"
                line.send(alert_msg)
                telegram.send(alert_msg)
            else:
                buzzer.alert_off()

            frame = overlay.draw_status(frame, state.value, warning=state == PostureState.FALLEN)
            if landmarks:
                frame = overlay.draw_landmarks(frame, landmarks)
            if state == PostureState.FALLEN:
                frame = overlay.draw_alert(frame, "FALL DETECTED")

            if config.SHOW_WINDOW and cv2 is not None:
                cv2.imshow("posture_alarm", frame)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break

            time.sleep(0.01)

    finally:
        cam.release()
        pose_estimator.close()
        person_detector.close()
        imu.close()
        buzzer.close()
        db.close()
        if cv2 is not None:
            cv2.destroyAllWindows()

        # Keep reporter instantiated and available for external scheduling/use.
        _ = reporter
        logger.info("posture_alarm stopped")


if __name__ == "__main__":
    run()
