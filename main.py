#!/usr/bin/env python3
"""
DriveSummary — Jarvis Edition
- Traffic Context (Current vs Historic)
- Market Data (SPY, BTC)
- News Headlines (RSS)
- Rich Notifications (Maps Buttons, Priority)
"""

import os
import json
import requests
import feedparser
import yfinance as yf
from datetime import datetime, timezone

# ======================
# CONFIG
# ======================
# Coordinates (Defaults to Philadelphia area)
HOME_LAT = float(os.environ.get("HOME_LAT", "39.9790488"))
HOME_LON = float(os.environ.get("HOME_LON", "-75.1848477"))
WORK_LAT = float(os.environ.get("WORK_LAT", "39.68002035"))
WORK_LON = float(os.environ.get("WORK_LON", "-75.69237944"))

HOME = {"name": "Home", "lat": HOME_LAT, "lon": HOME_LON}
WORK = {"name": "Work", "lat": WORK_LAT, "lon": WORK_LON}

TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
TM_API_KEY = os.environ.get("TICKETMASTER_API_KEY")

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "DriveSummary")
SEND_NOTIFICATIONS = os.environ.get("SEND_NOTIFICATIONS", "0").lower() in ("1", "true", "yes", "on")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
REQUEST_TIMEOUT = 20

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
        r = requests.get(url, params=params or {}, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "DriveSummary/Jarvis"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def send_ntfy_rich(title, message, priority="default", tags=None, actions=None):
    """Sends a rich notification with buttons and styling."""
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": ",".join(tags) if tags else "",
    }
    if actions:
        headers["Actions"] = json.dumps(actions)
    
    try:
        r = requests.post(NTFY_URL, data=message.encode("utf-8"), headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Could not send notification: {e}")

# ======================
# DATA SOURCES
# ======================
def get_traffic_smart(a, b):
    """Returns (current_time, historic_time, delay_seconds)"""
    if not TOMTOM_API_KEY:
        return None, None, 0
    
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{a['lat']},{a['lon']}:{b['lat']},{b['lon']}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "routeType": "fastest",
        "travelMode": "car",
        "departAt": now_iso_utc(),
        "computeTravelTimeFor": "all" # Get historic and current
    }
    
    data = safe_get_json(url, params)
    if not data:
        return None, None, 0
        
    try:
        route = data.get("routes", [{}])[0]
        summary = route.get("summary", {})
        
        current = int(summary.get("travelTimeInSeconds", 0))
        historic = int(summary.get("historicTrafficTravelTimeInSeconds", current))
        delay = current - historic
        
        return current, historic, delay
    except Exception:
        return None, None, 0

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {"latitude": lat, "longitude": lon, "current": "temperature_2m,precipitation,weathercode"}
    d = safe_get_json(url, params)
    cur = (d or {}).get("current", {})
    
    code = cur.get("weathercode", 0)
    temp_c = cur.get("temperature_2m")
    temp_f = (temp_c * 9/5 + 32) if isinstance(temp_c, (int, float)) else None
    
    # Simple WMO map
    desc = "Clear"
    if code in [1, 2, 3]: desc = "Cloudy"
    elif code in [51, 53, 55, 61, 63, 65]: desc = "Rain"
    elif code in [71, 73, 75]: desc = "Snow"
    elif code >= 95: desc = "Storm"
    
    return {"temp": temp_f, "desc": desc, "code": code}

def get_markets():
    """Get SPY and BTC percent change."""
    try:
        tickers = yf.Tickers("SPY BTC-USD")
        res = []
        for symbol, name in [("SPY", "S&P"), ("BTC-USD", "BTC")]:
            hist = tickers.tickers[symbol].history(period="2d")
            if len(hist) >= 2:
                close = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change = ((close - prev) / prev) * 100
                icon = "🟢" if change >= 0 else "🔴"
                res.append(f"{icon} {name} {change:+.1f}%")
        return " | ".join(res)
    except Exception:
        return "Markets: N/A"

def get_news():
    """Get top 3 headlines from NPR."""
    try:
        feed = feedparser.parse("https://feeds.npr.org/1001/rss.xml")
        headlines = [entry.title for entry in feed.entries[:3]]
        return headlines
    except Exception:
        return []

def get_events(lat, lon):
    if not TM_API_KEY: return []
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TM_API_KEY, "latlong": f"{lat},{lon}", "radius": "20", "unit": "miles",
        "size": 3, "sort": "date,asc", "startDateTime": now_iso_utc()
    }
    data = safe_get_json(url, params)
    events = []
    for e in (data or {}).get("_embedded", {}).get("events", []):
        name = e.get("name")
        url = e.get("url")
        events.append((name, url))
    return events

# ======================
# MAIN
# ======================
def main():
    # 1. Determine Direction (Morning = To Work, Evening = To Home)
    hour = datetime.now().hour
    is_morning = 4 <= hour < 12
    
    origin = HOME if is_morning else WORK
    dest = WORK if is_morning else HOME
    direction_str = "To Work" if is_morning else "To Home"
    
    # 2. Fetch Data
    cur_time, hist_time, delay = get_traffic_smart(origin, dest)
    weather = get_weather(origin["lat"], origin["lon"])
    markets = get_markets()
    news = get_news()
    events = get_events(HOME["lat"], HOME["lon"]) if not is_morning else [] # Only show events in evening
    
    # 3. Analyze Traffic
    traffic_status = "🟢 Clear"
    priority = "default"
    if delay > 900: # 15 mins
        traffic_status = f"🔴 +{fmt_hm(delay)} Delay"
        priority = "high"
    elif delay > 300: # 5 mins
        traffic_status = f"🟡 +{fmt_hm(delay)} Busy"
    
    # 4. Build Message
    title = f"{traffic_status} {direction_str}"
    
    msg_lines = []
    msg_lines.append(f"⏱️ **{fmt_hm(cur_time)}** (Usual: {fmt_hm(hist_time)})")
    msg_lines.append(f"🌡️ {weather['temp']:.0f}°F {weather['desc']}")
    msg_lines.append(f"📊 {markets}")
    msg_lines.append("")
    
    if news:
        msg_lines.append("**📰 Briefing:**")
        for h in news:
            msg_lines.append(f"• {h}")
            
    if events:
        msg_lines.append("\n**🎟️ Tonight:**")
        for name, url in events:
            msg_lines.append(f"• [{name}]({url})")

    message = "\n".join(msg_lines)
    
    # 5. Actions (Buttons)
    maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin['lat']},{origin['lon']}&destination={dest['lat']},{dest['lon']}&travelmode=driving"
    actions = [
        {"action": "view", "label": "🚗 Start Navigation", "url": maps_url}
    ]

    # 6. Send
    print(f"--- {title} ---")
    print(message)
    
    if SEND_NOTIFICATIONS:
        send_ntfy_rich(title, message, priority=priority, tags=["car", "chart_with_upwards_trend"], actions=actions)

if __name__ == "__main__":
    main()