import os
import requests
from datetime import datetime, timedelta, timezone

# ======================
# CONFIGURATION
# ======================

# Your coordinates
HOME_LAT, HOME_LON = 39.9790488, -75.1848477
WORK_LAT, WORK_LON = 39.68002035, -75.69237944

# ntfy topic
TOPIC = "DriveSummary"

# API keys (fetched automatically from GitHub secrets)
TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
OWM_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
TM_API_KEY = os.environ.get("TICKETMASTER_API_KEY")

# ======================
# HELPER FUNCTIONS
# ======================

def fmt_dur(seconds):
    if not seconds:
        return "N/A"
    m = seconds // 60
    h, m = divmod(m, 60)
    return f"{h}h {m}m" if h else f"{m}m"

def ntfy_post(message):
    try:
        requests.post(f"https://ntfy.sh/{TOPIC}", data=message.encode("utf-8"))
    except Exception as e:
        print("Failed to send notification:", e)

# ======================
# API CALLS
# ======================

def get_travel_time(origin_lat, origin_lon, dest_lat, dest_lon):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
    params = {"key": TOMTOM_API_KEY, "traffic": "true"}
    resp = requests.get(url, params=params)
    try:
        return resp.json()["routes"][0]["summary"]["travelTimeInSeconds"]
    except Exception:
        return None

def get_weather_alerts(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "exclude": "minutely,hourly,daily,current"
    }
    resp = requests.get(url, params=params)
    return resp.json().get("alerts", [])

def get_ticketmaster_events(lat, lon):
    if not TM_API_KEY:
        return []
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TM_API_KEY,
        "latlong": f"{lat},{lon}",
        "radius": "25",
        "unit": "miles",
        "countryCode": "US",
        "size": 5,
        "sort": "date,asc"
    }
    resp = requests.get(url, params=params)
    events = []
    for e in resp.json().get("_embedded", {}).get("events", []):
        name = e.get("name", "Event")
        venue = (e.get("_embedded", {}).get("venues", [{}])[0]).get("name", "")
        date = e.get("dates", {}).get("start", {}).get("localDate", "")
        time = e.get("dates", {}).get("start", {}).get("localTime", "")
        events.append(f"{date} {time} — {name} @ {venue}")
    return events

# ======================
# MAIN LOGIC
# ======================

def main():
    to_work = get_travel_time(HOME_LAT, HOME_LON, WORK_LAT, WORK_LON)
    to_home = get_travel_time(WORK_LAT, WORK_LON, HOME_LAT, HOME_LON)
    alerts = get_weather_alerts(HOME_LAT, HOME_LON)
    events = get_ticketmaster_events(HOME_LAT, HOME_LON)

    msg = [
        "🚗 **Drive Summary**",
        f"To work: {fmt_dur(to_work)}",
        f"To home: {fmt_dur(to_home)}"
    ]

    if alerts:
        msg.append("\n🌧️ **Weather Alerts:**")
        for a in alerts:
            ev = a.get("event", "Alert")
            desc = (a.get("description") or "").strip().split("\n")[0]
            msg.append(f"• {ev}: {desc}")

    if events:
        msg.append("\n🎟️ **Nearby Events:**")
        for e in events:
            msg.append(f"• {e}")

    text = "\n".join(msg)
    print("\n--- DRIVE SUMMARY TEST OUTPUT ---\n")
    print(text)
    print("\n---------------------------------\n")
    # Commented out so it won’t ping your phone
    # ntfy_post(text)

if __name__ == "__main__":
    main()
