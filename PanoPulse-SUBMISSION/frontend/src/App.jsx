import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "./api";
import FleetSidebar from "./components/FleetSidebar";
import CabinetDetail from "./components/CabinetDetail";
import FleetOverview from "./components/FleetOverview";
import DigitalTwin3D from "./components/DigitalTwin3D";
import CopilotView from "./components/CopilotView";
import AlertsFeed from "./components/AlertsFeed";
import NotificationToast from "./components/NotificationToast";
import PitchDemoBanner from "./components/PitchDemoBanner";
import EmergencyMode from "./components/EmergencyMode";

const POLL_MS = 3000;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default function App() {
  const [cabinets, setCabinets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [selected, setSelected] = useState(null);
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(true);
  const [view, setView] = useState("detail");
  const [toast, setToast] = useState(null);
  const [demo, setDemo] = useState({ running: false, step: null, copilotMsg: null, workOrder: false, secondsLeft: 0 });
  const [emergencyDismissedFor, setEmergencyDismissedFor] = useState(null);
  const [emergencyWorkOrderSent, setEmergencyWorkOrderSent] = useState(false);

  const knownAlertIds = useRef(new Set());
  const toastTimerRef = useRef(null);

  const refreshFleet = useCallback(async () => {
    try {
      const [cabs, sum, al] = await Promise.all([
        api.listCabinets(),
        api.fleetSummary(),
        api.getAlerts(),
      ]);
      setCabinets(cabs);
      setSummary(sum.counts);
      setAlerts(al);
      setConnected(true);
      if (!selectedId && cabs.length) setSelectedId(cabs[0].cabinet_id);

      // Show a toast when a new alert is detected (notification channel confirmation)
      for (const a of al) {
        if (!knownAlertIds.current.has(a.id)) {
          knownAlertIds.current.add(a.id);
          if (knownAlertIds.current.size > 1) {
            // everything looks "new" on first load — only show toasts for later ones
            setToast(a);
            clearTimeout(toastTimerRef.current);
            toastTimerRef.current = setTimeout(() => setToast(null), 6000);
          }
        }
      }
    } catch (e) {
      setConnected(false);
    }
  }, [selectedId]);

  const refreshSelected = useCallback(async () => {
    if (!selectedId) return;
    try {
      const [detail, hist] = await Promise.all([
        api.getCabinet(selectedId),
        api.getHistory(selectedId),
      ]);
      setSelected(detail);
      setHistory(hist);
    } catch (e) {
      /* ignore transient errors during polling */
    }
  }, [selectedId]);

  useEffect(() => {
    refreshFleet();
    const id = setInterval(refreshFleet, POLL_MS);
    return () => clearInterval(id);
  }, [refreshFleet]);

  useEffect(() => {
    refreshSelected();
    const id = setInterval(refreshSelected, POLL_MS);
    return () => clearInterval(id);
  }, [refreshSelected]);

  useEffect(() => {
    // Once a cabinet drops out of critical, clear its dismissal so a
    // FUTURE critical episode shows Emergency Mode again (rather than
    // staying silenced forever after the first dismiss).
    if (selected && selected.risk_label !== "critical" && emergencyDismissedFor === selected.cabinet_id) {
      setEmergencyDismissedFor(null);
    }
  }, [selected?.risk_label, selected?.cabinet_id]);

  const handleScenario = async (cabinetId, scenario) => {
    await api.setScenario(cabinetId, scenario);
    refreshSelected();
    refreshFleet();
  };

  const handleAck = async (alertId) => {
    await api.ackAlert(alertId);
    refreshFleet();
  };

  const handleEmergencyAck = async () => {
    const matching = alerts.find((a) => a.cabinet_id === selected?.cabinet_id && !a.acknowledged);
    if (matching) await handleAck(matching.id);
    setEmergencyDismissedFor(selected?.cabinet_id);
  };

  const handleEmergencyWorkOrder = () => {
    setEmergencyWorkOrderSent(true);
    setTimeout(() => setEmergencyWorkOrderSent(false), 4000);
  };

  const handleSelectAndView = (cabinetId) => {
    setSelectedId(cabinetId);
    setView("detail");
  };

  const handleRunFleetSimulation = async () => {
    if (cabinets.length < 6) return;
    // A wider spread of targets makes the fleet-wide chart change
    // visibly, not just a single thin sliver.
    const targets = [cabinets[5], cabinets[15], cabinets[25], cabinets[35], cabinets[45], cabinets[55]].filter(Boolean);
    const scenarios = ["sensor_fault", "sensor_fault", "sensor_fault", "sensor_fault", "sensor_fault", "arc_flash"];
    await Promise.all(targets.map((c, i) => api.setScenario(c.cabinet_id, scenarios[i])));
    await refreshFleet();
    if (selectedId) refreshSelected();
  };

  // --- Live Pitch Demo Mode: an automated end-to-end scenario ---
  const runPitchDemo = async () => {
    if (demo.running) return;
    const demoCabinetId = selectedId || cabinets[0]?.cabinet_id;
    if (!demoCabinetId) return;

    setView("detail");
    setSelectedId(demoCabinetId);

    const countdown = { total: 40 };
    let secondsElapsed = 0;
    const tickTimer = setInterval(() => {
      secondsElapsed += 1;
      setDemo((d) => ({ ...d, secondsLeft: Math.max(0, countdown.total - secondsElapsed) }));
    }, 1000);

    try {
      setDemo({ running: true, step: "🔄 Resetting to normal state...", copilotMsg: null, workOrder: false, secondsLeft: 40 });
      await api.setScenario(demoCabinetId, "normal");
      await sleep(1500);

      setDemo((d) => ({ ...d, step: "⚡ Simulating a sudden load and temperature rise on phase L1..." }));
      await api.setScenario(demoCabinetId, "overload");
      await sleep(3000);

      setDemo((d) => ({ ...d, step: "📊 Detecting anomaly — multi-sensor correlation running..." }));
      // Instead of a fixed sleep, we actively wait for real detection —
      // this avoids a race condition between demo timing and the
      // engine's real (variable) detection speed. This matters because
      // it keeps the AI's commentary genuinely grounded in the true
      // current state, not a guessed one.
      let detected = false;
      for (let i = 0; i < 7; i++) {
        await sleep(2500);
        try {
          const d2 = await api.getCabinet(demoCabinetId);
          if (d2.risk_label !== "normal") {
            detected = true;
            break;
          }
        } catch (e) {
          /* keep going */
        }
      }
      await refreshSelected();
      await refreshFleet();
      if (!detected) {
        setDemo((d) => ({ ...d, step: "⚠️ Anomaly hasn't crossed the threshold yet this run — the system is being conservative by design (low false-alarm rate)." }));
        await sleep(4000);
      }

      setDemo((d) => ({ ...d, step: "🤖 AI Co-Pilot engaging, analyzing root cause..." }));
      let copilotAnswer = "Analyzing...";
      try {
        const res = await api.askCopilot(demoCabinetId, "Why is the risk high?");
        copilotAnswer = res.answer;
      } catch (e) {
        /* don't break the demo flow */
      }
      setDemo((d) => ({ ...d, copilotMsg: copilotAnswer }));
      await sleep(6000);

      setDemo((d) => ({ ...d, step: "📋 Creating an automatic work order, notifying the field team...", workOrder: true }));
      await sleep(3500);

      setDemo((d) => ({ ...d, step: "✅ Simulating field intervention — system stabilizing..." }));
      await api.setScenario(demoCabinetId, "normal");
      await sleep(4000);
      await refreshSelected();
      await refreshFleet();

      setDemo((d) => ({ ...d, step: "🎬 Demo complete." }));
      await sleep(1500);
    } finally {
      clearInterval(tickTimer);
      setDemo({ running: false, step: null, copilotMsg: null, workOrder: false, secondsLeft: 0 });
    }
  };

  const tabs = [
    { key: "detail", label: "Cabinet Detail" },
    { key: "twin", label: "Digital Twin" },
    { key: "fleet", label: "Fleet Overview" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr 300px", height: "100vh" }}>
      <NotificationToast alert={toast} onClose={() => setToast(null)} />
      <PitchDemoBanner step={demo.step} copilotMsg={demo.copilotMsg} workOrderSent={demo.workOrder} secondsLeft={demo.secondsLeft} />
      {selected && selected.risk_label === "critical" && emergencyDismissedFor !== selected.cabinet_id && !demo.running && (
        <EmergencyMode
          cabinet={selected}
          onDismiss={() => setEmergencyDismissedFor(selected.cabinet_id)}
          onAck={handleEmergencyAck}
          onViewIncident={() => { setView("detail"); setEmergencyDismissedFor(selected.cabinet_id); }}
          onCreateWorkOrder={handleEmergencyWorkOrder}
          workOrderSent={emergencyWorkOrderSent}
        />
      )}

      <div style={{ borderRight: "1px solid var(--border)", background: "var(--bg)" }}>
        <FleetSidebar cabinets={cabinets} summary={summary} selectedId={selectedId} onSelect={handleSelectAndView} />
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        <div
          style={{
            padding: "16px 28px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: 18, fontWeight: 500, color: "var(--copper)" }}>PanoPulse</div>
            <div style={{ fontSize: 12, color: "var(--text-dim)" }}>
              In-cabinet anomaly early-warning system · on-prem
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              onClick={runPitchDemo}
              disabled={demo.running}
              style={{
                background: demo.running ? "var(--panel-2)" : "linear-gradient(135deg, #3FB89C, #2D8A75)",
                border: "none",
                borderRadius: 6,
                color: "#fff",
                padding: "6px 14px",
                fontSize: 12,
                fontWeight: 700,
                cursor: demo.running ? "default" : "pointer",
              }}
            >
              {demo.running ? `⏸ Demo running (${demo.secondsLeft}s)` : "▶ Presentation Mode"}
            </button>

            <div style={{ display: "flex", gap: 4 }}>
              {tabs.map((v) => (
                <button
                  key={v.key}
                  onClick={() => setView(v.key)}
                  style={{
                    background: view === v.key ? "var(--panel-2)" : "transparent",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    color: view === v.key ? "var(--copper)" : "var(--text-dim)",
                    padding: "6px 12px",
                    fontSize: 12,
                  }}
                >
                  {v.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => setView("copilot")}
              className={view === "copilot" ? "" : "copilot-pulse"}
              style={{
                background: view === "copilot" ? "var(--copper)" : "linear-gradient(135deg, var(--copper-dim), var(--copper))",
                border: "none",
                borderRadius: 6,
                color: "#fff",
                padding: "6px 14px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              🤖 AI Co-Pilot
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: connected ? "var(--teal)" : "var(--critical)", fontFamily: "var(--font-mono)" }}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: connected ? "var(--teal)" : "var(--critical)" }} />
              {connected ? "connected" : "disconnected"}
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflow: "hidden" }}>
          {view === "detail" ? (
            <CabinetDetail cabinet={selected} history={history} onScenario={handleScenario} />
          ) : view === "twin" ? (
            <DigitalTwin3D cabinet={selected} onScenario={handleScenario} />
          ) : view === "copilot" ? (
            <CopilotView cabinet={selected} />
          ) : (
            <FleetOverview
              summary={summary}
              cabinets={cabinets}
              totalCabinets={cabinets.length}
              onSelectCabinet={handleSelectAndView}
              onRunSimulation={handleRunFleetSimulation}
            />
          )}
        </div>
      </div>

      <div style={{ borderLeft: "1px solid var(--border)" }}>
        <AlertsFeed alerts={alerts} onAck={handleAck} />
      </div>
    </div>
  );
}
