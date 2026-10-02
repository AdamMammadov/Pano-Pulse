"""
PanoPulse — davamlılıq (persistence) qatı
--------------------------------------------
Zəiflik: əvvəlki versiya tamamilə in-memory idi — server yenidən başlasa
(elektrik kəsintisi, yenidən başlatma, çökmə), bütün tarixçə və alert
qeydləri itirilirdi. Sahə tətbiqi üçün bu qəbuledilməzdir: bir ark flaşı
alertinin auditi/sübutu itə bilməz.

Bu modul yerli SQLite faylına (on-prem, heç bir xarici DB server lazım
deyil) yazır. Dizayn qərarı: engine-in CANLI z-score pəncərəsi (son 60
nümunə) yenidən başlamada sıfırlanır — bunu gizlətmirik, sənədləşdiririk
(bkz. README) — çünki tam vəziyyət bərpası mürəkkəbliyi bu mərhələdə
faydasından artıqdır; ~1 saat ərzində pəncərə özü yenidən dolur. Amma
TARİXÇƏ VƏ ALERT-LƏR (audit üçün əsas olan hissə) tam qorunur.
"""
from __future__ import annotations
import sqlite3
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("PANOPULSE_DB_PATH", str(Path(__file__).parent.parent / "panopulse.db")))

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cabinet_id TEXT NOT NULL,
    ts REAL NOT NULL,
    risk_score REAL NOT NULL,
    risk_label TEXT NOT NULL,
    likely_cause TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshots_cabinet_ts ON snapshots(cabinet_id, ts);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    cabinet_id TEXT NOT NULL,
    ts REAL NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    likely_cause TEXT,
    channels TEXT NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts);
"""


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")  # eşzamanlı oxu/yazı üçün — on-prem tək fayl
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


@contextmanager
def cursor(conn: sqlite3.Connection):
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()


def save_snapshot(conn: sqlite3.Connection, cabinet_id: str, snapshot: dict):
    payload = json.dumps(snapshot, default=str)
    with cursor(conn) as cur:
        cur.execute(
            "INSERT INTO snapshots (cabinet_id, ts, risk_score, risk_label, likely_cause, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (cabinet_id, time.time(), snapshot["risk_score"], snapshot["risk_label"],
             snapshot.get("likely_cause"), payload),
        )


def save_snapshots_batch(conn: sqlite3.Connection, snapshots: list[tuple[str, dict]]):
    """Batched insert for a full fleet tick (120 cabinets every few seconds) —
    one commit instead of 120, so WAL checkpointing doesn't become a bottleneck."""
    now = time.time()
    rows = [
        (cid, now, s["risk_score"], s["risk_label"], s.get("likely_cause"), json.dumps(s, default=str))
        for cid, s in snapshots
    ]
    with cursor(conn) as cur:
        cur.executemany(
            "INSERT INTO snapshots (cabinet_id, ts, risk_score, risk_label, likely_cause, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )


def save_alert(conn: sqlite3.Connection, alert: dict):
    with cursor(conn) as cur:
        cur.execute(
            "INSERT OR REPLACE INTO alerts (id, cabinet_id, ts, severity, message, likely_cause, channels, acknowledged) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (alert["id"], alert["cabinet_id"], alert["timestamp"], alert["severity"],
             alert["message"], alert.get("likely_cause"), json.dumps(alert.get("channels", [])),
             int(alert.get("acknowledged", False))),
        )


def ack_alert(conn: sqlite3.Connection, alert_id: str):
    with cursor(conn) as cur:
        cur.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))


def load_recent_alerts(conn: sqlite3.Connection, limit: int = 200) -> list[dict]:
    with cursor(conn) as cur:
        rows = cur.execute(
            "SELECT id, cabinet_id, ts, severity, message, likely_cause, channels, acknowledged "
            "FROM alerts ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": r[0], "cabinet_id": r[1], "timestamp": r[2], "severity": r[3],
            "message": r[4], "likely_cause": r[5], "channels": json.loads(r[6]),
            "acknowledged": bool(r[7]),
        }
        for r in rows
    ]


def load_history(conn: sqlite3.Connection, cabinet_id: str, limit: int = 500) -> list[dict]:
    with cursor(conn) as cur:
        rows = cur.execute(
            "SELECT payload FROM snapshots WHERE cabinet_id = ? ORDER BY ts DESC LIMIT ?",
            (cabinet_id, limit),
        ).fetchall()
    return [json.loads(r[0]) for r in reversed(rows)]


def prune_old(conn: sqlite3.Connection, max_age_days: int = 30):
    """Basic retention policy so panopulse.db doesn't grow unbounded on a
    small on-prem box. Alerts are kept regardless (audit trail)."""
    cutoff = time.time() - max_age_days * 86400
    with cursor(conn) as cur:
        cur.execute("DELETE FROM snapshots WHERE ts < ?", (cutoff,))
