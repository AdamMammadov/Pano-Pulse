import { useState } from "react";
import { RISK_COLOR, RISK_LABEL_EN } from "../riskStyle";

export default function FleetSidebar({ cabinets, summary, selectedId, onSelect }) {
  const [view, setView] = useState("grid");
  const [query, setQuery] = useState("");
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [hovered, setHovered] = useState(null); // { cabinet, x, y }

  const filtered = cabinets.filter((c) => {
    if (onlyIssues && c.risk_label === "normal") return false;
    if (query && !c.cabinet_id.toLowerCase().includes(query.toLowerCase())) return false;
    return true;
  });
  const sorted = [...filtered].sort((a, b) => b.risk_score - a.risk_score);

  const handleEnter = (e, c) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setHovered({ cabinet: c, x: rect.right + 8, y: rect.top });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", position: "relative" }}>
      <div style={{ padding: "16px 16px 12px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: "var(--text-dim)" }}>
            {filtered.length}/{cabinets.length} cabinets
          </span>
          <div style={{ display: "flex", gap: 2 }}>
            {["grid", "list"].map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                style={{
                  fontSize: 10,
                  padding: "2px 6px",
                  background: view === v ? "var(--panel-2)" : "transparent",
                  border: "1px solid var(--border)",
                  borderRadius: 4,
                  color: view === v ? "var(--copper)" : "var(--text-dim)",
                }}
              >
                {v === "grid" ? "grid" : "list"}
              </button>
            ))}
          </div>
        </div>

        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search cabinet (AG-042)…"
          style={{
            width: "100%",
            background: "var(--panel-2)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            color: "var(--text)",
            padding: "6px 10px",
            fontSize: 12,
            marginBottom: 8,
            boxSizing: "border-box",
          }}
        />
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--text-dim)", marginBottom: 10, cursor: "pointer" }}>
          <input type="checkbox" checked={onlyIssues} onChange={(e) => setOnlyIssues(e.target.checked)} />
          Show only cabinets with alerts
        </label>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {["normal", "watch", "warning", "critical"].map((k) => (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-dim)" }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_COLOR[k], display: "inline-block" }} />
              {summary?.[k] ?? 0}
            </div>
          ))}
        </div>
      </div>

      {view === "grid" ? (
        <div style={{ padding: 12, display: "grid", gridTemplateColumns: "repeat(10, 1fr)", gap: 4, overflowY: "auto" }}>
          {sorted.map((c) => (
            <div
              key={c.cabinet_id}
              onClick={() => onSelect(c.cabinet_id)}
              onMouseEnter={(e) => handleEnter(e, c)}
              onMouseLeave={() => setHovered(null)}
              style={{
                aspectRatio: "1",
                borderRadius: 3,
                background: RISK_COLOR[c.risk_label],
                cursor: "pointer",
                outline: c.cabinet_id === selectedId ? "2px solid var(--copper)" : "none",
                outlineOffset: 1,
                opacity: c.risk_label === "normal" ? 0.35 : 1,
              }}
            />
          ))}
        </div>
      ) : (
        <div style={{ overflowY: "auto", flex: 1 }}>
          {sorted.map((c) => (
            <button
              key={c.cabinet_id}
              onClick={() => onSelect(c.cabinet_id)}
              onMouseEnter={(e) => handleEnter(e, c)}
              onMouseLeave={() => setHovered(null)}
              style={{
                width: "100%",
                textAlign: "left",
                background: c.cabinet_id === selectedId ? "var(--panel-2)" : "transparent",
                border: "none",
                borderLeft: `3px solid ${c.cabinet_id === selectedId ? "var(--copper)" : "transparent"}`,
                borderBottom: "1px solid var(--border)",
                padding: "10px 16px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                color: "var(--text)",
              }}
            >
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 13 }}>{c.cabinet_id}</span>
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-dim)" }}>
                  {c.risk_score.toFixed(0)}
                </span>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_COLOR[c.risk_label] }} />
              </span>
            </button>
          ))}
          {sorted.length === 0 && (
            <div style={{ padding: 16, fontSize: 12, color: "var(--text-dim)" }}>No results found.</div>
          )}
        </div>
      )}

      {hovered && (
        <div
          style={{
            position: "fixed",
            left: hovered.x,
            top: hovered.y,
            zIndex: 50,
            background: "var(--panel-2)",
            border: `1px solid ${RISK_COLOR[hovered.cabinet.risk_label]}`,
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 12,
            pointerEvents: "none",
            boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
            minWidth: 140,
          }}
        >
          <div style={{ fontFamily: "var(--font-mono)", fontWeight: 600, marginBottom: 4 }}>{hovered.cabinet.cabinet_id}</div>
          <div style={{ color: "var(--text-dim)" }}>Load: <span style={{ color: "var(--text)", fontFamily: "var(--font-mono)" }}>{hovered.cabinet.load_A ?? "—"}A</span></div>
          <div style={{ color: "var(--text-dim)" }}>
            Risk: <span style={{ color: RISK_COLOR[hovered.cabinet.risk_label], fontFamily: "var(--font-mono)" }}>{hovered.cabinet.risk_score.toFixed(0)}/100</span>
          </div>
          <div style={{ color: "var(--text-dim)", fontSize: 11, marginTop: 2 }}>{RISK_LABEL_EN[hovered.cabinet.risk_label]} · click for details</div>
        </div>
      )}
    </div>
  );
}
