# FareWatch: flight price predictor and tracker

Full-stack app that shows flight fares for a route and date, predicts what each fare *should* cost with a
machine-learning model, advises whether to book now or wait, and tracks fares over time with price-drop alerts.

| Layer | Tech |
|---|---|
| Frontend | React 18, Vite, Recharts (JavaScript) |
| API | Flask, Flask-CORS, APScheduler (Python) |
| Database | MongoDB (flights, price_history, tracked, alerts) |
| Data collection | `requests` + BeautifulSoup scraper, plus a simulated provider for offline demos |
| ML | scikit-learn: one-hot encoding + HistGradientBoostingRegressor on log(price) |

## Architecture

```
React (Vite :5173) --/api--> Flask (:5000) --> services/flights.py --> scraper/providers.py (simulated | live)
                                   |                  |
                                   |                  +--> ml/predictor.py (fair price, forecast, deal, advice)
                                   +--> MongoDB: flights, price_history, tracked, alerts
APScheduler job (every CHECK_INTERVAL_MIN) --> services/tracker.py --> re-fetch, store fare, raise alerts
```

## Run it

1. **MongoDB**: `docker compose up -d` (or point `MONGO_URI` at your own server / Atlas).
2. **Backend**
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   python -m ml.train        # optional: trains on first start anyway (about 10 seconds)
   python app.py             # http://localhost:5000
   ```
3. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev               # http://localhost:5173
   ```
4. **Tests** (no MongoDB needed, uses mongomock): `cd backend && pytest`

To see tracking move quickly in a demo, set `SIM_BUCKET_MIN=1` and `CHECK_INTERVAL_MIN=1` in `.env`,
track a flight, and press "Check prices now" a few times.

## Features

- Search by route, date and cabin; sort by price, best deal, duration, departure.
- Every result shows flight number, airline, times, duration, stops, **seats available**, price,
  the model's expected price and a deal badge.
- "Predict & track": expected-fare curve up to departure, buy/wait advice, observed price history, target-price alert.
- Standalone "Price predictor" for what-if fares.
- Watchlist with alerts; background job re-checks fares automatically.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health`, `/api/meta` | status + model metrics, dropdown values |
| GET | `/api/flights/search?source&destination&date&class&sort` | live/simulated fares + predictions |
| POST | `/api/predict` | what-if prediction, forecast, advice (`price` optional) |
| GET | `/api/history?flight_key=` | stored fare observations |
| GET/POST | `/api/track` | list / start tracking (`flight`, `target_price`) |
| DELETE | `/api/track/<id>` | stop tracking |
| POST | `/api/track/check` | re-check this visitor's tracked flights now |
| GET / POST | `/api/alerts`, `/api/alerts/read` | alerts and mark-read |

Visitors are identified by an anonymous `X-Client-Id` header generated in the browser. Add real authentication before deploying publicly.

## How the prediction works

Features: airline, source, destination, departure time-of-day bucket, cabin, stops, duration, days left, weekday, month.
The target is `log(price)`, which keeps percentage error even across cheap and expensive routes.

- **Expected fare** = model output for that flight. **Deal badge** compares the listed fare with it.
- **Forecast** re-runs the model for each remaining day before departure.
- **Advice**: book if departure is within 3 days or the forecast rises 5%+ in the next week; wait if the fare is 7%+
  above expected with more than 10 days left; otherwise keep watching.

### Important: training data and scraping

- Out of the box the model trains on **synthetic data** generated from airline-style pricing rules
  (`ml/synthetic.py`), so its metrics describe how well it learned those rules, not real-world accuracy.
  To use real data, train on a CSV with columns `airline, source_city, destination_city, departure_time, class,
  stops, duration, days_left, price` (the public Kaggle "Flight Price Prediction" layout works):
  `python -m ml.train --csv Clean_Dataset.csv`. Over time, export your own `price_history` collection to build a real training set.
- The default provider is **simulated** (results carry a "Demo data" tag). Most airline and travel sites forbid automated scraping and
  block bots. `LiveScraperProvider` is a configurable template (selectors and URL in `.env`); it honours robots.txt, rate-limits and
  falls back to simulated data on failure. Only point it at sources whose terms permit it, or swap in a licensed fares API
  (Amadeus, Skyscanner partners, etc.) by implementing `BaseProvider.search`.

## Project layout

```
backend/   app.py  config.py  db.py  ml/(constants, synthetic, train, predictor)  scraper/providers.py
           services/(flights, tracker)  tests/test_api.py
frontend/  src/(App, api, utils, styles.css)  src/components/(SearchForm, FlightList, FlightDetail, ForecastChart, PredictorForm, TrackedPanel)
```
