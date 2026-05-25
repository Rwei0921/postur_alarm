"""Play one long buzzer tone for five seconds."""

from __future__ import annotations

import argparse
import importlib
import time


BUZZER_PIN = 17
DURATION_SECONDS = 5.0
FREQUENCY_HZ = 2000.0


def run_buzzer(simulate: bool = False) -> None:
    print(f"Buzzer long tone: GPIO {BUZZER_PIN}, {FREQUENCY_HZ:.0f}Hz, {DURATION_SECONDS:.0f}s")

    if simulate:
        print("SIMULATE: buzzer ON")
        time.sleep(0.01)
        print("SIMULATE: buzzer OFF")
        return

    try:
        gpiozero = importlib.import_module("gpiozero")
        PWMOutputDevice = getattr(gpiozero, "PWMOutputDevice")
        buzzer = PWMOutputDevice(BUZZER_PIN, frequency=FREQUENCY_HZ)
    except Exception as exc:
        raise RuntimeError(
            "Unable to initialize buzzer GPIO. Try `sudo apt-get install -y python3-lgpio` "
            "and run inside the project virtualenv."
        ) from exc

    try:
        buzzer.value = 0.5
        time.sleep(DURATION_SECONDS)
    finally:
        buzzer.value = 0.0
        buzzer.close()
        print("Buzzer test finished")


def main() -> None:
    parser = argparse.ArgumentParser(description="Play one five-second buzzer tone.")
    parser.add_argument("--simulate", action="store_true", help="Print actions without using GPIO")
    args = parser.parse_args()
    run_buzzer(simulate=args.simulate)


if __name__ == "__main__":
    main()
