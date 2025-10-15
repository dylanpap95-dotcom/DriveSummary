import os, requests, json

HOME_LAT, HOME_LON = 39.9790488, -75.1848477
WORK_LAT, WORK_LON = 39.68002035, -75.69237944
TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")

url = f"https://api.tomtom.com/routing/1/calculateRoute/{HOME_LAT},{HOME_LON}:{WORK_LAT},{WORK_LON}/json"
params = {"key": TOMTOM_API_KEY, "traffic": "true"}

print("🔍 Testing TomTom API call...")
print("URL:", url)
print("Params:", params)

try:
    r = requests.get(url, params=params, timeout=10)
    print("\nStatus:", r.status_code)
    data = r.json()
    print(json.dumps(data, indent=2)[:1000])  # Show first 1000 chars
    if "routes" in data:
        t = data["routes"][0]["summary"]["travelTimeInSeconds"]
        print(f"\n✅ Travel time: {t/60:.1f} minutes")
    else:
        print("\n⚠️ No routes found in response.")
except Exception as e:
    print("❌ Error:", e)