import { useState } from "react";
import { api } from "../api";
import { ADVICE, inr } from "../utils";
import { isoDate } from "../utils";
import { ForecastChart } from "./ForecastChart";

export default function PredictorForm({ meta }) {
  const [f, setF] = useState({ airline: meta.airlines[1], source: "Delhi", destination: "Bangalore", date: isoDate(30),
    departure_time: "09:00", stops: 0, class: "Economy", price: "" });
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      setRes(await api.predict({ ...f, stops: Number(f.stops), price: f.price ? Number(f.price) : undefined }));
    } catch (x) { setErr(x.message); setRes(null); } finally { setBusy(false); }
  };

  return (
    <div className="predictor">
      <form className="panel grid" onSubmit={submit}>
        <label>Airline<select value={f.airline} onChange={set("airline")}>{meta.airlines.map((a) => <option key={a}>{a}</option>)}</select></label>
        <label>From<select value={f.source} onChange={set("source")}>{meta.cities.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label>To<select value={f.destination} onChange={set("destination")}>{meta.cities.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label>Departure date<input type="date" min={isoDate(0)} value={f.date} onChange={set("date")} required /></label>
        <label>Departure time<input type="time" value={f.departure_time} onChange={set("departure_time")} required /></label>
        <label>Stops<select value={f.stops} onChange={set("stops")}><option value={0}>Non-stop</option><option value={1}>1 stop</option><option value={2}>2 stops</option></select></label>
        <label>Cabin<select value={f.class} onChange={set("class")}>{meta.classes.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label>Fare you were quoted (optional)<input type="number" min="500" placeholder="e.g. 5400" value={f.price} onChange={set("price")} /></label>
        <button className="btn primary" disabled={busy}>{busy ? "Predicting…" : "Predict fare"}</button>
      </form>
      {err && <p className="error" role="alert">{err}</p>}
      {res && (
        <section className="panel result">
          <div className="big">{inr(res.predicted_price)}<span>expected fare, {res.days_left} days before departure</span></div>
          {f.price && <div className={`advice ${ADVICE[res.action].tone}`}><strong>{ADVICE[res.action].label}</strong><span>{res.reason}</span></div>}
          <ForecastChart forecast={res.forecast} listedPrice={f.price ? Number(f.price) : null} />
        </section>
      )}
    </div>
  );
}
