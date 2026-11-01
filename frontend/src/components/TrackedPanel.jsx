import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { inr, prettyDate } from "../utils";

export default function TrackedPanel({ refreshKey, onAlertsChange }) {
  const [items, setItems] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    try {
      const [t, a] = await Promise.all([api.tracked(), api.alerts()]);
      setItems(t.tracked); setAlerts(a.alerts); onAlertsChange(a.unread);
    } catch (e) { setErr(e.message); }
  }, [onAlertsChange]);

  useEffect(() => { load(); }, [load, refreshKey]);

  const check = async () => {
    setBusy(true); setNote(""); setErr("");
    try {
      const r = await api.checkNow();
      setNote(`Checked ${r.checked} flight${r.checked === 1 ? "" : "s"}; ${r.triggered} reached your target.`);
      await load();
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };
  const remove = async (id) => { await api.untrack(id); load(); };
  const markRead = async () => { await api.readAlerts(); load(); };

  return (
    <div className="watch">
      <section className="panel">
        <div className="row">
          <h2>Your watchlist</h2>
          <button className="btn" onClick={check} disabled={busy}>{busy ? "Checking…" : "Check prices now"}</button>
        </div>
        {note && <p className="ok">{note}</p>}
        {err && <p className="error" role="alert">{err}</p>}
        {items.length === 0 ? (
          <p className="muted">Nothing tracked yet. Search for a flight, open “Predict & track”, and set the fare you want.</p>
        ) : (
          <ul className="tracked">
            {items.map((t) => {
              const drop = t.initial_price - t.last_price;
              return (
                <li key={t.id}>
                  <div>
                    <strong>{t.airline} {t.flight_number}</strong>
                    <span className="muted">{t.source} to {t.destination} · {prettyDate(t.date)} · {t.class}</span>
                  </div>
                  <div className="nums">
                    <span>Now <b>{inr(t.last_price)}</b></span>
                    <span>Target <b>{inr(t.target_price)}</b></span>
                    <span className={drop > 0 ? "good-text" : drop < 0 ? "warn-text" : ""}>
                      {drop === 0 ? "No change" : drop > 0 ? `Down ${inr(drop)}` : `Up ${inr(-drop)}`} since tracking
                    </span>
                  </div>
                  <span className={`badge ${t.status === "triggered" ? "good" : "neutral"}`}>{t.status === "triggered" ? "Target reached" : t.status === "expired" ? "Departed" : "Watching"}</span>
                  <button className="link" onClick={() => remove(t.id)}>Stop tracking</button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="panel">
        <div className="row"><h2>Alerts</h2>{alerts.some((a) => !a.read) && <button className="link" onClick={markRead}>Mark all as read</button>}</div>
        {alerts.length === 0 ? <p className="muted">No alerts yet. We add one here when a tracked fare hits your target.</p> : (
          <ul className="alerts">
            {alerts.map((a) => <li key={a.id} className={a.read ? "" : "unread"}>{a.message}<time>{new Date(a.ts).toLocaleString("en-IN")}</time></li>)}
          </ul>
        )}
      </section>
    </div>
  );
}
