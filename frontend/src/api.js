const BASE = import.meta.env.VITE_API_URL || "/api";

// Anonymous per-browser id so tracked flights and alerts belong to this visitor.
function clientId() {
  let id = localStorage.getItem("farewatch-client");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("farewatch-client", id);
  }
  return id;
}

async function request(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: { "Content-Type": "application/json", "X-Client-Id": clientId() },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Check that the Flask API is running on port 5000.");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

const qs = (params) => new URLSearchParams(params).toString();

export const api = {
  meta: () => request("/meta"),
  search: (p) => request(`/flights/search?${qs(p)}`),
  predict: (p) => request("/predict", { method: "POST", body: p }),
  history: (flightKey) => request(`/history?${qs({ flight_key: flightKey })}`),
  tracked: () => request("/track"),
  track: (flight, target_price) => request("/track", { method: "POST", body: { flight, target_price } }),
  untrack: (id) => request(`/track/${id}`, { method: "DELETE" }),
  checkNow: () => request("/track/check", { method: "POST" }),
  alerts: () => request("/alerts"),
  readAlerts: () => request("/alerts/read", { method: "POST" }),
};
