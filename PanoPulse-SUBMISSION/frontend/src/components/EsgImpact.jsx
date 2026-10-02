import { useState } from "react";

const CO2_FACTOR_KG_PER_KWH = 0.45; // commonly cited approximate value for Turkey's grid average

export default function EsgImpact({ cabinet }) {
  const [resistanceMOhm, setResistanceMOhm] = useState(2); // mΩ — example of a typical "loose connection" range

  const anomalousChannels = (cabinet?.contributing_factors || []).join(" ").toLowerCase();
  const hasLooseConnection = anomalousChannels.includes("current") || anomalousChannels.includes("temperature");
  if (!cabinet || !hasLooseConnection) return null;

  const current = cabinet.current.L1.primary_A;
  const resistanceOhm = resistanceMOhm / 1000;
  const powerLossW = current * current * resistanceOhm; // P = I²R
  const monthlyKwh = (powerLossW / 1000) * 24 * 30.4;
  const monthlyCo2Kg = monthlyKwh * CO2_FACTOR_KG_PER_KWH;

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--teal)", borderRadius: 8, padding: 16, marginTop: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>
        🌱 Energy Efficiency / ESG Impact
        <span style={{ marginLeft: 6, fontSize: 10, opacity: 0.7 }}>(P=I²R formula, editable assumption)</span>
      </div>

      <div style={{ display: "flex", gap: 20, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div>
          <label style={{ fontSize: 11, color: "var(--text-dim)", display: "block", marginBottom: 4 }}>
            Assumed excess resistance (mΩ)
          </label>
          <input
            type="number"
            step="0.5"
            value={resistanceMOhm}
            onChange={(e) => setResistanceMOhm(Math.max(0, Number(e.target.value)))}
            style={{ width: 80, background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", padding: "6px 10px", fontFamily: "var(--font-mono)", fontSize: 13 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)" }}>Instantaneous power loss</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: "var(--warning)" }}>{powerLossW.toFixed(0)} W</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)" }}>Estimated monthly energy loss</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: "var(--warning)" }}>{monthlyKwh.toFixed(0)} kWh</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: "var(--text-dim)" }}>Estimated monthly CO₂</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: "var(--teal)" }}>{monthlyCo2Kg.toFixed(0)} kg</div>
        </div>
      </div>

      <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 10, fontStyle: "italic" }}>
        Calculation: P = I²R (I={current.toFixed(0)}A, R={resistanceMOhm}mΩ — example of a typical loose-connection
        range; the real value should be verified with a field measurement). CO₂ factor: ~{CO2_FACTOR_KG_PER_KWH} kg/kWh
        (a commonly cited approximation for Turkey's grid average — should be confirmed against the current official factor).
      </div>
    </div>
  );
}
