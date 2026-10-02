import { useState } from "react";
import { RISK_COLOR } from "../riskStyle";
import ArConceptModal from "./ArConceptModal";
import { api } from "../api";

const HEX = {
  normal: "#3fb89c",
  watch: "#d9b23f",
  warning: "#e3873a",
  critical: "#e2574a",
  blue: "#4fa3d1",
};

const LOAD_WATCH_A = 150;   // yellow border threshold
const LOAD_WARN_A = 300;    // orange/red border threshold

function loadColor(loadA, anomalous) {
  if (anomalous) return HEX.critical;
  if (loadA >= LOAD_WARN_A) return HEX.warning;
  if (loadA >= LOAD_WATCH_A) return HEX.watch;
  return HEX.blue;
}

function Zone({ children, active, activeColor, style }) {
  return (
    <div
      style={{
        background: "#1D2427",
        border: `1px solid ${active ? activeColor : "#2B3338"}`,
        borderRadius: 8,
        boxShadow: active ? `0 0 16px ${activeColor}55` : "none",
        transition: "all 0.3s",
        padding: 12,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export default function DigitalTwin3D({ cabinet, onScenario }) {
  const [showAr, setShowAr] = useState(false);
  if (!cabinet) {
    return <div style={{ padding: 40, color: "var(--text-dim)" }}>Select a cabinet from the left.</div>;
  }

  const cur = cabinet.current;
  const anomalousChannels = (cabinet.contributing_factors || []).join(" ").toLowerCase();
  const currentAnomalous = anomalousChannels.includes("current") || anomalousChannels.includes("temperature");
  const humidityAnomalous = anomalousChannels.includes("humidity") || anomalousChannels.includes("discharge");
  const arcActive = cabinet.arc_trip;

  // Estimated per-phase local temperature: the shared surface-temperature
  // sensor sits closest to the L1 line (see sensors.py) — for L2/L3 we
  // apply a modest scaling based on the current ratio (a clearly-labeled
  // estimate, not a fabricated precise number).
  const estTemp = (phaseA) => {
    const ratio = cur.L1.primary_A > 1 ? phaseA / cur.L1.primary_A : 1;
    return (cabinet.surface_temp_C * (0.85 + 0.15 * ratio)).toFixed(1);
  };

  const busbars = [
    { label: "L1", val: cur.L1.primary_A, anomalous: currentAnomalous },
    { label: "L2", val: cur.L2.primary_A, anomalous: false },
    { label: "L3", val: cur.L3.primary_A, anomalous: false },
  ];

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
          {cabinet.cabinet_id} — Digital Twin (schematic cross-section) · colored live from real sensor state
        </div>
        <button
          onClick={() => onScenario && onScenario(cabinet.cabinet_id, "overload")}
          style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-dim)", padding: "5px 12px", fontSize: 11 }}
        >
          ⚡ Test Anomaly
        </button>
        <button
          onClick={() => setShowAr(true)}
          style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-dim)", padding: "5px 12px", fontSize: 11, marginLeft: 8 }}
        >
          🥽 AR Preview (Concept)
        </button>
      </div>
      {showAr && <ArConceptModal onClose={() => setShowAr(false)} />}

      <div style={{ flex: 1, overflowY: "auto", padding: 24, display: "flex", justifyContent: "center" }}>
        <div style={{ width: "100%", maxWidth: 520, border: "2px solid #2B3338", borderRadius: 10, background: "#171D21", padding: 16 }}>
          <div style={{ textAlign: "center", color: "var(--text-dim)", fontSize: 12, marginBottom: 14 }}>
            1600 kVA LV Cabinet · TEDAS-MLZ/2003-06.B
          </div>

          <Zone active={arcActive} activeColor={HEX.critical} style={{ marginBottom: 14, display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 20, height: 20, borderRadius: "50%", background: arcActive ? HEX.critical : HEX.normal, flexShrink: 0, animation: arcActive ? "flash-critical 1s ease-out infinite" : "none" }} />
            <div>
              <div style={{ color: "var(--text)", fontSize: 13 }}>ABB TVOC-2 — ARC Sensor</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: arcActive ? HEX.critical : "var(--text-dim)" }}>
                {arcActive ? "TRIPPED — Modbus reg. 100/1300" : "Normal · Modbus reg. 100/1300"}
              </div>
            </div>
          </Zone>

          <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
            {busbars.map((bus) => {
              const borderColor = loadColor(bus.val, bus.anomalous);
              const isHighLoad = bus.val >= LOAD_WATCH_A;
              return (
                <Zone key={bus.label} active={bus.anomalous} activeColor={HEX.critical} style={{ flex: 1, textAlign: "center" }}>
                  <div
                    className={bus.anomalous ? "critical-flash" : ""}
                    style={{
                      height: 90,
                      borderRadius: 6,
                      background: bus.anomalous ? HEX.critical : "#2A3A45",
                      opacity: bus.anomalous ? 0.9 : 0.7,
                      marginBottom: 8,
                      border: `2px solid ${isHighLoad || bus.anomalous ? borderColor : "#3A4650"}`,
                      transition: "border-color 0.4s, background 0.4s",
                    }}
                  />
                  <div style={{ color: "var(--text-dim)", fontSize: 12 }}>{bus.label}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: bus.anomalous ? HEX.critical : isHighLoad ? borderColor : "var(--text)" }}>
                    {bus.val.toFixed(0)}A
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-dim)", marginTop: 2 }}>
                    ~{estTemp(bus.val)}°C
                  </div>
                </Zone>
              );
            })}
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <Zone active={false} style={{ flex: 1 }}>
              <div style={{ color: "var(--text)", fontSize: 12 }}>Gateway</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: HEX.blue }}>SCADA :5020</div>
              <div style={{ color: "var(--text-dim)", fontSize: 11 }}>"Modem" compartment</div>
            </Zone>
            <Zone active={humidityAnomalous} activeColor={HEX.warning} style={{ flex: 1 }}>
              <div style={{ color: "var(--text)", fontSize: 12 }}>Humidity / PD</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: humidityAnomalous ? HEX.warning : "var(--text-dim)" }}>
                {cabinet.humidity_pct}% · {cabinet.pd_magnitude_pC}pC
              </div>
              <div style={{ color: "var(--text-dim)", fontSize: 11 }}>Techimp HFCT</div>
            </Zone>
          </div>

          {cabinet.surface_temp_C > 45 && (
            <div style={{ marginTop: 14, textAlign: "center", fontSize: 12, color: HEX.warning }}>
              🌡️ Surface temperature rising: {cabinet.surface_temp_C}°C
            </div>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 1, background: "var(--border)", borderTop: "1px solid var(--border)" }}>
        {[
          { label: "L1", value: `${cur.L1.primary_A.toFixed(0)}A`, color: loadColor(cur.L1.primary_A, currentAnomalous) },
          { label: "L2", value: `${cur.L2.primary_A.toFixed(0)}A`, color: loadColor(cur.L2.primary_A, false) },
          { label: "L3", value: `${cur.L3.primary_A.toFixed(0)}A`, color: loadColor(cur.L3.primary_A, false) },
          { label: "ARC", value: arcActive ? "TRIPPED" : "Normal", color: arcActive ? HEX.critical : HEX.normal },
        ].map((item) => (
          <div key={item.label} style={{ background: "var(--panel)", padding: "10px 14px" }}>
            <div style={{ fontSize: 11, color: "var(--text-dim)" }}>{item.label}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 15, color: item.color }}>{item.value}</div>
          </div>
        ))}
      </div>

      <div style={{ padding: "10px 16px", borderTop: "1px solid var(--border)", display: "flex", gap: 16, fontSize: 12, color: "var(--text-dim)" }}>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: HEX.blue, marginRight: 6 }} />Normal</span>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: HEX.watch, marginRight: 6 }} />150A+ load</span>
        <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: RISK_COLOR.critical, marginRight: 6 }} />Anomaly</span>
      </div>
    </div>
  );
}
