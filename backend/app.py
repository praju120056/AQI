# backend/app.py
import sys
import os

# Add the project root to system path so imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from backend.database import save_aqi_record, get_all_aqi_records
from backend.aqi_calculator import compute_final_aqi
from backend.config import OWM_API_KEY
import requests
from datetime import datetime, timezone

app = Flask(__name__)

@app.route('/')
def home():
    return "AQI Backend is Running! Use /api/fetch_city endpoints."

@app.route('/api/calculate_manual', methods=['POST'])
def handle_manual_calculation():
    data = request.json
    raw_values = {
        'pm25': data.get('pm25'), 'pm10': data.get('pm10'), 'no2': data.get('no2'),
        'o3': data.get('o3'), 'co': data.get('co'), 'so2': data.get('so2'),
        'nh3': data.get('nh3'), 'pb': data.get('pb')
    }
    result = compute_final_aqi(raw_values)
    result['source'] = data.get('source', 'manual_entry')
    result['timestamp'] = datetime.now(timezone.utc).isoformat()
    save_aqi_record(result.copy())
    return jsonify(result)

@app.route('/api/get_all_data', methods=['GET'])
def get_all_data():
    records = get_all_aqi_records(limit=1000)
    return jsonify(records)

# ---------------- new: /api/fetch_city ----------------
def geocode_city(city_name, limit=1):
    try:
        if not OWM_API_KEY:
            return None, None
        url = "http://api.openweathermap.org/geo/1.0/direct"
        r = requests.get(url, params={"q": city_name, "limit": limit, "appid": OWM_API_KEY}, timeout=8)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, None
        return data[0].get("lat"), data[0].get("lon")
    except Exception as e:
        print("Geocode error:", e)
        return None, None

def fetch_owm_air(lat, lon):
    try:
        if not OWM_API_KEY:
            return None
        url = "http://api.openweathermap.org/data/2.5/air_pollution"
        r = requests.get(url, params={"lat": lat, "lon": lon, "appid": OWM_API_KEY}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("OWM air fetch error:", e)
        return None

@app.route('/api/fetch_city', methods=['GET'])
def fetch_city_aqi():
    city = request.args.get('city') or request.args.get('q')
    if not city:
        return jsonify({"error": "Please provide ?city=<city name>"}), 400

    lat, lon = geocode_city(city)
    if lat is None or lon is None:
        return jsonify({"error": f"Could not geocode city: {city}"}), 404

    j = fetch_owm_air(lat, lon)
    if not j or "list" not in j or not j["list"]:
        return jsonify({"error": "No air pollution data available"}), 502

    components = j["list"][0].get("components", {})

    # --- CRITICAL FIX: CONVERT CO UNITS ---
    # OWM provides CO in µg/m3. CPCB Standard uses mg/m3.
    # 1 mg = 1000 µg. So we divide by 1000.
    co_in_ug = components.get("co")
    co_in_mg = co_in_ug / 1000.0 if co_in_ug is not None else None

    # Map OWM keys to our backend keys
    payload = {
        "pm25": components.get("pm2_5"), # Note OWM uses pm2_5
        "pm10": components.get("pm10"),
        "no2": components.get("no2"),
        "o3": components.get("o3"),
        "co": co_in_mg,  # <--- PASS THE CONVERTED VALUE HERE
        "so2": components.get("so2"),
        "nh3": components.get("nh3"),
        "pb": None,
        "source": f"OpenWeatherMap:{city}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    result = compute_final_aqi(payload)

    # Merge metadata
    # We save the converted CO value to DB so the graphs are consistent with the AQI logic
    result.update({
        "source": payload["source"],
        "timestamp": payload["timestamp"],
        "pm25_raw": payload["pm25"],
        "pm10_raw": payload["pm10"],
        "co_raw": co_in_mg, # <--- SAVE CONVERTED VALUE
        "no2_raw": payload["no2"],
        "so2_raw": payload["so2"],
        "o3_raw": payload["o3"],
        "nh3_raw": payload["nh3"],
        "pb_raw": None
    })

    save_aqi_record(result.copy())
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)