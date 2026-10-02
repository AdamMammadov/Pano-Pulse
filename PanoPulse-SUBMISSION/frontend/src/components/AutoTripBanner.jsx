import { useState, useEffect } from "react";

const AUTO_TRIP_THRESHOLD = 90;

/**
 * IMPORTANT ENGINEERING/SAFETY NOTE: this component does NOT perform a
 * real breaker/relay control action — it sends no command to any
 * physical circuit. This is a SIMULATION of the concept "what would
 * autonomous load-shedding look like if risk gets too high." A real
 * autonomous trip system requires safety certification (SIL), fail-safe
 * circuit design, and field testing — these are explicitly out of scope
 * for this hackathon. The interface always keeps this labeled
 * "(simulation)".
 *
 * Shown as a dismissible popup with an explicit action button (rather
 * than firing automatically), so a presenter controls exactly when it
 * appears during a demo.
 */
export default function AutoTripBanner({ cabinet }) {
  const [dismissedFor, setDismissedFor] = useState(null);
  const [tripped, setTripped] = useState(false);

  useEffect(() => {
    if (!cabinet) return;
    if (cabinet.risk_score < AUTO_TRIP_THRESHOLD) {
      setTripped(false);
    }
  }, [cabinet?.risk_score, cabinet?.cabinet_id]);

  const shouldShow = cabinet && cabinet.risk_score >= AUTO_TRIP_THRESHOLD && dismissedFor !== cabinet.cabinet_id;
  if (!shouldShow) return null;

  return (
    <div
      onClick={() => setDismissedFor(cabinet.cabinet_id)}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 250,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "linear-gradient(135deg, #1D2427, #2A1A1A)",
          border: "2px solid var(--critical)",
          borderRadius: 12,
          padding: "20px 24px",
          maxWidth: 460,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <span style={{ fontSize: 22 }}>🤖⚡</span>
          <span style={{ fontSize: 14, fontWeight: 700, color: "var(--critical)" }}>
            AUTONOMOUS DEFENSE AVAILABLE (SIMULATION)
          </span>
        </div>
        <div style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.5, marginBottom: 14 }}>
          AI has detected that <strong>{cabinet.cabinet_id}</strong>'s risk score has crossed the
          critical threshold ({AUTO_TRIP_THRESHOLD}%). As a preventive measure, its non-critical
          L3 line can be disconnected as a concept demonstration.
        </div>

        {!tripped ? (
          <button
            onClick={() => setTripped(true)}
            style={{
              background: "var(--critical)", border: "none", borderRadius: 8, color: "#fff",
              padding: "10px 18px", fontSize: 13, fontWeight: 700, cursor: "pointer", marginBottom: 10,
            }}
          >
            ⚡ Auto-Trip Load Shedding
          </button>
        ) : (
          <div style={{ fontSize: 13, color: "var(--teal)", marginBottom: 10 }}>
            ✓ L3 line disconnected (concept demonstration).
          </div>
        )}

        <div style={{ fontSize: 10, color: "var(--text-dim)", fontStyle: "italic", marginBottom: 10 }}>
          ⚠️ This is a SIMULATION — no real breaker/relay command was sent. A genuine autonomous
          trip system requires a separate safety certification (SIL) and fail-safe hardware process.
        </div>

        <button
          onClick={() => setDismissedFor(cabinet.cabinet_id)}
          style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", padding: "6px 14px", fontSize: 12 }}
        >
          Close
        </button>
      </div>
    </div>
  );
}
