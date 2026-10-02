import { useState } from "react";
import { api } from "../api";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

const CHANNELS = [
  { key: "current_L1", label: "Current (L1)" },
  { key: "surface_temp", label: "Surface Temperature" },
  { key: "humidity", label: "Humidity" },
  { key: "pd_magnitude", label: "Partial Discharge" },
];

export default function WhatIfSimulator({ cabinet }) {
  const [adjustments, setAdjustments] = useState({ current_L1: 0, surface_temp: 0, humidity: 0, pd_magnitude: 0 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!cabinet) return null;

  const run = async () => {
    const active = Object.fromEntries(Object.entries(adjustments).filter(([, v]) => v !== 0));
    if (Object.keys(active).length === 0) return;
    setLoading(true);
    try {
      const res = await api.whatIf(cabinet.cabinet_id, active);
      setResult(res);
    } catch (e) {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setAdjustments({ current_L1: 0, surface_temp: 0, humidity: 0, pd_magnitude: 0 });
    setResult(null);
  };

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginTop: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 4 }}>
        🧠 What-If Simulator
      </div>
      <div style={{ fontSize: 10, color: "var(--text-dim)", marginBottom: 12, fontStyle: "italic" }}>
        Read-only projection — runs your hypothetical through the real detection engine without changing any live data.
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        {CHANNELS.map((c) => (
          <div key={c.key}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-dim)", marginBottom: 2 }}>
              <span>{c.label}</span>
              <span style={{ fontFamily: "var(--font-mono)", color: adjustments[c.key] !== 0 ? "var(--copper)" : "var(--text-dim)" }}>
                {adjustments[c.key] > 0 ? "+" : ""}{adjustments[c.key]}%
              </span>
            </div>
            <input
              type="range"
              min={-50}
              max={100}
              step={5}
              value={adjustments[c.key]}
              onChange={(e) => setAdjustments((a) => ({ ...a, [c.key]: Number(e.target.value) }))}
              style={{ width: "100%" }}
            />
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: result ? 14 : 0 }}>
        <button
          onClick={run}
          disabled={loading}
          style={{ background: "var(--copper-dim)", border: "none", borderRadius: 6, color: "var(--text)", padding: "8px 16px", fontSize: 13 }}
        >
          {loading ? "Simulating…" : "Run Simulation"}
        </button>
        <button
          onClick={reset}
          style={{ background: "transparent", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-dim)", padding: "8px 16px", fontSize: 13 }}
        >
          Reset
        </button>
      </div>

      {result && (
        <div style={{ background: "var(--panel-2)", borderRadius: 8, padding: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 10 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase" }}>Current</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, color: RISK_COLOR[result.current.risk_label] }}>
                {result.current.risk_score.toFixed(0)}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-dim)" }}>{RISK_LABEL_EN[result.current.risk_label]}</div>
            </div>
            <div style={{ fontSize: 20, color: "var(--text-dim)" }}>→</div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase" }}>Simulated</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 24, color: RISK_COLOR[result.simulated.risk_label] }}>
                {result.simulated.risk_score.toFixed(0)}
              </div>
              <div style={{ fontSize: 10, color: "var(--text-dim)" }}>{RISK_LABEL_EN[result.simulated.risk_label]}</div>
            </div>
            {result.simulated.forecast && (
              <div style={{ fontSize: 11, color: "var(--warning)", flex: 1 }}>
                🕐 {result.simulated.forecast.message}
              </div>
            )}
          </div>
          {result.simulated.likely_cause && (
            <div style={{ fontSize: 12, color: "var(--text)" }}>
              <strong>Projected cause:</strong> {result.simulated.likely_cause}
            </div>
          )}
          {result.simulated.root_cause_ranking?.length > 0 && (
            <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>
              {result.simulated.root_cause_ranking.map((r) => `${r.cause} (${r.probability_pct.toFixed(0)}%)`).join(" · ")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
