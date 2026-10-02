import { useState } from "react";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

const COLS = 12;

export default function RiskHeatmap({ cabinets, onSelectCabinet }) {
  const [hovered, setHovered] = useState(null);

  const sorted = [...cabinets].sort((a, b) => {
    const na = parseInt(a.cabinet_id.replace(/\D/g, ""), 10);
    const nb = parseInt(b.cabinet_id.replace(/\D/g, ""), 10);
    return na - nb;
  });

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, position: "relative" }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 12 }}>
        🗺️ Risk Heatmap — substation layout ({cabinets.length} cabinets)
      </div>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${COLS}, 1fr)`, gap: 5 }}>
        {sorted.map((c) => (
          <div
            key={c.cabinet_id}
            onClick={() => onSelectCabinet(c.cabinet_id)}
            onMouseEnter={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              setHovered({ cabinet: c, x: rect.left, y: rect.bottom + 6 });
            }}
            onMouseLeave={() => setHovered(null)}
            style={{
              aspectRatio: "1",
              borderRadius: 5,
              background: RISK_COLOR[c.risk_label],
              opacity: c.risk_label === "normal" ? 0.3 : 1,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 8,
              fontFamily: "var(--font-mono)",
              color: "rgba(0,0,0,0.55)",
              transition: "transform 0.15s",
              boxShadow: c.risk_label === "critical" ? `0 0 8px ${RISK_COLOR.critical}` : "none",
            }}
            title={c.cabinet_id}
          >
            {c.cabinet_id.replace("AG-", "")}
          </div>
        ))}
      </div>

      {hovered && (
        <div
          style={{
            position: "fixed",
            left: hovered.x,
            top: hovered.y,
            zIndex: 60,
            background: "var(--panel-2)",
            border: `1px solid ${RISK_COLOR[hovered.cabinet.risk_label]}`,
            borderRadius: 8,
            padding: "8px 12px",
            fontSize: 12,
            pointerEvents: "none",
            boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
          }}
        >
          <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{hovered.cabinet.cabinet_id}</div>
          <div style={{ color: RISK_COLOR[hovered.cabinet.risk_label] }}>
            Risk: {hovered.cabinet.risk_score.toFixed(0)} · {RISK_LABEL_EN[hovered.cabinet.risk_label]}
          </div>
          <div style={{ color: "var(--text-dim)", fontSize: 11 }}>Load: {hovered.cabinet.load_A ?? "—"}A</div>
        </div>
      )}
    </div>
  );
}
