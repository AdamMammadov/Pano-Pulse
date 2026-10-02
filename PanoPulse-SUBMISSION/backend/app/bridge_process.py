"""
PanoPulse — bridge process (Modbus CLIENT)
-------------------------------------------------
This process connects, as a real Modbus TCP CLIENT, to the virtual
MPR-53CS and ABB TVOC-2 devices exposed by device_process.py, and
writes the results into the field_gateway_state SQLite table for
main.py to read safely (plain sqlite3, no pymodbus involved there).

History: the first version used pymodbus's async client and hung
unpredictably in this environment (see device_process.py's own
docstring). Team member Lala Shirinli independently diagnosed and
fixed two real, separate issues through her own testing:
  1. The async pymodbus client was unreliable here — replaced with
     the synchronous pyModbusTCP client (auto_open=True, timeout=2.0),
     which has run reliably in repeated tests (failed=0).
  2. device_process.py's original current-scaling (value * 1000) could
     exceed the uint16 register limit (65535) for realistic current
     values (e.g. 300A * 1000 = 300,000) — device_process.py now
     writes the raw current value directly (no *1000), which this
     bridge must read WITHOUT a matching /1000 (kept in sync below).

This process is intentionally minimal-dependency (pyModbusTCP + the
standard library only) — no pydantic/FastAPI import, consistent with
device_process.py's own isolation rationale.
"""
from __future__ import annotations
import sqlite3
import time
import os
from pathlib import Path

from pyModbusTCP.client import ModbusClient

DB_PATH = Path(os.environ.get("PANOPULSE_DB_PATH", str(Path(__file__).parent.parent / "panopulse.db")))
POLL_INTERVAL_S = 2

HOST = "127.0.0.1"
MPR_PORT, TVOC_PORT = 5031, 5032
MPR_REG_L1 = 6                              # L1/L2/L3 occupy 6, 8, 10
TVOC_REG_TRIP1_LOW, TVOC_REG_SYSTEM_STATE = 100, 1300

SCHEMA = """
CREATE TABLE IF NOT EXISTS field_gateway_state (
    cabinet_id TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    current_l1 REAL, current_l2 REAL, current_l3 REAL,
    arc_trip INTEGER, arc_system_state INTEGER, link_ok INTEGER
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def poll_once(mpr_client: ModbusClient, tvoc_client: ModbusClient) -> dict:
    """One real Modbus round-trip per device. Returns link_ok truthfully
    based on whether BOTH reads actually succeeded this cycle — this
    matters because main.py only trusts a row when link_ok=1, and a
    hardcoded 1 would silently mask real communication failures."""
    result = {"current_l1": None, "current_l2": None, "current_l3": None,
              "arc_trip": None, "arc_system_state": None, "link_ok": 0}
    try:
        if not mpr_client.is_open:
            mpr_client.open()
        regs = mpr_client.read_holding_registers(MPR_REG_L1, 5)
        mpr_ok = regs is not None
        if mpr_ok:
            # NOTE: no /1000 here — device_process.py writes the raw
            # current value directly (see module docstring). If that
            # ever changes, this must change with it.
            result["current_l1"] = regs[0]
            result["current_l2"] = regs[2]
            result["current_l3"] = regs[4]
        else:
            mpr_client.close()

        if not tvoc_client.is_open:
            tvoc_client.open()
        trip = tvoc_client.read_holding_registers(TVOC_REG_TRIP1_LOW, 1)
        state = tvoc_client.read_holding_registers(TVOC_REG_SYSTEM_STATE, 1)
        tvoc_ok = trip is not None and state is not None
        if tvoc_ok:
            result["arc_trip"] = trip[0]
            result["arc_system_state"] = state[0]
        else:
            tvoc_client.close()

        result["link_ok"] = 1 if (mpr_ok and tvoc_ok) else 0
    except Exception:
        result["link_ok"] = 0
    return result


def start_bridge():
    conn = get_db()
    mpr_client = ModbusClient(host=HOST, port=MPR_PORT, auto_open=True, auto_close=False, timeout=2.0)
    tvoc_client = ModbusClient(host=HOST, port=TVOC_PORT, auto_open=True, auto_close=False, timeout=2.0)
    print(f"[bridge] started, polling every {POLL_INTERVAL_S}s, writing to {DB_PATH}", flush=True)

    success, failed = 0, 0
    while True:
        data = poll_once(mpr_client, tvoc_client)
        if data["link_ok"]:
            success += 1
        else:
            failed += 1
        print(f"[bridge] L1={data['current_l1']} trip={data['arc_trip']} link_ok={data['link_ok']} "
              f"| success={success} failed={failed}", flush=True)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO field_gateway_state "
                "(cabinet_id, ts, current_l1, current_l2, current_l3, arc_trip, arc_system_state, link_ok) "
                "VALUES ('AG-001', ?, ?, ?, ?, ?, ?, ?)",
                (time.time(), data["current_l1"], data["current_l2"], data["current_l3"],
                 data["arc_trip"], data["arc_system_state"], data["link_ok"]),
            )
            conn.commit()
        except Exception as e:
            print(f"[bridge] db write error: {e}", flush=True)
        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    start_bridge()
