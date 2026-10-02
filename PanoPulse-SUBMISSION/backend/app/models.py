"""
PanoPulse — data models
------------------------
Schemas for a single OG hücrə / AG pano (cabinet) and everything the
monitoring engine produces about it: raw sensor readings, fused risk
scores, and alerts.

Design note: every cabinet is identified by `cabinet_id` so the same
engine scales from 1 to 1000s of cabinets (challenge requires >=100).
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Phase(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Scenario(str, Enum):
    """Demo scenarios the jury can trigger live. See challenge brief:
    'örnek normal ve anormal çalışma senaryoları' must be shown."""
    NORMAL = "normal"
    OVERLOAD = "overload"          # gradual overcurrent + heating (loose connection)
    ARC_FLASH = "arc_flash"        # sudden ABB TVOC-2 trip
    INSULATION = "insulation"      # rising humidity + PD activity (slow degradation)
    SENSOR_FAULT = "sensor_fault"  # a channel goes silent / out of range


class CurrentReading(BaseModel):
    timestamp: datetime
    phase: Phase
    secondary_mA: float
    multiplier: float = 6000.0
    primary_A: float


class ArcReading(BaseModel):
    """Mirrors the real ABB TVOC-2 Modbus registers we integrate against:
    trip detector bitfield (PDU 0x64+), system state (1300), modbus
    failure (1200). We don't reinvent arc detection — TVOC-2 is already
    SIL-2 certified; we just relay and log its state."""
    timestamp: datetime
    trip_active: bool
    system_state_code: int          # 0 = OK, mirrors register 1300
    modbus_link_ok: bool             # mirrors register 1200 (failure reg)
    sensor_status_ok: bool


class PDReading(BaseModel):
    """Derived from Techimp HFCT-class sensors. Real HFCT output is an
    analog RF signal (1-60/80MHz) that needs a dedicated PD analyzer;
    for the hackathon we model the analyzer's typical outputs:
    discharge magnitude (pC) and pulses/cycle, which is what an
    HFCT+analyzer chain reports downstream."""
    timestamp: datetime
    discharge_magnitude_pC: float
    pulses_per_cycle: float


class EnvReading(BaseModel):
    """Wireless temp/humidity node inside the cabinet."""
    timestamp: datetime
    ambient_temp_C: float
    surface_temp_C: float           # cable/busbar surface — correlates with current
    humidity_pct: float


class CabinetSnapshot(BaseModel):
    """One fused, point-in-time view of a cabinet — what the dashboard
    and the alerting engine both consume."""
    cabinet_id: str
    timestamp: datetime
    current: dict[str, CurrentReading]   # keyed by phase
    arc: ArcReading
    pd: PDReading
    env: EnvReading
    risk_score: float = 0.0              # 0-100, fused
    risk_label: str = "normal"           # normal | watch | warning | critical
    contributing_factors: list[str] = Field(default_factory=list)
    likely_cause: Optional[str] = None


class Alert(BaseModel):
    id: str
    cabinet_id: str
    timestamp: datetime
    severity: str            # watch | warning | critical
    message: str
    likely_cause: Optional[str]
    channel: str              # dashboard | sms | whatsapp
    acknowledged: bool = False
