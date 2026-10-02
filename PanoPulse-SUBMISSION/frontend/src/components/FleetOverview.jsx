import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { api } from "../api";
import Gauge from "./Gauge";
import RiskHeatmap from "./RiskHeatmap";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

const HOURLY_RATE_USD = 500; // same illustrative default as the per-cabinet calculator

export default function FleetOverview({ summary, cabinets, totalCabinets, onSelectCabinet, onRunSimulation }) {
  const [history, setHistory] = useState([]);
  const [topPriority, setTopPriority] = useState([]);
  const [simulating, setSimulating] = useState(false);
  const [fleetExposureUsd, setFleetExposureUsd] = useState(0);

  useEffect(() => {
    const load = () => {
      api.fleetHistory().then(setHistory).catch(() => {});
      api.topPriorityPanels().then(setTopPriority).catch(() => {});
    };
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const topRisky = [...(cabinets || [])].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);
  const atRiskIds = topRisky.filter((c) => c.risk_label !== "normal").map((c) => c.cabinet_id).join(",");

  useEffect(() => {
    // Fleet-wide financial exposure is a REAL sum over each at-risk
    // cabinet's own forecast-based estimate (same transparent formula
    // as the per-cabinet calculator) — never a flat, invented number.
    let cancelled = false;
    (async () => {
      const ids = atRiskIds ? atRiskIds.split(",") : [];
      if (ids.length === 0) {
        setFleetExposureUsd(0);
        return;
      }
      try {
        const details = await Promise.all(ids.map((id) => api.getCabinet(id)));
        const total = details.reduce((sum, d) => {
          const hours = d?.forecast?.hours_to_critical ?? 4;
          return sum + hours * HOURLY_RATE_USD;
        }, 0);
        if (!cancelled) setFleetExposureUsd(Math.round(total));
      } catch (e) {
        /* ignore transient errors */
      }
    })();
    return () => { cancelled = true; };
  }, [atRiskIds]);

  const chartData = history.map((h) => ({
    t: new Date(h.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    normal: h.normal,
    watch: h.watch,
    warning: h.warning,
    critical: h.critical,
    avg_risk: h.avg_risk,
  }));

  const latestAvgRisk = history.length ? history[history.length - 1].avg_risk : 0;
  const healthIndex = Math.max(0, 100 - latestAvgRisk).toFixed(1);
  const healthColor = healthIndex >= 90 ? RISK_COLOR.normal : healthIndex >= 70 ? RISK_COLOR.watch : RISK_COLOR.critical;

  const handleSimulate = async () => {
    setSimulating(true);
    try {
      await onRunSimulation();
    } finally {
      setTimeout(() => setSimulating(false), 2000);
    }
  };

  return (
    <div style={{ padding: "20px 28px", overflowY: "auto", height: "100%" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 22, fontWeight: 500 }}>Fleet Overview</div>
          <div style={{ fontSize: 13, color: "var(--text-dim)" }}>{totalCabinets} cabinets · management view</div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {/* System Health Index */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, background: "var(--panel)", border: `1px solid ${healthColor}`, borderRadius: 10, padding: "8px 16px" }}>
            <Gauge value={parseFloat(healthIndex)} color={healthColor} size={64} />
            <div>
              <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: 0.5 }}>System Health</div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: healthColor, fontWeight: 600 }}>{healthIndex}%</div>
            </div>
          </div>

          {fleetExposureUsd > 0 && (
            <div style={{ display: "flex", flexDirection: "column", background: "var(--panel)", border: "1px solid var(--warning)", borderRadius: 10, padding: "8px 16px" }}>
              <div style={{ fontSize: 10, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: 0.5 }}>
                Estimated exposure (top at-risk cabinets)
              </div>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: 18, color: "var(--warning)", fontWeight: 600 }}>
                ~${fleetExposureUsd.toLocaleString()}
              </div>
            </div>
          )}

          <button
            onClick={handleSimulate}
            disabled={simulating}
            style={{
              background: simulating ? "var(--panel-2)" : "var(--copper-dim)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              color: "var(--text)",
              padding: "10px 18px",
              fontSize: 13,
              cursor: simulating ? "default" : "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {simulating ? "Simulation running…" : "⚡ Start Simulation"}
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        {["normal", "watch", "warning", "critical"].map((k) => (
          <div key={k} style={{ flex: 1, background: "var(--panel)", border: `1px solid ${RISK_COLOR[k]}`, borderRadius: 8, padding: "14px 16px", textAlign: "center" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 28, color: RISK_COLOR[k] }}>{summary?.[k] ?? 0}</div>
            <div style={{ fontSize: 12, color: "var(--text-dim)", textTransform: "uppercase" }}>{k}</div>
          </div>
        ))}
      </div>

      <div style={{ marginBottom: 20 }}>
        <RiskHeatmap cabinets={cabinets || []} onSelectCabinet={onSelectCabinet} />
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
        <div style={{ flex: 2, background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, height: 280 }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 8 }}>
            Risk category distribution — over time (all {totalCabinets} cabinets)
          </div>
          <ResponsiveContainer width="100%" height="88%">
            <AreaChart data={chartData}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
              <XAxis dataKey="t" stroke="var(--text-dim)" fontSize={11} />
              <YAxis stroke="var(--text-dim)" fontSize={11} />
              <Tooltip contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area type="monotone" dataKey="normal" stackId="1" stroke={RISK_COLOR.normal} fill={RISK_COLOR.normal} fillOpacity={0.5} name="Normal" />
              <Area type="monotone" dataKey="watch" stackId="1" stroke={RISK_COLOR.watch} fill={RISK_COLOR.watch} fillOpacity={0.6} name="Watch" />
              <Area type="monotone" dataKey="warning" stackId="1" stroke={RISK_COLOR.warning} fill={RISK_COLOR.warning} fillOpacity={0.7} name="Warning" />
              <Area type="monotone" dataKey="critical" stackId="1" stroke={RISK_COLOR.critical} fill={RISK_COLOR.critical} fillOpacity={0.8} name="Critical" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top 5 riskiest cabinets */}
        <div style={{ flex: 1, background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, height: 280, display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>Top 5 Highest-Risk Cabinets</div>
          <div style={{ flex: 1, overflowY: "auto" }}>
            {topRisky.map((c, i) => (
              <button
                key={c.cabinet_id}
                onClick={() => onSelectCabinet(c.cabinet_id)}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  background: "transparent",
                  border: "none",
                  borderBottom: "1px solid var(--border)",
                  padding: "8px 4px",
                  cursor: "pointer",
                  color: "var(--text)",
                }}
              >
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 11, color: "var(--text-dim)", width: 14 }}>{i + 1}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 13 }}>{c.cabinet_id}</span>
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: RISK_COLOR[c.risk_label] }}>
                    {c.risk_score.toFixed(0)}
                  </span>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: RISK_COLOR[c.risk_label] }} />
                </span>
              </button>
            ))}
            {topRisky.every((c) => c.risk_score === 0) && (
              <div style={{ fontSize: 12, color: "var(--text-dim)", padding: "8px 4px" }}>All cabinets normal.</div>
            )}
          </div>
        </div>
      </div>

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 12 }}>
          🎯 Top Priority Panels — weighted by risk, persistence & forecast urgency (not risk score alone)
        </div>
        {topPriority.length === 0 ? (
          <div style={{ fontSize: 12, color: "var(--text-dim)", padding: "8px 4px" }}>
            No panels currently need attention.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {topPriority.map((panel, index) => (
              <button
                key={panel.cabinet_id}
                onClick={() => onSelectCabinet(panel.cabinet_id)}
                style={{
                  width: "100%",
                  display: "grid",
                  gridTemplateColumns: "28px 80px 130px 110px 1fr",
                  alignItems: "center",
                  gap: 10,
                  background: "transparent",
                  border: "none",
                  borderBottom: "1px solid var(--border)",
                  padding: "9px 4px",
                  cursor: "pointer",
                  color: "var(--text)",
                  textAlign: "left",
                }}
              >
                <span style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: 12 }}>#{index + 1}</span>
                <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 13 }}>{panel.cabinet_id}</span>
                <span style={{ color: RISK_COLOR[panel.risk_label] || "var(--text)", fontWeight: 600, fontSize: 13 }}>
                  {panel.risk_score.toFixed(0)} — {RISK_LABEL_EN[panel.risk_label]}
                </span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                  priority: {panel.priority_score.toFixed(1)}
                </span>
                <span style={{ fontSize: 12, color: "var(--text-dim)" }}>{panel.likely_cause || "—"}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, height: 200 }}>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 8 }}>Average fleet risk score</div>
        <ResponsiveContainer width="100%" height="80%">
          <AreaChart data={chartData}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
            <XAxis dataKey="t" stroke="var(--text-dim)" fontSize={11} />
            <YAxis domain={[0, 100]} stroke="var(--text-dim)" fontSize={11} />
            <Tooltip contentStyle={{ background: "var(--panel-2)", border: "1px solid var(--border)" }} />
            <Area type="monotone" dataKey="avg_risk" stroke="var(--copper)" fill="var(--copper)" fillOpacity={0.3} name="Average risk" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
