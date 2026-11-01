"""Domain constants shared by the ML code, the scraper and the API."""

CITIES = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"]
AIRPORT_CODES = {"Delhi": "DEL", "Mumbai": "BOM", "Bangalore": "BLR",
                 "Kolkata": "CCU", "Hyderabad": "HYD", "Chennai": "MAA"}

AIRLINES = {
    "Air India":         {"code": "AI", "mult": 1.12, "full_service": True},
    "IndiGo":            {"code": "6E", "mult": 0.97, "full_service": False},
    "Akasa Air":         {"code": "QP", "mult": 0.92, "full_service": False},
    "SpiceJet":          {"code": "SG", "mult": 0.90, "full_service": False},
    "Air India Express": {"code": "IX", "mult": 0.88, "full_service": False},
}
CLASSES = ["Economy", "Business"]
TIME_BUCKETS = ["Early_Morning", "Morning", "Afternoon", "Evening", "Night", "Late_Night"]

# approximate great-circle distances in km
_DIST = {
    ("Delhi", "Mumbai"): 1150, ("Delhi", "Bangalore"): 1750, ("Delhi", "Kolkata"): 1300,
    ("Delhi", "Hyderabad"): 1250, ("Delhi", "Chennai"): 1760, ("Mumbai", "Bangalore"): 840,
    ("Mumbai", "Kolkata"): 1660, ("Mumbai", "Hyderabad"): 620, ("Mumbai", "Chennai"): 1030,
    ("Bangalore", "Kolkata"): 1550, ("Bangalore", "Hyderabad"): 500, ("Bangalore", "Chennai"): 290,
    ("Kolkata", "Hyderabad"): 1190, ("Kolkata", "Chennai"): 1380, ("Hyderabad", "Chennai"): 520,
}


def distance(a, b):
    return _DIST.get((a, b)) or _DIST.get((b, a))


def time_bucket(hour):
    if 4 <= hour < 8:
        return "Early_Morning"
    if 8 <= hour < 12:
        return "Morning"
    if 12 <= hour < 16:
        return "Afternoon"
    if 16 <= hour < 20:
        return "Evening"
    if 20 <= hour < 24:
        return "Night"
    return "Late_Night"


def flight_hours(source, destination, stops=0):
    """Rough block time in hours."""
    return round(distance(source, destination) / 750 + 0.6 + 2.2 * stops, 2)
