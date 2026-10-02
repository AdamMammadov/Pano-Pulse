export default function Gauge({ value, size = 90, color, label, invert = false }) {
  const pct = Math.max(0, Math.min(100, value));
  const displayPct = invert ? 100 - pct : pct;
  const angle = (displayPct / 100) * 360;

  return (
    <div style={{ width: size, height: size, position: "relative", flexShrink: 0 }}>
      <div
        style={{
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          background: `conic-gradient(${color} ${angle}deg, var(--border) ${angle}deg)`,
          transition: "background 0.4s ease",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: size * 0.13,
          borderRadius: "50%",
          background: "var(--panel)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ fontFamily: "var(--font-mono)", fontSize: size * 0.24, color, lineHeight: 1 }}>
          {pct.toFixed(0)}
        </div>
        {label && (
          <div style={{ fontSize: size * 0.09, color: "var(--text-dim)", marginTop: 2, textAlign: "center" }}>
            {label}
          </div>
        )}
      </div>
    </div>
  );
}
