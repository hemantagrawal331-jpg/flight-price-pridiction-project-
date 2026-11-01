import { DEALS, hoursLabel, inr, stopsLabel } from "../utils";

function Pass({ f, onOpen }) {
  const deal = DEALS[f.deal];
  const low = f.seats != null && f.seats <= 9;
  return (
    <article className="pass">
      <div className="pass-main">
        <header>
          <strong>{f.airline}</strong>
          <span className="flight-no">{f.flight_number}</span>
          {f.data_source === "simulated" && <span className="tag" title="Fares are generated for demonstration">Demo data</span>}
        </header>
        <div className="route">
          <div><b>{f.departure_time}</b><span>{f.source}</span></div>
          <div className="leg"><span>{hoursLabel(f.duration)}</span><i /><span>{stopsLabel(f.stops)}</span></div>
          <div><b>{f.arrival_time}{f.arrival_day_offset ? <sup>+{f.arrival_day_offset}</sup> : null}</b><span>{f.destination}</span></div>
        </div>
        <p className={low ? "seats low" : "seats"}>{f.seats == null ? "Seat count unavailable" : low ? `Only ${f.seats} seats left` : `${f.seats} seats available`}</p>
      </div>
      <div className="pass-stub">
        <div className="price">{inr(f.price)}</div>
        <div className="expected">Expected {inr(f.predicted_price)}</div>
        <span className={`badge ${deal.tone}`}>{deal.label}</span>
        <button className="btn" onClick={() => onOpen(f)}>Predict & track</button>
      </div>
    </article>
  );
}

export default function FlightList({ flights, onOpen }) {
  return <div className="passes">{flights.map((f) => <Pass key={f.flight_key} f={f} onOpen={onOpen} />)}</div>;
}
