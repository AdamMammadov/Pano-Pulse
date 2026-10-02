import { RISK_COLOR } from "../riskStyle";
import { api, API_BASE } from "../api";

const SYSTEM_LOGS = [
  { icon: "🟢", text: "[SYSTEM] Modbus RTU/TCP connection active (:5020)", color: "var(--teal)" },
  { icon: "🔵", text: "[INFO] Telemetry OK · 120 cabinets live", color: "var(--info)" },
];

export default function AlertsFeed({ alerts, onAck }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          padding: "16px 16px 12px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span style={{ fontSize: 12, color: "var(--text-dim)" }}>alert feed · {alerts.length}</span>
        <a
          href={api.alertsExportUrl()}
          style={{ fontSize: 11, color: "var(--copper)", textDecoration: "none" }}
        >
          Download CSV
        </a>
      </div>

      <div style={{ borderBottom: "1px solid var(--border)" }}>
        {SYSTEM_LOGS.map((log, i) => (
          <div key={i} style={{ padding: "8px 16px", fontSize: 11, fontFamily: "var(--font-mono)", color: log.color, opacity: 0.8 }}>
            {log.icon} {log.text}
          </div>
        ))}
      </div>

      <div style={{ overflowY: "auto", flex: 1 }}>
        {alerts.length === 0 && (
          <div style={{ padding: 16, fontSize: 13, color: "var(--text-dim)" }}>
            No alerts yet.
          </div>
        )}
        {alerts.map((a) => (
          <div
            key={a.id}
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid var(--border)",
              opacity: a.acknowledged ? 0.5 : 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_COLOR[a.severity], flexShrink: 0 }} />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                {a.cabinet_id}
              </span>
            </div>
            <div style={{ fontSize: 13, marginBottom: 6 }}>{a.likely_cause}</div>
            <div style={{ fontSize: 10, color: "var(--text-dim)", marginBottom: 6, wordBreak: "break-word", lineHeight: 1.5 }}>
              {a.channels?.join(" · ")}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {!a.acknowledged && (
                <button
                  onClick={() => onAck(a.id)}
                  style={{
                    background: "transparent",
                    border: "1px solid var(--border)",
                    borderRadius: 4,
                    color: "var(--text-dim)",
                    fontSize: 11,
                    padding: "4px 8px",
                  }}
                >
                  acknowledge
                </button>
              )}
              <a
                href={`${API_BASE}/cabinets/${a.cabinet_id}/report.pdf`}
                style={{ fontSize: 11, color: "var(--copper)", textDecoration: "none" }}
              >
                📄 PDF report
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
