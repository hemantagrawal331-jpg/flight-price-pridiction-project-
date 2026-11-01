import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { prettyDate } from "./utils";
import SearchForm from "./components/SearchForm";
import FlightList from "./components/FlightList";
import FlightDetail from "./components/FlightDetail";
import PredictorForm from "./components/PredictorForm";
import TrackedPanel from "./components/TrackedPanel";

export default function App() {
  const [meta, setMeta] = useState(null);
  const [tab, setTab] = useState("search");
  const [flights, setFlights] = useState(null);
  const [query, setQuery] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [unread, setUnread] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => { api.meta().then(setMeta).catch((e) => setError(e.message)); }, []);
  useEffect(() => {
    const poll = () => api.alerts().then((a) => setUnread(a.unread)).catch(() => {});
    poll();
    const id = setInterval(poll, 30000);
    return () => clearInterval(id);
  }, []);

  const search = async (form) => {
    setLoading(true); setError(""); setQuery(form);
    try { setFlights((await api.search(form)).flights); }
    catch (e) { setError(e.message); setFlights(null); }
    finally { setLoading(false); }
  };
  const closeDetail = useCallback(() => setSelected(null), []);

  return (
    <>
      <header className="top">
        <h1>FareWatch</h1>
        <p>See what a flight should cost, then let us watch the price for you.</p>
        <nav aria-label="Sections">
          <button className={tab === "search" ? "on" : ""} onClick={() => setTab("search")}>Find flights</button>
          <button className={tab === "predict" ? "on" : ""} onClick={() => setTab("predict")}>Price predictor</button>
          <button className={tab === "watch" ? "on" : ""} onClick={() => setTab("watch")}>
            Watchlist{unread > 0 && <span className="count">{unread}</span>}
          </button>
        </nav>
      </header>

      <main>
        {!meta && !error && <p className="muted">Connecting…</p>}
        {error && !meta && <p className="error" role="alert">{error}</p>}
        {meta && tab === "search" && (
          <>
            <SearchForm meta={meta} loading={loading} onSearch={search} />
            {error && <p className="error" role="alert">{error}</p>}
            {flights && (
              <>
                <h2 className="results-title">{flights.length} flights, {query.source} to {query.destination}
                  <span className="muted"> · {prettyDate(query.date)}</span></h2>
                <FlightList flights={flights} onOpen={setSelected} />
              </>
            )}
            {!flights && !error && !loading && <p className="muted empty">Pick a route and date to see fares, seats left, and how each fare compares with what the model expects.</p>}
          </>
        )}
        {meta && tab === "predict" && <PredictorForm meta={meta} />}
        {meta && tab === "watch" && <TrackedPanel refreshKey={refreshKey} onAlertsChange={setUnread} />}
      </main>

      {selected && <FlightDetail flight={selected} onClose={closeDetail} onTracked={() => setRefreshKey((k) => k + 1)} />}
    </>
  );
}
