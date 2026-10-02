import { useState } from "react";

export default function FinancialImpact({ cabinet }) {
  const [hourlyRate, setHourlyRate] = useState(500);

  if (!cabinet || cabinet.risk_label === "normal") return null;

  // Hours: IF a predictive-maintenance forecast exists (real model
  // output), we use it — otherwise we show a conservative default (4
  // hours) with a clear "default" label.
  const hours = cabinet.forecast?.hours_to_critical ?? 4;
  const estimatedLoss = Math.round(hours * hourlyRate);

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--warning)",
        borderRadius: 8,
        padding: 16,
        marginTop: 16,
      }}
    >
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>
        💰 Estimated Financial Impact
        <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.7 }}>(assumption-based, editable)</span>
      </div>

      <div style={{ display: "flex", gap: 20, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)" }}>Estimated intervention window</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 20, color: "var(--warning)" }}>
            {hours < 1 ? `${Math.round(hours * 60)} min` : `${hours.toFixed(1)} hours`}
          </div>
          <div style={{ fontSize: 10, color: "var(--text-dim)" }}>
            {cabinet.forecast ? "from the predictive maintenance model" : "default (no forecast available)"}
          </div>
        </div>

        <div>
          <label style={{ fontSize: 11, color: "var(--text-dim)", display: "block", marginBottom: 4 }}>
            Assumed hourly downtime cost ($)
          </label>
          <input
            type="number"
            value={hourlyRate}
            onChange={(e) => setHourlyRate(Math.max(0, Number(e.target.value)))}
            style={{
              width: 100,
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              color: "var(--text)",
              padding: "6px 10px",
              fontFamily: "var(--font-mono)",
              fontSize: 13,
            }}
          />
        </div>

        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)" }}>Estimated preventable loss</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, color: "var(--critical)", fontWeight: 600 }}>
            ~${estimatedLoss.toLocaleString()}
          </div>
        </div>
      </div>

      <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 10, fontStyle: "italic" }}>
        Note: the hourly rate is an illustrative default — in a real deployment it should be
        updated using ADM/GDZ's own production/SAIDI-SAIFI cost data. The time estimate,
        however, is the real output of the anomaly detection model (surface-temperature trend
        extrapolation).
      </div>
    </div>
  );
}
