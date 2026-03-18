"""MPU6050 wrapper with simulation fallback."""

from __future__ import annotations

import importlib
import math
import random
import time
from dataclasses import dataclass


@dataclass
class IMUReading:
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    timestamp: float


class IMU_MPU6050:
    def __init__(
        self,
        simulate: bool = True,
        bus_id: int = 1,
        address: int = 0x68,
        shock_threshold_g: float = 1.8,
        seed: int | None = None,
    ) -> None:
        self.simulate = simulate
        self.bus_id = bus_id
        self.address = address
        self.shock_threshold_g = shock_threshold_g
        self._rng = random.Random(seed)

        self._bus = None
        if not self.simulate:
            try:
                SMBus = getattr(importlib.import_module("smbus2"), "SMBus")
                self._bus = SMBus(self.bus_id)
            except Exception:
                self.simulate = True

    def read(self) -> IMUReading:
        if self.simulate:
            return self._read_simulated()
        return self._read_hardware()

    def detect_impact(self, reading: IMUReading | None = None) -> bool:
        reading = reading or self.read()
        acc_mag = math.sqrt(reading.ax * reading.ax + reading.ay * reading.ay + reading.az * reading.az)
        return abs(acc_mag - 1.0) >= self.shock_threshold_g

    def close(self) -> None:
        if self._bus is not None:
            self._bus.close()

    def _read_simulated(self) -> IMUReading:
        noise = lambda scale: self._rng.uniform(-scale, scale)
        shock = 0.0
        if self._rng.random() < 0.01:
            shock = self._rng.uniform(-2.5, 2.5)
        return IMUReading(
            ax=noise(0.05) + shock,
            ay=noise(0.05),
            az=1.0 + noise(0.08),
            gx=noise(0.8),
            gy=noise(0.8),
            gz=noise(0.8),
            timestamp=time.monotonic(),
        )

    def _read_hardware(self) -> IMUReading:
        # Fallback structure for real I2C mode. In production, decode device registers here.
        return IMUReading(0.0, 0.0, 1.0, 0.0, 0.0, 0.0, time.monotonic())
