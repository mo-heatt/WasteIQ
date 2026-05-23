const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const error = await response.json();
      message = error.detail || message;
    } catch {
      // Keep generic message.
    }
    throw new Error(message);
  }

  return response.json();
}

export function getHealth() {
  return fetchJson("/api/health");
}

export function getDashboard() {
  return fetchJson("/api/dashboard");
}

export function getDatasetSummary() {
  return fetchJson("/api/dataset/summary");
}

export function getChallenge1State() {
  return fetchJson("/api/challenge1/state");
}

export function getZones() {
  return fetchJson("/api/zones");
}

export function getLayers() {
  return fetchJson("/api/layers");
}

export function getRegions() {
  return fetchJson("/api/regions");
}

export function getDefaultSimulation() {
  return fetchJson("/api/simulation/default");
}

export function getOptimizerComparison() {
  return fetchJson("/api/optimizer/comparison");
}

export function getRecommendation() {
  return fetchJson("/api/recommendation");
}

export function getBeforeAfterShipment() {
  return fetchJson("/api/operations/before-after");
}

export function getFuelArea() {
  return fetchJson("/api/operations/fuel-area");
}

export function getLatestTruckAssignment() {
  return fetchJson("/api/truck-assignment/latest");
}

export function getRecentTruckAssignments() {
  return fetchJson("/api/truck-assignment/recent");
}

export function simulateTruckAssignment(payload) {
  return fetchJson("/api/truck-assignment/simulate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getScenarios() {
  return fetchJson("/api/scenarios");
}

export function getScenario(id) {
  return fetchJson(`/api/scenarios/${id}`);
}

export function getDemoSteps() {
  return fetchJson("/api/demo/steps");
}

export function getImpact() {
  return fetchJson("/api/impact");
}

export function simulateMix(payload) {
  return fetchJson("/api/simulate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
