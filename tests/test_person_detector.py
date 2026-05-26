from vision.person_detector import PersonDetector


def _detector(visibility_threshold: float = 0.6, min_visible_keypoints: int = 10) -> PersonDetector:
    detector = object.__new__(PersonDetector)
    detector.visibility_threshold = visibility_threshold
    detector.min_visible_keypoints = min_visible_keypoints
    return detector


def _landmarks(default_visibility: float = 0.8) -> list[dict[str, float]]:
    return [{"visibility": default_visibility} for _ in range(33)]


def test_has_person_requires_important_keypoint_visibility_average():
    detector = _detector()
    landmarks = _landmarks()
    for idx in (0, 11, 12, 23, 24, 25, 26, 27, 28):
        landmarks[idx]["visibility"] = 0.2

    assert detector.has_person(landmarks) is False


def test_has_person_accepts_visible_count_and_important_average():
    detector = _detector()
    landmarks = _landmarks()

    assert detector.has_person(landmarks) is True
