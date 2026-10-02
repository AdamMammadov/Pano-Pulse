import { useEffect, useState } from "react";
import { api } from "../api";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

export default function ForensicsTimeline({ cabinetId }) {
  const [events, setEvents] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const load = () => api.getForensics(cabinetId).then(setEvents).catch(() => {});
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [cabinetId, open]);

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginTop: 16 }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{ background: "none", border: "none", color: "var(--text)", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, padding: 0, fontSize: 12 }}
      >
        <span style={{ color: "var(--text-dim)" }}>{open ? "▾" : "▸"}</span>
        🔍 Incident Timeline / Digital Forensics {events.length > 0 && `(${events.length})`}
      </button>

      {open && (
        <div style={{ marginTop: 12 }}>
          {events.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--text-dim)" }}>No past incidents recorded for this cabinet yet.</div>
          ) : (
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              {events.map((e, i) => {
                const key = `${e.timestamp}-${i}`;
                const isOpen = expanded === key;
                return (
                  <div key={key} style={{ borderLeft: `2px solid ${RISK_COLOR[e.risk_label]}`, paddingLeft: 12, marginBottom: 10 }}>
                    <button
                      onClick={() => setExpanded(isOpen ? null : key)}
                      style={{ background: "none", border: "none", color: "var(--text)", cursor: "pointer", width: "100%", textAlign: "left", padding: 0 }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                        <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>
                          {new Date(e.timestamp).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                        <span style={{ color: RISK_COLOR[e.risk_label], fontFamily: "var(--font-mono)" }}>
                          {e.risk_score.toFixed(0)} · {RISK_LABEL_EN[e.risk_label]}
                        </span>
                      </div>
                      <div style={{ fontSize: 13, marginTop: 2 }}>{e.likely_cause}</div>
                    </button>

                    {isOpen && (
                      <div style={{ marginTop: 8, background: "var(--panel-2)", borderRadius: 6, padding: 10, fontSize: 11 }}>
                        <div style={{ color: "var(--text-dim)", marginBottom: 6 }}>
                          Health score at the time: <span style={{ color: "var(--text)" }}>{e.health_score?.toFixed(1) ?? "—"}/100</span>
                        </div>
                        <div style={{ color: "var(--text-dim)", marginBottom: 6 }}>Evidence (contributing factors):</div>
                        <ul style={{ margin: "0 0 8px", paddingLeft: 16 }}>
                          {e.contributing_factors.map((f, fi) => <li key={fi}>{f}</li>)}
                        </ul>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>
                          <span>L1/L2/L3: {e.current.L1.primary_A}/{e.current.L2.primary_A}/{e.current.L3.primary_A} A</span>
                          <span>Surface: {e.surface_temp_C}°C</span>
                          <span>Humidity: {e.humidity_pct}%</span>
                          <span>PD: {e.pd_magnitude_pC}pC</span>
                          <span>ARC trip: {e.arc_trip ? "yes" : "no"}</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
