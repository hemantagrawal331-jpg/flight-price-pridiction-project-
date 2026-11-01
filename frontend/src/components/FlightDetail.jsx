import { useEffect, useState } from "react";
import { api } from "../api";
import { ADVICE, DEALS, inr, prettyDate, stopsLabel } from "../utils";
import { ForecastChart, HistoryChart } from "./ForecastChart";

export default function FlightDetail({ flight, onClose, onTracked }) {
  const [pred, setPred] = useState(null);
  const [history, setHistory] = useState([]);
  const [target, setTarget] = useState(Math.round((flight.price * 0.9) / 10) * 10);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api.predict({ ...flight, price: flight.price }).then(setPred).catch((e) => setErr(e.message));
    api.history(flight.flight_key).then((r) => setHistory(r.history)).catch(() => {});
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [flight, onClose]);

  const track = async () => {
    setErr(""); setMsg("");
    try {
      await api.track(flight, Number(target));
      setMsg(`Tracking started. We will alert you if the fare reaches ${inr(Number(target))} or less.`);
      onTracked();
    } catch (e) { setErr(e.message); }
  };

  const advice = pred && ADVICE[pred.action];
  return (
    <div className="overlay" onClick={onClose}>
      <section className="modal" role="dialog" aria-modal="true" aria-label="Flight details" onClick={(e) => e.stopPropagation()}>
        <button className="close" onClick={onClose} aria-label="Close">×</button>
        <h2>{flight.airline} {flight.flight_number}</h2>
        <p className="muted">{flight.source} to {flight.destination} · {prettyDate(flight.date)} · {flight.departure_time} · {stopsLabel(flight.stops)} · {flight.class}</p>

        <div className="facts">
          <div><span>Listed fare</span><b>{inr(flight.price)}</b></div>
          <div><span>Expected fare</span><b>{inr(flight.predicted_price)}</b></div>
          <div><span>Seats</span><b>{flight.seats ?? "-"}</b></div>
          <div><span>Versus expected</span><b>{flight.gap_pct > 0 ? "+" : ""}{flight.gap_pct}%</b></div>
        </div>

        {!pred && !err && <p className="muted">Running the prediction model…</p>}
        {pred && (
          <>
            <div className={`advice ${advice.tone}`}>
              <strong>{advice.label}</strong>
              <span>{pred.reason}</span>
            </div>
            <h3>Expected fare until departure</h3>
            <ForecastChart forecast={pred.forecast} listedPrice={flight.price} />
          </>
        )}
        <h3>Fares we have seen</h3>
        <HistoryChart history={history} />

        <h3>Get an alert</h3>
        <div className="track">
          <label>Tell me when the fare is at or below
            <input type="number" min="500" step="10" value={target} onChange={(e) => setTarget(e.target.value)} />
          </label>
          <button className="btn primary" onClick={track}>Track this flight</button>
        </div>
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="error" role="alert">{err}</p>}
      </section>
    </div>
  );
}
