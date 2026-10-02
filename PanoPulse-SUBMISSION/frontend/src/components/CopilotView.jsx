import CopilotChat from "./CopilotChat";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

export default function CopilotView({ cabinet }) {
  if (!cabinet) {
    return <div style={{ padding: 40, color: "var(--text-dim)" }}>Select a cabinet from the left.</div>;
  }

  return (
    <div style={{ height: "100%", overflowY: "auto", padding: "24px 28px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: "linear-gradient(135deg, var(--copper), #E8A85C)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 20,
          }}
        >
          🤖
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 500, color: "var(--text)" }}>PanoPulse AI Co-Pilot</div>
          <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
            Autonomous analysis · grounded only in {cabinet.cabinet_id}'s real data — no hallucination
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "var(--panel)",
          border: `1px solid ${RISK_COLOR[cabinet.risk_label]}`,
          borderRadius: 8,
          padding: "10px 16px",
          marginBottom: 20,
          width: "fit-content",
        }}
      >
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: RISK_COLOR[cabinet.risk_label] }} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 16, color: RISK_COLOR[cabinet.risk_label] }}>
          {cabinet.risk_score.toFixed(0)}/100
        </span>
        <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{RISK_LABEL_EN[cabinet.risk_label]}</span>
        {cabinet.forecast && (
          <span style={{ fontSize: 12, color: "var(--warning)", marginLeft: 8 }}>🕐 {cabinet.forecast.message}</span>
        )}
      </div>

      <CopilotChat cabinetId={cabinet.cabinet_id} />
    </div>
  );
}
