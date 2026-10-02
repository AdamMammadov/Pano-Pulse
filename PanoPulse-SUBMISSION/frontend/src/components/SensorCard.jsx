export default function SensorCard({ label, value, unit, sub, accent }) {
  const isLongText = typeof value === "string" && value.length > 6;
  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "14px 16px",
        flex: 1,
        minWidth: 130,
        overflow: "hidden",
      }}
    >
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 6 }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4, flexWrap: "wrap" }}>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: isLongText ? 16 : 24,
            fontWeight: 500,
            color: accent || "var(--text)",
            wordBreak: "break-word",
            lineHeight: 1.3,
          }}
        >
          {value}
        </span>
        {unit && <span style={{ fontSize: 13, color: "var(--text-dim)" }}>{unit}</span>}
      </div>
      {sub && <div style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
