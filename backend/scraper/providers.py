"""Flight data providers.

* SimulatedProvider - deterministic schedule + fares that drift over time (works offline, great for demos)
* LiveScraperProvider - requests + BeautifulSoup against a site you configure in .env
  (checks robots.txt, rate-limits, identifies itself). Use only where the site's terms allow it.
* FallbackProvider - tries live first, falls back to simulated so the app never goes blank.
"""
import json
import random
import re
import time
from datetime import date, datetime, timedelta
from urllib import robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import config
from ml.constants import AIRLINES, AIRPORT_CODES, TIME_BUCKETS, flight_hours, time_bucket
from ml.synthetic import base_price

USER_AGENT = "FlightPriceTrackerBot/1.0 (+personal research project)"


def _fmt_time(minutes):
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class BaseProvider:
    name = "base"

    def search(self, source, destination, date_str, cls="Economy"):
        raise NotImplementedError


class SimulatedProvider(BaseProvider):
    name = "simulated"

    def search(self, source, destination, date_str, cls="Economy"):
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        days_left = max((d - date.today()).days, 1)
        rng = random.Random(f"{source}|{destination}|{date_str}|{cls}")
        bucket_no = int(time.time() // (60 * config.SIM_BUCKET_MIN))

        carriers = [a for a, v in AIRLINES.items() if cls == "Economy" or v["full_service"]]
        hours = sorted(rng.sample(range(5, 23), 8))
        flights = []
        for i, hour in enumerate(hours):
            airline = carriers[i % len(carriers)]
            stops = rng.choices([0, 1, 2], weights=[0.55, 0.38, 0.07])[0]
            dep_min = hour * 60 + rng.choice([0, 10, 20, 30, 40, 50])
            duration = round(flight_hours(source, destination, stops) + rng.uniform(-0.2, 0.4), 2)
            arr_min = dep_min + int(duration * 60)
            number = f"{AIRLINES[airline]['code']} {rng.randint(100, 989)}"
            key = f"{number}|{source}|{destination}|{date_str}|{cls}"

            bias = rng.uniform(0.95, 1.08)  # per-flight pricing quirk
            move = random.Random(f"{key}|{bucket_no}")  # market drift, changes every SIM_BUCKET_MIN
            demand = 0.93 + 0.14 * move.random()
            price = base_price(airline, source, destination, cls, stops, time_bucket(dep_min // 60 % 24),
                               days_left, d.weekday(), d.month) * bias * demand
            capacity = 170 if cls == "Economy" else 24
            fill = 0.15 + 0.85 * min(days_left, 45) / 45
            seats = int(capacity * fill * rng.uniform(0.35, 1.0)) + move.randint(-3, 3)
            flights.append({
                "flight_number": number, "airline": airline,
                "source": source, "destination": destination, "date": date_str, "class": cls,
                "departure_time": _fmt_time(dep_min), "arrival_time": _fmt_time(arr_min),
                "arrival_day_offset": arr_min // (24 * 60),
                "duration": duration, "stops": stops,
                "price": int(round(price, -1)), "seats": max(1, seats),
                "data_source": "simulated",
            })
        return flights


class LiveScraperProvider(BaseProvider):
    name = "live"

    def _allowed(self, url):
        parts = urlparse(url)
        rp = robotparser.RobotFileParser()
        rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
        try:
            rp.read()
        except Exception:
            return False
        return rp.can_fetch(USER_AGENT, url)

    @staticmethod
    def _text(card, selector):
        el = card.select_one(selector) if selector else None
        return el.get_text(" ", strip=True) if el else ""

    def search(self, source, destination, date_str, cls="Economy"):
        sel = config.SCRAPE_SELECTORS
        if not config.SCRAPE_URL_TEMPLATE or "card" not in sel:
            raise RuntimeError("Live scraper is not configured (SCRAPE_URL_TEMPLATE / SCRAPE_SELECTORS)")
        url = config.SCRAPE_URL_TEMPLATE.format(
            src=AIRPORT_CODES[source], dst=AIRPORT_CODES[destination], date=date_str)
        if not self._allowed(url):
            raise RuntimeError("robots.txt does not allow fetching this URL")
        time.sleep(config.SCRAPE_DELAY_SEC)
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        flights = []
        for card in soup.select(sel["card"]):
            price = re.sub(r"[^\d]", "", self._text(card, sel.get("price")))
            dep = re.search(r"\d{1,2}:\d{2}", self._text(card, sel.get("departure")))
            arr = re.search(r"\d{1,2}:\d{2}", self._text(card, sel.get("arrival")))
            if not (price and dep and arr):
                continue
            h1, m1 = map(int, dep.group().split(":"))
            h2, m2 = map(int, arr.group().split(":"))
            minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
            if minutes <= 0:
                minutes += 24 * 60
            stops_txt = self._text(card, sel.get("stops")).lower()
            stops = 0 if ("non" in stops_txt or not stops_txt) else int((re.findall(r"\d", stops_txt) or [1])[0])
            seats = re.sub(r"[^\d]", "", self._text(card, sel.get("seats")))
            airline = self._text(card, sel.get("airline"))
            flights.append({
                "flight_number": self._text(card, sel.get("flight_number")) or "N/A",
                "airline": airline if airline in AIRLINES else "IndiGo",
                "source": source, "destination": destination, "date": date_str, "class": cls,
                "departure_time": f"{h1:02d}:{m1:02d}", "arrival_time": f"{h2:02d}:{m2:02d}",
                "arrival_day_offset": 0, "duration": round(minutes / 60, 2), "stops": min(stops, 2),
                "price": int(price), "seats": int(seats) if seats else None,
                "data_source": "live",
            })
        if not flights:
            raise RuntimeError("No flights parsed - check SCRAPE_SELECTORS")
        return flights


class FallbackProvider(BaseProvider):
    name = "live+fallback"

    def __init__(self, primary, fallback):
        self.primary, self.fallback = primary, fallback

    def search(self, *args, **kwargs):
        try:
            return self.primary.search(*args, **kwargs)
        except Exception as exc:  # network, parsing, robots...
            print(f"[provider] live scrape failed ({exc}); using simulated data")
            return self.fallback.search(*args, **kwargs)


def get_provider():
    if config.PROVIDER == "live":
        return FallbackProvider(LiveScraperProvider(), SimulatedProvider())
    return SimulatedProvider()
