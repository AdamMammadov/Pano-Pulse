// PanoPulse API client.
// Points at the on-prem backend — change API_BASE if it runs on a
// different host/port on your local network.
export const API_BASE = "http://localhost:8000";

// Dev-only default — in a real deployment this comes from a secure
// local config, never hardcoded in the bundle. See backend/app/auth.py.
const API_KEY = "panopulse-dev-key-CHANGE-ME";

async function j(path, opts) {
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

function authed(opts = {}) {
  return { ...opts, headers: { ...(opts.headers || {}), "X-API-Key": API_KEY } };
}

export const api = {
  fleetSummary: () => j("/fleet/summary"),
  listCabinets: () => j("/cabinets"),
  getCabinet: (id) => j(`/cabinets/${id}`),
  getHistory: (id) => j(`/cabinets/${id}/history`),
  getForensics: (id) => j(`/cabinets/${id}/forensics`),
  setScenario: (id, scenario) =>
    j(
      `/cabinets/${id}/scenario`,
      authed({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      })
    ),
  getAlerts: () => j("/alerts"),
  ackAlert: (id) => j(`/alerts/${id}/ack`, authed({ method: "POST" })),
  alertsExportUrl: () => `${API_BASE}/alerts/export.csv`,
  fleetHistory: () => j("/fleet/history"),
  topPriorityPanels: () => j("/fleet/top-priority"),
  askCopilot: (id, question) =>
    j(`/cabinets/${id}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  whatIf: (id, adjustments) =>
    j(`/cabinets/${id}/what-if`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ adjustments }),
    }),
};
