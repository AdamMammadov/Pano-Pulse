const CHANNEL_LABELS = {
  dashboard: "📺 Dashboard",
  sms: "📟 SMS (local gateway simulation)",
  whatsapp: "💬 WhatsApp (local gateway simulation)",
  telegram: "📱 Telegram (sent)",
  telegram_disabled: "📱 Telegram (not configured — no token)",
};

export default function NotificationToast({ alert, onClose }) {
  if (!alert) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 80,
        right: 320,
        zIndex: 100,
        background: "var(--panel-2)",
        border: `1px solid ${alert.severity === "critical" ? "var(--critical)" : "var(--warning)"}`,
        borderRadius: 10,
        padding: "14px 18px",
        maxWidth: 340,
        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
        animation: "toast-in 0.3s ease-out",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: alert.severity === "critical" ? "var(--critical)" : "var(--warning)" }}>
          [{alert.severity?.toUpperCase()}] {alert.cabinet_id}
        </div>
        <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--text-dim)", cursor: "pointer", fontSize: 14, lineHeight: 1 }}>
          ✕
        </button>
      </div>
      <div style={{ fontSize: 12, color: "var(--text)", marginBottom: 10 }}>{alert.message}</div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {(alert.channels || []).map((ch) => (
          <span
            key={ch}
            style={{
              fontSize: 10,
              fontFamily: "var(--font-mono)",
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              padding: "2px 6px",
              color: ch.includes("disabled") ? "var(--text-dim)" : "var(--teal)",
            }}
          >
            {CHANNEL_LABELS[ch] || ch}
          </span>
        ))}
      </div>
    </div>
  );
}
