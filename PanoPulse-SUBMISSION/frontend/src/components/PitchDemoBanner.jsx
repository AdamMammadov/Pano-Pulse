export default function PitchDemoBanner({ step, copilotMsg, workOrderSent, secondsLeft }) {
  if (!step) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 70,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 200,
        background: "var(--panel-2)",
        border: "2px solid var(--copper)",
        borderRadius: 12,
        padding: "16px 24px",
        minWidth: 420,
        maxWidth: 560,
        boxShadow: "0 12px 32px rgba(0,0,0,0.6)",
        animation: "demo-banner-pulse 2s ease-in-out infinite",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "var(--copper)", letterSpacing: 0.5 }}>
          ▶ LIVE PRESENTATION MODE
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
          {secondsLeft}s
        </div>
      </div>
      <div style={{ fontSize: 14, color: "var(--text)" }}>{step}</div>

      {copilotMsg && (
        <div
          style={{
            marginTop: 12,
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 12,
            color: "var(--text)",
          }}
        >
          🤖 <strong style={{ color: "var(--copper)" }}>AI Co-Pilot:</strong> {copilotMsg}
        </div>
      )}

      {workOrderSent && (
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--teal)" }}>
          ✓ Automatic work order created · field team notified
        </div>
      )}
    </div>
  );
}
