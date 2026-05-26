# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-26
**Commit:** 9258dff
**Branch:** master

## OVERVIEW

Raspberry Pi posture alarm demo in Python. Camera frames go through MediaPipe Pose, rule-based fall classification, state transitions, GPIO buzzer/LED, LINE/Discord notifications, SQLite logging, CSV reporting, and OpenCV overlays.

## STRUCTURE

```text
D:\posture_alarm/
├── main.py                 # Runtime wiring and event loop
├── config.py               # Environment-driven constants only
├── mark_bed_roi.py         # Standalone rectangular bed ROI marker
├── setup_demo.py           # Interactive creator for demo.env
├── run_demo.sh             # Loads demo.env then runs main.py
├── install_rpi.sh          # Raspberry Pi setup helper
├── posture_alarm.service   # systemd service template
├── posture_alarm.env.example
├── alert/                  # GPIO + outbound notifier boundaries
├── core/                   # State machine, timestamps, logging helpers
├── storage/                # SQLite event DB and daily CSV reports
├── ui/                     # OpenCV overlay drawing only
├── vision/                 # Camera, MediaPipe, fall classifier pipeline
├── tests/                  # Hardware-free pytest suite
└── .github/agents/accuracy.agent.md
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Runtime orchestration | `main.py` | Instantiates every boundary class; pass config values here. |
| Environment defaults | `config.py` | Keep all `os.getenv()` parsing centralized here. |
| Fall tuning | `vision/fall_classifier.py`, `core/state_machine.py`, `TUNING_GUIDE.md` | Also read `.github/agents/accuracy.agent.md`. |
| Camera access | `vision/camera.py` | Supports OpenCV and Raspberry Pi camera paths. |
| MediaPipe pose | `vision/pose_estimator.py`, `vision/person_detector.py` | Optional dependency boundary. |
| GPIO alarm | `alert/buzzer_led.py`, `test_bz_led.py`, `test_bz_long.py` | BCM pins: buzzer GPIO 17, LED GPIO 27. |
| LINE/Discord | `alert/notifier_line.py`, `alert/notifier_discord.py`, `test_notify.py` | Return `False` on missing config or request failures. |
| Persistence | `storage/db_sqlite.py`, `storage/reporter.py` | Events table is created lazily; payloads are JSON strings. |
| Overlay changes | `ui/overlay.py` | Draw helpers load `cv2` lazily. |
| Demo setup | `setup_demo.py`, `demo.env`, `run_demo.sh` | `demo.env` can contain secrets; do not commit it. |
| Unit tests | `tests/` | Deterministic, no real camera/GPIO/GUI/network. |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `run` | function | `main.py` | Main loop, signal handling, module wiring, alert fanout. |
| `_interactive_mark_bed_roi` | function | `main.py` | 4-point polygon ROI marking at startup/manual `m`. |
| `_in_bed_roi` | function | `main.py` | Suppresses fall posture inside bed ROI unless fall event exists. |
| `PostureState` | enum | `core/state_machine.py` | `NORMAL`, `SUSPECT_FALL`, `FALLEN`, `SEDENTARY`. |
| `PostureStateMachine` | class | `core/state_machine.py` | Time-based transition rules with injectable `now`. |
| `FallFeatures` | dataclass | `vision/fall_classifier.py` | Classifier diagnostics returned with decisions. |
| `FallClassifier` | class | `vision/fall_classifier.py` | Trunk angle, hip drop/speed, event window, smoothing score. |
| `Camera` | class | `vision/camera.py` | Runtime camera abstraction. |
| `PersonDetector` | class | `vision/person_detector.py` | Landmark visibility/person-present gate. |
| `PoseEstimator` | class | `vision/pose_estimator.py` | MediaPipe landmark extraction. |
| `BuzzerLED` | class | `alert/buzzer_led.py` | Fail-soft GPIO output; simulation fallback. |
| `LineNotifier` | class | `alert/notifier_line.py` | LINE Messaging API push integration. |
| `DiscordNotifier` | class | `alert/notifier_discord.py` | Discord webhook integration. |
| `EventDB` | class | `storage/db_sqlite.py` | SQLite event insertion and recent fetches. |
| `Reporter` | class | `storage/reporter.py` | Daily CSV export from event DB. |
| `Overlay` | class | `ui/overlay.py` | Status, alert, landmarks, bed ROI rendering. |

## CONVENTIONS

- Use `from __future__ import annotations` in Python modules.
- Imports are standard library, third-party, local packages; keep local imports absolute from repo root.
- Use double quotes, 4-space indentation, short module docstrings, sparse comments.
- Public functions/methods and important locals should be typed when clear.
- Use `dataclass` for small result containers and `Enum` for finite state sets.
- Keep dynamic library boundaries lazy: `cv2`, `numpy`, `picamera2`, `requests`, and GPIO imports should stay inside boundary helpers where practical.
- Keep config values in `config.py`; pass them into constructors from `main.py`.
- Hardware, network, camera, and GUI failures should fail soft at the boundary when the app can keep running.
- Core logic should not silently swallow actionable exceptions.
- SQLite event payloads must remain JSON-serializable; preserve existing schema unless migration is explicitly requested.

## ANTI-PATTERNS (THIS PROJECT)

- Do not add dependencies casually; `requirements.txt` is intentionally small.
- Do not move environment parsing out of `config.py`.
- Do not replace the rule-based fall pipeline with a new architecture unless requested.
- Do not rename top-level modules or public classes without updating all imports.
- Do not make tests require a real camera, GPIO, OpenCV GUI, LINE, Discord, or network access.
- Do not modify test assertions without a clear correctness reason; tests document behavior.
- Do not skip the import-health check after wiring, config-loading, or optional-import changes.
- Do not commit `demo.env`; it can contain LINE tokens and Discord webhooks.

## UNIQUE STYLES

- Simulation-friendly defaults matter: code should run in non-Raspberry-Pi environments where possible.
- State-machine tests inject timestamps instead of sleeping.
- Classifier tests construct synthetic landmark lists and assert feature values, not just booleans.
- Notifier tests monkeypatch `_load_requests`; keep that seam available.
- SQLite tests use `:memory:` or `tmp_path`; storage code creates parent directories itself.
- Alert messages and display timestamps use Taiwan local formatting through `core.utils`.
- `main.py` supports both rectangle and 4-point polygon bed ROI; rectangle values remain for backward compatibility.

## COMMANDS

```bash
pip install -r requirements.txt
python main.py
python mark_bed_roi.py
python mark_bed_roi.py --run-main
python setup_demo.py
python -m pytest tests -q
python -m pytest tests/test_state_machine.py -q
python -m pytest tests -k sedentary -q
python test_bz_led.py --simulate --pwm-buzzer
python test_notify.py
```

Import-health check after wiring/import changes:

```bash
python -c "from vision.camera import Camera; from vision.person_detector import PersonDetector; from vision.pose_estimator import PoseEstimator; from vision.fall_classifier import FallClassifier; from core.state_machine import PostureStateMachine; from core.utils import setup_logger; from alert.buzzer_led import BuzzerLED; from alert.notifier_line import LineNotifier; from alert.notifier_discord import DiscordNotifier; from storage.db_sqlite import EventDB; from storage.reporter import Reporter; from ui.overlay import Overlay; print('All imports OK')"
```

## VALIDATION DEFAULTS

- Small logic change: run the narrowest relevant test first.
- Shared core/config/vision changes: run `python -m pytest tests -q`.
- Wiring or optional import changes: run the import-health check too.
- Hardware scripts may need Raspberry Pi GPIO permissions or `python3-lgpio`; report blockers instead of guessing.
- There is no configured linter, formatter, typechecker, build system, Makefile, tox/nox, pyproject, or CI workflow in this repo.

## LOCATION DECISION

Only this root file is warranted now. Source counts are small (`vision/` 5 code files, `tests/` 7, `alert/` 4, `core/` 3, `storage/` 3, `ui/` 2), and no subdirectory has local config or enough unique rules to justify a child `AGENTS.md` without repeating parent guidance.

## NOTES

- Current workspace includes a `.venv/`; exclude it from repository analysis.
- `rg` was unavailable in the current Windows environment during generation; use PowerShell/search fallback if needed.
- The working tree was already dirty when this file was regenerated; avoid reverting unrelated changes.
