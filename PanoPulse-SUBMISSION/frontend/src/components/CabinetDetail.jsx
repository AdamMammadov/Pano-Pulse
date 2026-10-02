import { useEffect, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import SensorCard from "./SensorCard";
import CopilotChat from "./CopilotChat";
import Gauge from "./Gauge";
import FinancialImpact from "./FinancialImpact";
import EsgImpact from "./EsgImpact";
import WhatIfSimulator from "./WhatIfSimulator";
import ForensicsTimeline from "./ForensicsTimeline";
import FailureCountdown from "./FailureCountdown";
import AutoTripBanner from "./AutoTripBanner";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";
import { playCriticalAlertSound } from "../alertSound";
import { API_BASE } from "../api";

const SCENARIOS = [
  { key: "normal", label: "Normal" },
  { key: "overload", label: "Overload" },
  { key: "arc_flash", label: "Arc Flash" },
  { key: "insulation", label: "Insulation Degradation" },
  { key: "sensor_fault", label: "Sensor Fault" },
];

const HEALTH_SCORE_LABEL = (score) => {
  if (score >= 90) return "Healthy";
  if (score >= 75) return "Normal";
  if (score >= 50) return "Watch";
  return "Critical";
};

export default function CabinetDetail({ cabinet, history, onScenario }) {
  const prevLabelRef = useRef(null);

  useEffect(() => {
    if (!cabinet) return;
    const becameCritical = cabinet.risk_label === "critical" && prevLabelRef.current !== "critical";
    if (becameCritical) playCriticalAlertSound();
    prevLabelRef.current = cabinet.risk_label;
  }, [cabinet?.risk_label, cabinet?.cabinet_id]);

  if (!cabinet) {
    return (
      <div style={{ padding: 40, color: "var(--text-dim)" }}>
        Select a cabinet from the left.
      </div>
    );
  }

  const chartData = history.map((h) => ({
    t: new Date(h.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    risk: h.risk_score,
  }));

  return (
    <div style={{ padding: "20px 28px", overflowY: "auto", height: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 500 }}>
            {cabinet.cabinet_id}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-dim)" }}>
            LV cabinet · 1600 kVA · TEDAS-MLZ/2003-06.B
            {cabinet.data_source === "modbus_live" && (
              <span
                style={{
                  marginLeft: 10,
                  fontSize: 11,
                  color: "var(--teal)",
                  border: "1px solid var(--teal)",
                  borderRadius: 4,
                  padding: "1px 6px",
                }}
                title="Current/ARC values for this cabinet are read live via a real Modbus TCP client from a virtual MPR-53CS/TVOC-2 device — not the shared synthetic generator."
              >
                🔌 Live Modbus (real client round-trip)
              </span>
            )}
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Gauge value={cabinet.risk_score} color={RISK_COLOR[cabinet.risk_label]} label="RISK" size={72} />
          <div
            style={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "8px 14px",
              minWidth: 110,
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 4 }}>
              Cabinet Health Score
            </div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 20, fontWeight: 500 }}>
              {cabinet.health_score?.toFixed(1) ?? "—"}
              <span style={{ fontSize: 11, color: "var(--text-dim)" }}> / 100</span>
            </div>
            <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
              {cabinet.health_score != null ? HEALTH_SCORE_LABEL(cabinet.health_score) : "No data"}
            </div>
          </div>
          <div
            className={cabinet.risk_label === "critical" ? "critical-flash" : ""}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              background: "var(--panel)",
              border: `1px solid ${RISK_COLOR[cabinet.risk_label]}`,
              borderRadius: 8,
              padding: "8px 16px",
            }}
          >
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: RISK_COLOR[cabinet.risk_label] }} />
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 20, color: RISK_COLOR[cabinet.risk_label] }}>
              {cabinet.risk_score.toFixed(0)}
            </span>
            <span style={{ fontSize: 13, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: 0.5 }}>
              {RISK_LABEL_EN[cabinet.risk_label]}
            </span>
          </div>
          <a
            href={`${API_BASE}/cabinets/${cabinet.cabinet_id}/report.pdf`}
            style={{
              fontSize: 12,
              color: "var(--copper)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: "6px 12px",
              textDecoration: "none",
            }}
          >
            📄 PDF Report
          </a>
        </div>
      </div>

      <AutoTripBanner cabinet={cabinet} />
      <FailureCountdown forecast={cabinet.forecast} />

      {cabinet.likely_cause && (
        <div
          style={{
            background: "var(--panel-2)",
            border: `1px solid ${RISK_COLOR[cabinet.risk_label]}`,
            borderRadius: 8,
            padding: "12px 16px",
            marginBottom: 20,
            fontSize: 14,
          }}
        >
          <strong style={{ color: RISK_COLOR[cabinet.risk_label] }}>Likely cause: </strong>
          {cabinet.likely_cause}
          {cabinet.contributing_factors?.length > 0 && (
            <ul style={{ margin: "8px 0 0", paddingLeft: 18, color: "var(--text-dim)", fontSize: 13 }}>
              {cabinet.contributing_factors.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}

          {cabinet.root_cause_ranking?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>
                Root cause probability breakdown:
              </div>
              {cabinet.root_cause_ranking.map((r, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <div style={{ width: 160, fontSize: 12 }}>{r.cause}</div>
                  <div style={{ flex: 1, background: "var(--border)", borderRadius: 4, height: 8, overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${r.probability_pct}%`,
                        height: "100%",
                        background: i === 0 ? RISK_COLOR[cabinet.risk_label] : "var(--text-dim)",
                      }}
                    />
                  </div>
                  <div style={{ width: 40, fontSize: 12, fontFamily: "var(--font-mono)", textAlign: "right" }}>
                    {r.probability_pct.toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          )}

          {cabinet.forecast && (
            <div
              style={{
                marginTop: 12,
                paddingTop: 12,
                borderTop: "1px solid var(--border)",
                fontSize: 13,
                color: "var(--warning)",
              }}
            >
              🕐 <strong>Predictive maintenance:</strong> {cabinet.forecast.message}
            </div>
          )}
        </div>
      )}

      {/* Sensor readouts */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
        <SensorCard label="Current L1 / L2 / L3" value={`${cabinet.current.L1.primary_A} / ${cabinet.current.L2.primary_A} / ${cabinet.current.L3.primary_A}`} unit="A" sub="MPR-53CS · Modbus" />
        <SensorCard label="Surface temperature" value={cabinet.surface_temp_C} unit="°C" sub="Cable/busbar surface" accent={cabinet.surface_temp_C > 55 ? "var(--warning)" : undefined} />
        <SensorCard label="Ambient temperature" value={cabinet.ambient_temp_C} unit="°C" sub="Wireless node" />
        <SensorCard label="Humidity" value={cabinet.humidity_pct} unit="%RH" sub="Wireless node" />
        <SensorCard label="Partial discharge" value={cabinet.pd_magnitude_pC} unit="pC" sub="Techimp HFCT" />
        <SensorCard
          label="ARC status"
          value={cabinet.arc_trip ? "TRIPPED" : "Normal"}
          sub="ABB TVOC-2 · Modbus"
          accent={cabinet.arc_trip ? "var(--critical)" : "var(--teal)"}
        />
      </div>

      {/* Risk history chart */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border)",
          borderRadius: 8,
          padding: "16px",
          marginBottom: 20,
          height: 220,
        }}
      >
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 8 }}>
          Risk score — over time
        </div>
        <ResponsiveContainer width="100%" height="85%">
          <LineChart data={chartData}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="t" stroke="var(--text-dim)" fontSize={11} />
            <YAxis domain={[0, 100]} stroke="var(--text-dim)" fontSize={11} />
            <Tooltip contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)" }} />
            <Line type="monotone" dataKey="risk" stroke="var(--copper)" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Demo scenario controls */}
      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>
          Trigger demo scenario (this cabinet only)
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {SCENARIOS.map((s) => (
            <button
              key={s.key}
              onClick={() => onScenario(cabinet.cabinet_id, s.key)}
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                color: "var(--text)",
                padding: "8px 14px",
                fontSize: 13,
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <FinancialImpact cabinet={cabinet} />
      <EsgImpact cabinet={cabinet} />
      <WhatIfSimulator cabinet={cabinet} />
      <ForensicsTimeline cabinetId={cabinet.cabinet_id} />

      <CopilotChat cabinetId={cabinet.cabinet_id} />
    </div>
  );
}
