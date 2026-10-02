export default function ArConceptModal({ onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", zIndex: 300,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 24, maxWidth: 520 }}
      >
        <div style={{ fontSize: 11, color: "var(--warning)", fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>
          ⚠️ Concept Preview — Not a Working Feature
        </div>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>AR Field Engineer Interface (Future Concept)</div>

        {/* A simple, stylized "camera view + overlay" concept illustration */}
        <div style={{ background: "#0D1214", border: "2px dashed var(--border)", borderRadius: 10, padding: 20, marginBottom: 12, position: "relative", height: 260 }}>
          <div style={{ position: "absolute", top: 12, left: 12, fontSize: 10, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
            📷 [EXAMPLE] Phone/AR-glasses camera view
          </div>
          <div style={{ position: "absolute", top: 60, left: 40, width: 160, height: 180, border: "2px solid var(--border)", borderRadius: 4 }} />
          <div style={{ position: "absolute", top: 70, left: 210, background: "var(--panel-2)", border: "1px solid var(--critical)", borderRadius: 6, padding: "4px 8px", fontSize: 10 }}>
            🔴 L1: 78°C — anomaly
          </div>
          <div style={{ position: "absolute", top: 110, left: 210, background: "var(--panel-2)", border: "1px solid var(--teal)", borderRadius: 6, padding: "4px 8px", fontSize: 10 }}>
            🟢 ARC: normal
          </div>
          <div style={{ position: "absolute", top: 150, left: 210, background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, padding: "4px 8px", fontSize: 10 }}>
            📡 Modbus: connected
          </div>
          <div style={{ position: "absolute", bottom: 12, left: 12, right: 12, fontSize: 9, color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
            Concept: live sensor labels from the PanoPulse API are overlaid onto the camera
            feed (realizable with WebXR / ARCore-ARKit)
          </div>
        </div>

        <div style={{ fontSize: 12, color: "var(--text-dim)", lineHeight: 1.6 }}>
          This is a <strong>concept</strong> for a future development stage: when a field engineer
          points their phone/AR glasses at the cabinet, real-time data is pulled from PanoPulse's
          existing (already working) REST API and overlaid on the camera view. Right now this is a
          mockup — real WebXR/ARCore integration has not yet been built.
        </div>

        <button
          onClick={onClose}
          style={{ marginTop: 16, background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", padding: "8px 16px", fontSize: 12 }}
        >
          Close
        </button>
      </div>
    </div>
  );
}
