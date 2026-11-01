import { useState } from "react";
import { isoDate } from "../utils";

export default function SearchForm({ meta, loading, onSearch }) {
  const [f, setF] = useState({ source: "Delhi", destination: "Mumbai", date: isoDate(14), class: "Economy", sort: "price" });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const swap = () => setF({ ...f, source: f.destination, destination: f.source });

  return (
    <form className="panel search" onSubmit={(e) => { e.preventDefault(); onSearch(f); }}>
      <label>From
        <select value={f.source} onChange={set("source")}>{meta.cities.map((c) => <option key={c}>{c}</option>)}</select>
      </label>
      <button type="button" className="swap" onClick={swap} aria-label="Swap origin and destination">⇄</button>
      <label>To
        <select value={f.destination} onChange={set("destination")}>{meta.cities.map((c) => <option key={c}>{c}</option>)}</select>
      </label>
      <label>Departure
        <input type="date" value={f.date} min={isoDate(0)} onChange={set("date")} required />
      </label>
      <label>Cabin
        <select value={f.class} onChange={set("class")}>{meta.classes.map((c) => <option key={c}>{c}</option>)}</select>
      </label>
      <label>Sort by
        <select value={f.sort} onChange={set("sort")}>
          <option value="price">Lowest price</option>
          <option value="deal">Best deal vs expected</option>
          <option value="duration">Shortest</option>
          <option value="departure">Earliest departure</option>
        </select>
      </label>
      <button className="btn primary" disabled={loading}>{loading ? "Searching…" : "Search flights"}</button>
    </form>
  );
}
