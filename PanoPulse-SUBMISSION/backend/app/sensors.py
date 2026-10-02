"""
PanoPulse — synthetic sensor layer
------------------------------------
Generates data shaped exactly like the real channels this project
integrates against, per Grid Up Hackathon "Sağlanacak Girdiler":

  - Current : secondary mA -> primary A via fixed multiplier
              (matches "İstenen Veriler.xlsx": 6000x, 15-min steps)
  - ARC     : ABB TVOC-2 Modbus registers (trip / system state / link)
  - PD      : Techimp HFCT-class partial-discharge analyzer output
  - Env     : wireless temperature (ambient + surface) / humidity node

No real ADM/GDZ data is used or required — organizers confirmed
(kickoff call, 10 Sep) that only synthetic/sample data is provided,
since real field data cannot be shared under KVKK.

Each cabinet can be driven through a `Scenario` so the dashboard can
demo normal vs. anomalous behaviour live, as the brief requires:
"örnek normal ve anormal çalışma senaryoları".
"""
from __future__ import annotations
import math
import random
from datetime import datetime, timedelta, timezone
from .models import Scenario, Phase


class CabinetSimulator:
    """Deterministic-ish, seedable synthetic twin of one AG pano / OG
    hücrə. `advance()` moves the simulated clock forward one step and
    returns raw readings for every channel."""

    def __init__(self, cabinet_id: str, seed: int | None = None):
        self.cabinet_id = cabinet_id
        self.rng = random.Random(seed or hash(cabinet_id) & 0xFFFF)
        self.t = datetime.now(timezone.utc)
        self.scenario = Scenario.NORMAL
        self.scenario_age_s = 0
        # baseline operating point, varies per cabinet so a fleet of
        # 100+ doesn't look like clones of each other
        self.base_load_A = self.rng.uniform(180, 420)
        self.base_temp_C = self.rng.uniform(22, 30)
        self.base_humidity = self.rng.uniform(35, 55)

    def set_scenario(self, scenario: Scenario):
        self.scenario = scenario
        self.scenario_age_s = 0

    # ---- per-channel generators -------------------------------------------------

    def _diurnal_load_A(self) -> float:
        hour = self.t.hour + self.t.minute / 60
        # two peaks: morning + evening, matches typical LV feeder shape
        shape = 0.55 + 0.30 * math.sin((hour - 8) / 24 * 2 * math.pi) \
                     + 0.20 * math.sin((hour - 19) / 24 * 2 * math.pi)
        noise = self.rng.uniform(-0.05, 0.05)
        return max(20.0, self.base_load_A * (shape + noise))

    def current_A(self, phase_offset: float = 0.0) -> float:
        val = self._diurnal_load_A() * (1 + phase_offset)
        if self.scenario == Scenario.OVERLOAD:
            # gradual ramp — loose connection heating up over time
            ramp = min(1.8, 1.0 + self.scenario_age_s / 600)
            val *= ramp
        return round(val, 1)

    def surface_temp_C(self, current_A: float) -> float:
        # surface temp tracks current with lag + ambient baseline —
        # this coupling is exactly what the challenge asks teams to
        # evaluate jointly ("akım ile yüzey sıcaklık... birlikte
        # değerlendirilmesi")
        coupling = (current_A / max(self.base_load_A, 1)) ** 1.6
        val = self.base_temp_C + 18 * coupling + self.rng.uniform(-0.8, 0.8)
        if self.scenario == Scenario.OVERLOAD:
            val += min(35, self.scenario_age_s / 20)
        return round(val, 1)

    def humidity_pct(self) -> float:
        val = self.base_humidity + 6 * math.sin(self.t.hour / 24 * 2 * math.pi) \
              + self.rng.uniform(-2, 2)
        if self.scenario == Scenario.INSULATION:
            val += min(30, self.scenario_age_s / 120)
        return round(max(15, min(98, val)), 1)

    def pd_reading(self) -> tuple[float, float]:
        magnitude = self.rng.uniform(2, 15)     # pC, background noise floor
        pulses = self.rng.uniform(0, 3)
        if self.scenario == Scenario.INSULATION:
            growth = min(1, self.scenario_age_s / 1800)
            magnitude += 180 * growth
            pulses += 40 * growth
        return round(magnitude, 1), round(pulses, 1)

    def arc_state(self) -> tuple[bool, int, bool, bool]:
        trip = self.scenario == Scenario.ARC_FLASH and self.scenario_age_s > 5
        system_state = 0 if not trip else 2  # mirrors TVOC-2 "System state" register
        link_ok = not (self.scenario == Scenario.SENSOR_FAULT and self.scenario_age_s > 10)
        sensor_ok = link_ok
        return trip, system_state, link_ok, sensor_ok

    # ---- public API ---------------------------------------------------------

    def advance(self, step_seconds: int = 60) -> dict:
        self.t += timedelta(seconds=step_seconds)
        self.scenario_age_s += step_seconds

        currents = {}
        offsets = {Phase.L1: 0.0, Phase.L2: -0.03, Phase.L3: 0.02}
        for phase, off in offsets.items():
            A = self.current_A(off)
            if self.scenario == Scenario.SENSOR_FAULT and phase == Phase.L1 \
                    and self.scenario_age_s > 10:
                A = 0.0  # channel goes silent
            mA = round(A / 6000 * 1000, 2)  # invert the sheet's own formula
            currents[phase.value] = {"secondary_mA": mA, "primary_A": A}

        surf = self.surface_temp_C(currents[Phase.L1.value]["primary_A"])
        ambient = round(self.base_temp_C + self.rng.uniform(-1, 1), 1)
        humidity = self.humidity_pct()
        pd_mag, pd_pulses = self.pd_reading()
        trip, sys_state, link_ok, sensor_ok = self.arc_state()

        return {
            "timestamp": self.t,
            "current": currents,
            "surface_temp_C": surf,
            "ambient_temp_C": ambient,
            "humidity_pct": humidity,
            "pd_magnitude_pC": pd_mag,
            "pd_pulses_per_cycle": pd_pulses,
            "arc_trip": trip,
            "arc_system_state": sys_state,
            "arc_link_ok": link_ok,
            "arc_sensor_ok": sensor_ok,
        }
