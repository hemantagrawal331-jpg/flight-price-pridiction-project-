import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { inr } from "../utils";

const axis = { fontSize: 12, fill: "#5b6b7a" };

/** Model-predicted fare for every remaining day before departure. */
export function ForecastChart({ forecast, listedPrice }) {
  return (
    <div className="chart" role="img" aria-label="Predicted fare by days before departure">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={forecast} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="#dde4ea" vertical={false} />
          <XAxis dataKey="days_left" reversed tick={axis} label={{ value: "Days before departure", position: "insideBottom", offset: -2, style: axis }} height={40} />
          <YAxis tick={axis} width={64} tickFormatter={inr} domain={["auto", "auto"]} />
          <Tooltip formatter={(v) => [inr(v), "Expected fare"]} labelFormatter={(d) => `${d} days before departure`} />
          {listedPrice ? <ReferenceLine y={listedPrice} stroke="#e39b1b" strokeDasharray="5 4" label={{ value: "This fare", fill: "#9a6606", fontSize: 12, position: "insideTopRight" }} /> : null}
          <Line type="monotone" dataKey="price" stroke="#0e7c86" strokeWidth={2.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Fares we actually observed while tracking (real snapshots from MongoDB). */
export function HistoryChart({ history }) {
  if (history.length < 2) {
    return <p className="muted">Tracked fares appear here once we have seen this flight at least twice. Start tracking, then use “Check prices now” on the Watchlist tab.</p>;
  }
  const data = history.map((h) => ({ ...h, label: new Date(h.ts).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) }));
  return (
    <div className="chart" role="img" aria-label="Observed fares over time">
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="#dde4ea" vertical={false} />
          <XAxis dataKey="label" tick={axis} minTickGap={40} />
          <YAxis tick={axis} width={64} tickFormatter={inr} domain={["auto", "auto"]} />
          <Tooltip formatter={(v, n) => [inr(v), n === "price" ? "Observed fare" : "Expected fare"]} />
          <Line type="stepAfter" dataKey="price" stroke="#12263a" strokeWidth={2.5} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="predicted_price" stroke="#0e7c86" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
