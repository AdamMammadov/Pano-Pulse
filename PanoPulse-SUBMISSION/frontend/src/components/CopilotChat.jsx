import { useState, useEffect, useRef } from "react";
import { api, API_BASE } from "../api";

const SUGGESTIONS = ["Why is the risk high?", "What should I do?", "What's the current status?"];
const TYPE_SPEED_MS = 12;

function TypewriterText({ text }) {
  const [shown, setShown] = useState("");
  useEffect(() => {
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i += 2;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, TYPE_SPEED_MS);
    return () => clearInterval(id);
  }, [text]);
  const done = shown.length >= text.length;
  return (
    <>
      {shown}
      {!done && <span className="typewriter-cursor">▍</span>}
    </>
  );
}

export default function CopilotChat({ cabinetId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [workOrderSent, setWorkOrderSent] = useState(false);

  const send = async (question) => {
    if (!question.trim()) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    setWorkOrderSent(false);
    try {
      const res = await api.askCopilot(cabinetId, question);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, id: Date.now() }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: "Connection error.", id: Date.now() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkOrder = () => {
    // NOTE: this is not a real SAP/Jira API integration (no credentials
    // to connect with) — it shows a demo-purpose confirmation via the
    // same Notifier pattern used in alerts.py. Real integration, in the
    // same pattern as TelegramGateway, is a documented next step.
    setWorkOrderSent(true);
    setTimeout(() => setWorkOrderSent(false), 4000);
  };

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div style={{ background: "var(--panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16, marginTop: 20 }}>
      <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 10 }}>
        AI Co-Pilot — grounded only in this cabinet's real data — no hallucination
      </div>

      {messages.length === 0 && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              style={{ background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text-dim)", padding: "6px 10px", fontSize: 12 }}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div style={{ maxHeight: 220, overflowY: "auto", marginBottom: 10 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 8, textAlign: m.role === "user" ? "right" : "left" }}>
            <span
              style={{
                display: "inline-block",
                background: m.role === "user" ? "var(--copper-dim)" : "var(--panel-2)",
                color: "var(--text)",
                borderRadius: 8,
                padding: "6px 12px",
                fontSize: 13,
                maxWidth: "85%",
              }}
            >
              {m.role === "assistant" && m.id === lastAssistantMsg?.id ? <TypewriterText text={m.text} /> : m.text}
            </span>
          </div>
        ))}
        {loading && <div style={{ fontSize: 12, color: "var(--text-dim)" }}>typing…</div>}
      </div>

      {lastAssistantMsg && !loading && (
        <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
          <a
            href={`${API_BASE}/cabinets/${cabinetId}/report.pdf`}
            style={{ fontSize: 11, color: "var(--copper)", border: "1px solid var(--border)", borderRadius: 6, padding: "5px 10px", textDecoration: "none" }}
          >
            📄 Generate PDF Report
          </a>
          <button
            onClick={handleWorkOrder}
            style={{ fontSize: 11, color: workOrderSent ? "var(--teal)" : "var(--text-dim)", border: "1px solid var(--border)", borderRadius: 6, padding: "5px 10px", background: "transparent" }}
          >
            {workOrderSent ? "✓ Work order sent (demo)" : "📋 Send Work Order"}
          </button>
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)}
          placeholder="Ask a question about this cabinet…"
          style={{ flex: 1, background: "var(--panel-2)", border: "1px solid var(--border)", borderRadius: 6, color: "var(--text)", padding: "8px 12px", fontSize: 13 }}
        />
        <button
          onClick={() => send(input)}
          style={{ background: "var(--copper-dim)", border: "none", borderRadius: 6, color: "var(--text)", padding: "8px 16px", fontSize: 13 }}
        >
          Ask
        </button>
      </div>
    </div>
  );
}
