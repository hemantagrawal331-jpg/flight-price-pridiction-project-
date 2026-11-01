export const inr = (n) => (n == null ? "-" : "₹" + Math.round(n).toLocaleString("en-IN"));

export const DEALS = {
  great_deal: { label: "Great deal", tone: "good" },
  good_price: { label: "Good price", tone: "good" },
  fair_price: { label: "Fair price", tone: "neutral" },
  overpriced: { label: "Above expected", tone: "warn" },
};

export const ADVICE = {
  BUY_NOW: { label: "Book now", tone: "good" },
  WAIT: { label: "Wait", tone: "warn" },
  WATCH: { label: "Keep watching", tone: "neutral" },
};

export const stopsLabel = (n) => (n === 0 ? "Non-stop" : n === 1 ? "1 stop" : `${n} stops`);
export const hoursLabel = (h) => `${Math.floor(h)}h ${String(Math.round((h % 1) * 60)).padStart(2, "0")}m`;

export const isoDate = (offsetDays = 0) => {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
};

export const prettyDate = (iso) =>
  new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
