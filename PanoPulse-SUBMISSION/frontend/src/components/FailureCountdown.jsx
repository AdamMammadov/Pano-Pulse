import { useState, useEffect, useRef } from "react";

/**
 * SpaceX-style countdown — but NOT a fabricated number: we convert the
 * real hours value coming from anomaly_engine.py's genuine linear trend
 * extrapolation (forecast.hours_to_critical) into a live, real-time,
 * second-by-second countdown. When a new forecast arrives (via polling),
 * the counter re-syncs to it — so this isn't a fixed animation, it
 * tracks the real model output.
 */
export default function FailureCountdown({ forecast }) {
  const [remainingS, setRemainingS] = useState(null);
  const targetRef = useRef(null); // hedef zaman (Date.now() + hours*3600*1000)

  useEffect(() => {
    if (!forecast) {
      targetRef.current = null;
      setRemainingS(null);
      return;
    }
    targetRef.current = Date.now() + forecast.hours_to_critical * 3600 * 1000;
  }, [forecast?.hours_to_critical]);

  useEffect(() => {
    const id = setInterval(() => {
      if (!targetRef.current) {
        setRemainingS(null);
        return;
      }
      const diff = Math.max(0, Math.round((targetRef.current - Date.now()) / 1000));
      setRemainingS(diff);
    }, 1000);
    return () => clearInterval(id);
  }, []);

  if (!forecast || remainingS === null) return null;

  const h = Math.floor(remainingS / 3600);
  const m = Math.floor((remainingS % 3600) / 60);
  const s = remainingS % 60;
  const pad = (n) => String(n).padStart(2, "0");

  const urgent = h < 1;

  return (
    <div
      style={{
        background: "#0D1214",
        border: `2px solid ${urgent ? "var(--critical)" : "var(--warning)"}`,
        borderRadius: 10,
        padding: "14px 20px",
        marginBottom: 16,
        display: "flex",
        alignItems: "center",
        gap: 16,
      }}
      className={urgent ? "critical-flash" : ""}
    >
      <div style={{ fontSize: 22 }}>{urgent ? "🔴" : "🟠"}</div>
      <div>
        <div style={{ fontSize: 11, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: 0.5 }}>
          Estimated Time to Critical Threshold
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 32, fontWeight: 700, color: urgent ? "var(--critical)" : "var(--warning)", letterSpacing: 2 }}>
          {pad(h)}:{pad(m)}:{pad(s)}
        </div>
        <div style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 2 }}>
          Source: surface-temperature trend extrapolation (linear regression) — {forecast.message}
        </div>
      </div>
    </div>
  );
}
