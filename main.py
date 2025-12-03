#!/usr/bin/env python3
"""
DriveSummary — Final Automated Version
- Free data only (TomTom, Open-Meteo, NWS, Ticketmaster)
- Sends ntfy push to your topic (DriveSummary)
- Designed to run from GitHub Actions automatically
"""

import os
import requests
from datetime import datetime, timezone

# ======================
# CONFIG
# ======================
# Coordinates (Defaults to Philadelphia area if not set in env)
HOME_LAT = float(os.environ.get("HOME_LAT", "39.9790488"))
HOME_LON = float(os.environ.get("HOME_LON", "-75.1848477"))
WORK_LAT = float(os.environ.get("WORK_LAT", "39.68002035"))
WORK_LON = float(os.environ.get("WORK_LON", "-75.69237944"))

HOME = {"name": "Home", "lat": HOME_LAT, "lon": HOME_LON}
WORK = {"name": "Work", "lat": WORK_LAT, "lon": WORK_LON}

TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
TM_API_KEY = os.environ.get("TICKETMASTER_API_KEY")

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "DriveSummary")
# Send notifications if explicitly enabled or if running in GitHub Actions (CI=true)
SEND_NOTIFICATIONS = os.environ.get("SEND_NOTIFICATIONS", "0").lower() in ("1", "true", "yes", "on")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
REQUEST_TIMEOUT = 15

# ======================
# HELPERS
# ======================
def fmt_hm(seconds):
    if not seconds or seconds < 0:
        return "N/A"
    m = int(seconds) // 60
    h, m = divmod(m, 60)
    return f"{h}h {m}m" if h else f"{m}m"

def now_iso_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def safe_get_json(url, params=None):
    try:
        r = requests.get(url, params=params or {}, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "DriveSummary/Final"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def send_ntfy(message):
    try:
        r = requests.post(NTFY_URL, data=message.encode("utf-8"), timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Could not send notification: {e}")

# ======================
# API CALLS
# ======================
def tomtom_travel(a, b):
    if not TOMTOM_API_KEY:
        return None
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{a['lat']},{a['lon']}:{b['lat']},{b['lon']}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "routeType": "fastest",
        "travelMode": "car",
        "departAt": now_iso_utc(),
    }
    data = safe_get_json(url, params)
    if not data:
        return None
    try:
        summary = data.get("routes", [{}])[0].get("summary") or data.get("routes", [{}])[0].get("legs", [{}])[0].get("summary")
        return int(summary.get("travelTimeInSeconds", 0)) or None
    except Exception:
        return None

def open_meteo(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,precipitation,wind_speed_10m,weathercode"}
    d = safe_get_json(url, params)
    cur = (d or {}).get("current", {})
    return {
        "temp_c": cur.get("temperature_2m"),
        "precip_mm": cur.get("precipitation"),
        "wind_ms": cur.get("wind_speed_10m"),
        "code": cur.get("weathercode"),
    }

WMO = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Drizzle", 61: "Light rain",
    63: "Rain", 65: "Heavy rain", 71: "Snow", 95: "Thunderstorm"
}

def fmt_conditions(c):
    if not c: return "N/A"
    t = c.get("temp_c")
    temp_f = (t * 9/5 + 32) if isinstance(t, (int, float)) else None
    desc = WMO.get(c.get("code"), "—")
    wind_mph = (c.get("wind_ms") or 0) * 2.23694
    return f"{temp_f:.0f}°F, {desc}, wind {wind_mph:.0f} mph"

def nws_alerts(lat, lon):
    url = "https://api.weather.gov/alerts"
    params = {"point": f"{lat},{lon}", "status": "actual"}
    data = safe_get_json(url, params)
    features = (data or {}).get("features") or []
    return [f.get("properties", {}).get("headline") for f in features[:3] if f.get("properties")]

def ticketmaster_events(lat, lon, size=5):
    if not TM_API_KEY: return []
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TM_API_KEY, "latlong": f"{lat},{lon}", "radius": "25", "unit": "miles",
        "countryCode": "US", "size": size, "sort": "date,asc", "startDateTime": now_iso_utc(),
    }
    data = safe_get_json(url, params)
    events = []
    for e in (data or {}).get("_embedded", {}).get("events", []):
        name = e.get("name", "Event")
        venue = e.get("_embedded", {}).get("venues", [{}])[0].get("name", "")
        date = e.get("dates", {}).get("start", {}).get("localDate", "")
        time = e.get("dates", {}).get("start", {}).get("localTime", "")
        events.append(f"{date} {time} — {name}" + (f" @ {venue}" if venue else ""))
    return events

# ======================
# MAIN
# ======================
def main():
    today = datetime.now().strftime("%a %b %d")
    to_work = tomtom_travel(HOME, WORK)
    to_home = tomtom_travel(WORK, HOME)

    home_weather = open_meteo(HOME["lat"], HOME["lon"])
    work_weather = open_meteo(WORK["lat"], WORK["lon"])
    home_alerts = nws_alerts(HOME["lat"], HOME["lon"])
    work_alerts = nws_alerts(WORK["lat"], WORK["lon"])
    events = ticketmaster_events(HOME["lat"], HOME["lon"])

    lines = [
        f"🚗 Drive Summary ({today})",
        f"To work: {fmt_hm(to_work)} | To home: {fmt_hm(to_home)}",
        "",
        f"🌤️ Home: {fmt_conditions(home_weather)}",
        "⚠️ Alerts: " + (home_alerts[0] if home_alerts else "None"),
        "",
        f"🌤️ Work: {fmt_conditions(work_weather)}",
        "⚠️ Alerts: " + (work_alerts[0] if work_alerts else "None"),
    ]

    if events:
        lines.append("\n🎟️ Upcoming Events:")
        for e in events:
            lines.append(f"• {e}")

    lines.append("\n🗓️ Next checks: Mon-Fri 7:45 AM & 5 PM (ET)")
    text = "\n".join(lines)

    print(text)
    if SEND_NOTIFICATIONS:
        send_ntfy(text)

if __name__ == "__main__":
    main()