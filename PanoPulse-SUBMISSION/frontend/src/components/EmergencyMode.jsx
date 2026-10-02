import { RISK_COLOR } from "../riskStyle";

export default function EmergencyMode({ cabinet, onDismiss, onViewIncident, onAck, onCreateWorkOrder, workOrderSent }) {
  if (!cabinet) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "radial-gradient(circle at 50% 40%, #2A1414, #0D0808)",
        zIndex: 500,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      className="critical-flash"
    >
      <div
        style={{
          border: `3px solid ${RISK_COLOR.critical}`,
          borderRadius: 16,
          padding: "40px 56px",
          textAlign: "center",
          background: "rgba(13,8,8,0.85)",
          maxWidth: 560,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, color: RISK_COLOR.critical, letterSpacing: 2, marginBottom: 6 }}>
          🚨 CRITICAL INCIDENT
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 40, fontWeight: 700, color: "var(--text)", marginBottom: 4 }}>
          {cabinet.cabinet_id}
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 64, fontWeight: 700, color: RISK_COLOR.critical, lineHeight: 1 }}>
          {cabinet.risk_score.toFixed(0)}
        </div>
        <div style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 18 }}>RISK SCORE</div>

        <div style={{ fontSize: 15, color: "var(--text)", marginBottom: 10, textTransform: "uppercase", letterSpacing: 0.5 }}>
          {cabinet.likely_cause}
        </div>

        {cabinet.arc_trip && (
          <div style={{ fontSize: 13, color: RISK_COLOR.critical, fontWeight: 700, marginBottom: 18 }}>
            ABB TVOC-2 TRIP: ACTIVE
          </div>
        )}

        {cabinet.forecast && (
          <div style={{ fontSize: 12, color: "var(--warning)", marginBottom: 18 }}>
            🕐 {cabinet.forecast.message}
          </div>
        )}

        <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
          <button
            onClick={onAck}
            style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 8, color: "var(--text)", padding: "10px 18px", fontSize: 13 }}
          >
            ACKNOWLEDGE
          </button>
          <button
            onClick={onViewIncident}
            style={{ background: "var(--copper-dim)", border: "none", borderRadius: 8, color: "var(--text)", padding: "10px 18px", fontSize: 13, fontWeight: 600 }}
          >
            VIEW INCIDENT
          </button>
          <button
            onClick={onCreateWorkOrder}
            style={{ background: workOrderSent ? "var(--teal)" : RISK_COLOR.critical, border: "none", borderRadius: 8, color: "#fff", padding: "10px 18px", fontSize: 13, fontWeight: 600 }}
          >
            {workOrderSent ? "✓ WORK ORDER CREATED" : "CREATE WORK ORDER"}
          </button>
        </div>

        <button
          onClick={onDismiss}
          style={{ marginTop: 18, background: "none", border: "none", color: "var(--text-dim)", fontSize: 11, textDecoration: "underline", cursor: "pointer" }}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
