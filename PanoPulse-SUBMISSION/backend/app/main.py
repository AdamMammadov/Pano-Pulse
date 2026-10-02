"""
PanoPulse backend — FastAPI entrypoint
------------------------------------------
Runs entirely on-prem: no cloud SDK, no external managed DB — a local
SQLite file (storage.py) backs history and alerts so a restart doesn't
lose data. Mutating endpoints require an API key (auth.py); the
primary security boundary is still meant to be network segmentation
(OT VLAN), documented in docs/guvenlik.md.

Scalability note (brief requires >=100 modules): the FleetManager below
defaults to FLEET_SIZE cabinets. Each cabinet's live state is O(WINDOW)
floats (four rolling deques of 60 samples) — trivial for a small
on-prem box (Raspberry Pi class hardware is already enough; no GPU,
no heavy DB needed). Measured on this machine: 120 cabinets tick and
persist to SQLite well within the 5s tick budget (see docs/kalibrasyon.md).

Run locally:
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations
import asyncio
import csv
import io
import subprocess
import sqlite3
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .sensors import CabinetSimulator
from .anomaly_engine import CabinetEngine
from .alerts import AlertManager
from .models import Scenario
from .modbus_server import start_modbus_server, cabinet_base_address, REGS_PER_CABINET, MODBUS_PORT
from . import storage
from .auth import require_api_key
from .copilot import ask_copilot
from .reports import generate_incident_report

FLEET_SIZE = 120          # demonstrates the >=100 module requirement
TICK_SECONDS = 5          # real seconds between simulated steps (demo speed)
SIM_STEP_SECONDS = 60     # simulated seconds advanced per tick
FIELD_GATEWAY_FRESHNESS_S = 10  # bridge_process.py yazısı bundan köhnə olarsa "sintetik"ə qayıt


def read_field_gateway_state() -> dict | None:
    """AG-001 üçün bridge_process.py-nin yazdığı son Modbus oxumasını
    OXU — sadə, sinxron sqlite3, pymodbus-a TOXUNMUR. Körpü prosesi
    assa/dayansa belə, bu funksiya sadəcə None qaytarır, əsas tətbiq
    heç vaxt bloklanmır."""
    try:
        conn = sqlite3.connect(storage.DB_PATH, timeout=1)
        row = conn.execute(
            "SELECT ts, current_l1, current_l2, current_l3, arc_trip, arc_system_state, link_ok "
            "FROM field_gateway_state WHERE cabinet_id='AG-001'"
        ).fetchone()
        conn.close()
        if not row:
            return None
        ts, l1, l2, l3, trip, state, link_ok = row
        if time.time() - ts > FIELD_GATEWAY_FRESHNESS_S or not link_ok:
            return None
        if l1 is None:
            return None
        return {"current": {"L1": l1, "L2": l2, "L3": l3}, "arc_trip": bool(trip), "arc_system_state": state}
    except Exception:
        return None


class Cabinet:
    def __init__(self, cabinet_id: str):
        self.sim = CabinetSimulator(cabinet_id)
        self.engine = CabinetEngine(cabinet_id)
        self.history: list[dict] = []
        self.latest: dict | None = None

    async def tick(self):
        raw = self.sim.advance(SIM_STEP_SECONDS)
        data_source = "synthetic"

        if self.sim.cabinet_id == "AG-001":
            live = read_field_gateway_state()
            if live:
                for p in ("L1", "L2", "L3"):
                    a = live["current"][p]
                    raw["current"][p]["primary_A"] = a
                    raw["current"][p]["secondary_mA"] = round(a / 6000 * 1000, 2)
                raw["arc_trip"] = live["arc_trip"]
                raw["arc_system_state"] = live["arc_system_state"]
                data_source = "modbus_live"

        evaluation = self.engine.evaluate(raw)
        snapshot = {**raw, **evaluation, "cabinet_id": self.sim.cabinet_id, "data_source": data_source}
        self.latest = snapshot
        self.history.append(snapshot)
        if len(self.history) > 180:  # ~3h of 1-min samples for charts
            self.history.pop(0)
        return snapshot


class FleetManager:
    def __init__(self, size: int):
        self.cabinets = {f"AG-{i:03d}": Cabinet(f"AG-{i:03d}") for i in range(1, size + 1)}
        self.alerts = AlertManager()
        self.db = storage.get_connection()
        self.fleet_history: list[dict] = []  # flot-səviyyəli aqreqat trend (idarəetmə görünüşü)

    async def tick_all(self):
        fired = []
        batch = []
        for cab in self.cabinets.values():
            snap = await cab.tick()
            batch.append((cab.sim.cabinet_id, snap))
            alert = self.alerts.maybe_fire(cab.sim.cabinet_id, snap)
            if alert:
                storage.save_alert(self.db, alert)
                fired.append(alert)
        storage.save_snapshots_batch(self.db, batch)

        counts = self.summary()
        risks = [c.latest["risk_score"] for c in self.cabinets.values() if c.latest]
        self.fleet_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **counts,
            "avg_risk": round(sum(risks) / len(risks), 2) if risks else 0,
        })
        if len(self.fleet_history) > 180:
            self.fleet_history.pop(0)

        return fired

    def summary(self):
        counts = {"normal": 0, "watch": 0, "warning": 0, "critical": 0}
        for cab in self.cabinets.values():
            if cab.latest:
                counts[cab.latest["risk_label"]] += 1
        return counts

    def top_priority_panels(self, limit: int = 5):
        """Priority ranking is deliberately NOT the same as sorting by
        risk_score alone: a cabinet with a lower instantaneous score but
        several already-confirmed channels and a near-term forecast can
        be a higher operational priority than one with a single spikier
        reading. Weights (60/20/20) reflect that risk is still the
        dominant signal, with persistence and urgency as tie-breakers."""
        panels = []
        for cab in self.cabinets.values():
            if not cab.latest:
                continue
            snap = cab.latest
            risk = float(snap.get("risk_score", 0))

            confirmed_channels = sum(1 for t in cab.engine.trackers.values() if t.confirmed)
            persistence_score = min(100, confirmed_channels * 25)

            forecast_score = 0
            forecast = snap.get("forecast")
            if forecast:
                hours = forecast.get("hours_to_critical")
                if hours is not None:
                    if hours <= 1:
                        forecast_score = 100
                    elif hours <= 3:
                        forecast_score = 75
                    elif hours <= 6:
                        forecast_score = 50
                    elif hours <= 12:
                        forecast_score = 25

            priority_score = risk * 0.60 + persistence_score * 0.20 + forecast_score * 0.20

            panels.append({
                "cabinet_id": cab.sim.cabinet_id,
                "risk_score": round(risk, 1),
                "risk_label": snap.get("risk_label", "normal"),
                "health_score": snap.get("health_score"),
                "priority_score": round(priority_score, 1),
                "confirmed_channels": confirmed_channels,
                "forecast": forecast,
                "likely_cause": snap.get("likely_cause"),
                "timestamp": snap.get("timestamp"),
            })

        panels.sort(key=lambda x: x["priority_score"], reverse=True)
        return panels[:limit]


fleet = FleetManager(FLEET_SIZE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    fleet.alerts.log = list(reversed(storage.load_recent_alerts(fleet.db, limit=200)))

    # AG-001 üçün canlı Modbus göstərisi: tamamilə İZOLYASİYA OLUNMUŞ iki
    # köməkçi proses (bkz. device_process.py / bridge_process.py). Bunlar
    # ayrı proseslər olduğu üçün, nə qədər etibarsız olsalar da, ƏSAS
    # TƏTBİQİ HEÇ VAXT bloklaya bilməzlər — sadəcə "sintetik"ə enir.
    device_proc = subprocess.Popen([sys.executable, "-m", "app.device_process"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    bridge_proc = subprocess.Popen([sys.executable, "-m", "app.bridge_process"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for cab in fleet.cabinets.values():  # seed some live history immediately
        for _ in range(15):
            await cab.tick()

    async def loop():
        while True:
            await fleet.tick_all()
            await asyncio.sleep(TICK_SECONDS)

    tick_task = asyncio.create_task(loop())
    modbus_tasks = await start_modbus_server(fleet)  # bkz. modbus_server.py

    yield

    # --- shutdown --- (testlərin və real yenidən başlatmaların təmiz bitməsi üçün)
    for task in [tick_task, *modbus_tasks]:
        task.cancel()
    for proc in [device_proc, bridge_proc]:
        proc.terminate()


app = FastAPI(title="PanoPulse API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the on-prem dashboard's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "fleet_size": len(fleet.cabinets), "time": datetime.now(timezone.utc)}


@app.get("/fleet/summary")
def fleet_summary():
    return {"counts": fleet.summary(), "total": len(fleet.cabinets)}


@app.get("/fleet/top-priority")
def fleet_top_priority(limit: int = 5):
    """Ranked by priority_score (risk + persistence + urgency), NOT
    simply by risk_score — see FleetManager.top_priority_panels."""
    limit = max(1, min(limit, 20))
    return fleet.top_priority_panels(limit)


@app.get("/fleet/history")
def fleet_history():
    """İdarəetmə görünüşü üçün: flotun risk paylanması zaman içində necə
    dəyişib. Hər nöqtə bir tick-i (real 5 saniyə = simulyasiya 60 saniyəsi)
    təmsil edir."""
    return fleet.fleet_history


@app.get("/cabinets")
def list_cabinets():
    return [
        {
            "cabinet_id": cid,
            "risk_score": cab.latest["risk_score"] if cab.latest else 0,
            "risk_label": cab.latest["risk_label"] if cab.latest else "normal",
            "timestamp": cab.latest["timestamp"] if cab.latest else None,
            "load_A": round(sum(cab.latest["current"][p]["primary_A"] for p in ("L1", "L2", "L3")), 0) if cab.latest else 0,
        }
        for cid, cab in fleet.cabinets.items()
    ]


@app.get("/cabinets/{cabinet_id}")
def get_cabinet(cabinet_id: str):
    cab = fleet.cabinets.get(cabinet_id)
    if not cab:
        raise HTTPException(404, "cabinet not found")
    return cab.latest


@app.get("/cabinets/{cabinet_id}/history")
def get_history(cabinet_id: str):
    cab = fleet.cabinets.get(cabinet_id)
    if not cab:
        raise HTTPException(404, "cabinet not found")
    return cab.history


@app.get("/cabinets/{cabinet_id}/forensics")
def get_cabinet_forensics(cabinet_id: str):
    """Digital-forensics event timeline: every past tick where this
    cabinet was NOT normal, newest first, each with a full sensor
    snapshot — the evidence trail behind a risk score, not just the
    current number."""
    cab = fleet.cabinets.get(cabinet_id)
    if not cab:
        raise HTTPException(404, "cabinet not found")
    return list(reversed(cab.engine.forensic_events))


class ScenarioRequest(BaseModel):
    scenario: Scenario


@app.post("/cabinets/{cabinet_id}/scenario", dependencies=[Depends(require_api_key)])
def set_scenario(cabinet_id: str, body: ScenarioRequest):
    cab = fleet.cabinets.get(cabinet_id)
    if not cab:
        raise HTTPException(404, "cabinet not found")
    cab.sim.set_scenario(body.scenario)
    return {"cabinet_id": cabinet_id, "scenario": body.scenario}


@app.get("/cabinets/{cabinet_id}/report.pdf")
def get_cabinet_report(cabinet_id: str):
    cab = fleet.cabinets.get(cabinet_id)
    if not cab or not cab.latest:
        raise HTTPException(404, "cabinet not found or no data yet")
    pdf_bytes = generate_incident_report(cab.latest)
    return StreamingResponse(
        io.BytesIO(pdf_bytes), media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=panopulse_{cabinet_id}_report.pdf"},
    )


class AskRequest(BaseModel):
    question: str


@app.post("/cabinets/{cabinet_id}/ask")
def ask_cabinet(cabinet_id: str, body: AskRequest):
    cab = fleet.cabinets.get(cabinet_id)
    if not cab or not cab.latest:
        raise HTTPException(404, "cabinet not found or no data yet")
    return ask_copilot(body.question, cab.latest)


class WhatIfRequest(BaseModel):
    adjustments: dict[str, float]  # e.g. {"humidity": 20} means "+20%"


@app.post("/cabinets/{cabinet_id}/what-if")
def what_if_cabinet(cabinet_id: str, body: WhatIfRequest):
    """Read-only 'what if X changed by Y%?' projection. Never touches
    the cabinet's real detection state (see CabinetEngine.simulate_what_if
    docstring) — safe to call as many times as the operator wants."""
    cab = fleet.cabinets.get(cabinet_id)
    if not cab or not cab.latest:
        raise HTTPException(404, "cabinet not found or no data yet")
    allowed = {"current_L1", "surface_temp", "humidity", "pd_magnitude"}
    bad = set(body.adjustments) - allowed
    if bad:
        raise HTTPException(400, f"unknown channel(s): {sorted(bad)}. Allowed: {sorted(allowed)}")
    current_risk = cab.latest["risk_score"]
    current_label = cab.latest["risk_label"]
    simulated = cab.engine.simulate_what_if(cab.latest, body.adjustments)
    return {
        "cabinet_id": cabinet_id,
        "current": {"risk_score": current_risk, "risk_label": current_label},
        "simulated": simulated,
        "adjustments_applied": body.adjustments,
    }


@app.get("/modbus/register-map")
def modbus_register_map():
    """Documents the live Modbus TCP slave for the SCADA team — which
    register block belongs to which cabinet, and what each offset
    means. Mirrors the style of the MPR-53CS map ADM/GDZ shared with us."""
    field_names = [
        "risk_score_x10", "risk_label_code", "current_L1_x10", "current_L2_x10",
        "current_L3_x10", "surface_temp_x10", "ambient_temp_x10", "humidity_x10",
        "pd_magnitude_x10", "pd_pulses_x10", "arc_trip", "arc_system_state",
        "arc_link_ok", "alarm_active", "timestamp_hi", "timestamp_lo",
        "reserved", "reserved", "reserved", "reserved",
    ]
    cabinets = [
        {
            "cabinet_id": cid,
            "base_address": cabinet_base_address(i),
            "register_count": REGS_PER_CABINET,
        }
        for i, cid in enumerate(fleet.cabinets.keys(), start=1)
    ]
    return {
        "protocol": "Modbus TCP",
        "port": MODBUS_PORT,
        "function_code": 3,
        "note": "All values are x10-scaled unsigned int16 (same approach as the MPR-53CS multiplier convention)",
        "fields_in_order": field_names,
        "cabinets": cabinets[:5] + [{"...": f"+{len(cabinets)-5} more cabinets"}] if len(cabinets) > 5 else cabinets,
    }


@app.get("/alerts")
def get_alerts(limit: int = 50):
    return list(reversed(fleet.alerts.log[-limit:]))


@app.get("/alerts/export.csv")
def export_alerts_csv():
    """Uyumluluk/denetim için alert geçmişini CSV olarak indir."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "cabinet_id", "timestamp", "severity", "message", "likely_cause", "channels", "acknowledged"])
    for a in storage.load_recent_alerts(fleet.db, limit=5000):
        writer.writerow([
            a["id"], a["cabinet_id"], datetime.fromtimestamp(a["timestamp"]).isoformat(),
            a["severity"], a["message"], a["likely_cause"], "|".join(a["channels"]), a["acknowledged"],
        ])
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=panopulse_alerts.csv"},
    )


@app.post("/alerts/{alert_id}/ack", dependencies=[Depends(require_api_key)])
def ack_alert_endpoint(alert_id: str):
    for a in fleet.alerts.log:
        if a["id"] == alert_id:
            a["acknowledged"] = True
            storage.ack_alert(fleet.db, alert_id)
            return a
    raise HTTPException(404, "alert not found")
