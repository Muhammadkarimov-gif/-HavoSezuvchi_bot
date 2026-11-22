"""
api/weather.py — Open-Meteo weather + air quality fetching.

Uses:
  - https://api.open-meteo.com/v1/forecast        (weather)
  - https://air-quality-api.open-meteo.com/v1/air-quality  (PM2.5)

No API key required.
"""

import httpx
from typing import Optional

REGIONS: dict[str, dict] = {
    "tashkent":      {"name": "Toshkent",          "lat": 41.2995, "lon": 69.2401},
    "navoi":         {"name": "Navoiy",             "lat": 40.0840, "lon": 65.3791},
    "samarkand":     {"name": "Samarqand",          "lat": 39.6547, "lon": 66.9758},
    "bukhara":       {"name": "Buxoro",             "lat": 39.7747, "lon": 64.4286},
    "fergana":       {"name": "Farg'ona",           "lat": 40.3864, "lon": 71.7864},
    "andijan":       {"name": "Andijon",            "lat": 40.7821, "lon": 72.3442},
    "namangan":      {"name": "Namangan",           "lat": 41.0011, "lon": 71.6725},
    "kashkadarya":   {"name": "Qashqadaryo",        "lat": 38.8610, "lon": 65.7906},
    "surkhandarya":  {"name": "Surxondaryo",        "lat": 37.9400, "lon": 67.5700},
    "jizzakh":       {"name": "Jizzax",             "lat": 40.1158, "lon": 67.8422},
    "syrdarya":      {"name": "Sirdaryo",           "lat": 40.8390, "lon": 68.6630},
    "khorezm":       {"name": "Xorazm",             "lat": 41.5500, "lon": 60.6333},
    "karakalpakstan":{"name": "Qoraqalpog'iston",   "lat": 42.4600, "lon": 59.6166},
}

# WMO weather interpretation codes → Uzbek descriptions + emoji
WMO_CODES: dict[int, tuple[str, str]] = {
    0:  ("Ochiq osmon", "☀️"),
    1:  ("Asosan ochiq", "🌤️"),
    2:  ("Qisman bulutli", "⛅"),
    3:  ("Bulutli", "☁️"),
    45: ("Tuman", "🌫️"),
    48: ("Muzli tuman", "🌫️"),
    51: ("Yengil shivir", "🌦️"),
    53: ("O'rtacha shivir", "🌦️"),
    55: ("Kuchli shivir", "🌧️"),
    61: ("Yengil yomg'ir", "🌧️"),
    63: ("O'rtacha yomg'ir", "🌧️"),
    65: ("Kuchli yomg'ir", "🌧️"),
    71: ("Yengil qor", "🌨️"),
    73: ("O'rtacha qor", "🌨️"),
    75: ("Kuchli qor", "❄️"),
    80: ("Yomg'ir jalaси", "🌦️"),
    81: ("O'rtacha jala", "🌧️"),
    82: ("Kuchli jala", "⛈️"),
    95: ("Momaqaldiroq", "⛈️"),
    96: ("Do'l bilan momaqaldiroq", "⛈️"),
    99: ("Kuchli do'l bilan momaqaldiroq", "⛈️"),
}


def _pm25_to_aqi(pm25: float) -> int:
    """Convert PM2.5 (µg/m³) to US AQI using EPA linear interpolation."""
    breakpoints = [
        # (PM_low, PM_high, AQI_low, AQI_high)
        (0.0,   12.0,   0,   50),
        (12.1,  35.4,  51,  100),
        (35.5,  55.4, 101,  150),
        (55.5, 150.4, 151,  200),
        (150.5, 250.4, 201,  300),
        (250.5, 500.4, 301,  500),
    ]
    for pm_lo, pm_hi, aqi_lo, aqi_hi in breakpoints:
        if pm_lo <= pm25 <= pm_hi:
            aqi = ((aqi_hi - aqi_lo) / (pm_hi - pm_lo)) * (pm25 - pm_lo) + aqi_lo
            return round(aqi)
    if pm25 < 0:
        return 0
    return 500  # beyond scale


def pm25_to_clean_pct(pm25: float) -> int:
    """Return clean-air percentage (0-100) from PM2.5 value."""
    aqi = _pm25_to_aqi(pm25)
    return max(0, min(100, round(100 - (aqi / 500) * 100)))


def aqi_label(clean_pct: int) -> tuple[str, str]:
    """Return (Uzbek label, emoji) for a clean-air percentage."""
    if clean_pct >= 90:
        return ("Juda toza", "🌿")
    elif clean_pct >= 75:
        return ("Toza", "✅")
    elif clean_pct >= 60:
        return ("Qoniqarli", "🟡")
    elif clean_pct >= 40:
        return ("O'rtacha", "🟠")
    elif clean_pct >= 20:
        return ("Yomon", "🔴")
    else:
        return ("Xavfli", "☠️")


async def fetch_weather(region_key: str) -> Optional[dict]:
    """
    Fetch current weather for a region.

    Returns dict with keys:
      region_name, temp, feels_like, humidity, wind_speed,
      description, emoji, uv_index
    or None on error.
    """
    region = REGIONS.get(region_key)
    if not region:
        return None

    params = {
        "latitude": region["lat"],
        "longitude": region["lon"],
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code",
            "uv_index",
        ],
        "timezone": "Asia/Tashkent",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast", params=params
            )
            resp.raise_for_status()
            data = resp.json()

        cur = data["current"]
        code = int(cur.get("weather_code", 0))
        desc, emoji = WMO_CODES.get(code, ("Noma'lum", "🌡️"))

        return {
            "region_name": region["name"],
            "temp": round(cur["temperature_2m"]),
            "temperature": round(cur["temperature_2m"]),
            "feels_like": round(cur["apparent_temperature"]),
            "humidity": round(cur["relative_humidity_2m"]),
            "wind_speed": round(cur["wind_speed_10m"], 1),
            "description": desc,
            "emoji": emoji,
            "weather_code": code,
            "uv_index": round(cur.get("uv_index", 0), 1),
        }
    except Exception:
        return None


async def fetch_air_quality(region_key: str) -> Optional[dict]:
    """
    Fetch current air quality for a region.

    Returns dict with keys:
      region_name, pm25, aqi, clean_pct, label, label_emoji
    or None on error.
    """
    region = REGIONS.get(region_key)
    if not region:
        return None

    params = {
        "latitude": region["lat"],
        "longitude": region["lon"],
        "current": ["pm2_5"],
        "timezone": "Asia/Tashkent",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://air-quality-api.open-meteo.com/v1/air-quality",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        pm25 = data["current"]["pm2_5"]
        if pm25 is None:
            pm25 = 0.0
        pm25 = float(pm25)
        aqi = _pm25_to_aqi(pm25)
        clean_pct = pm25_to_clean_pct(pm25)
        label, label_emoji = aqi_label(clean_pct)

        return {
            "region_name": region["name"],
            "pm25": round(pm25, 1),
            "pm2_5": round(pm25, 1),
            "aqi": aqi,
            "clean_pct": clean_pct,
            "clean_air_pct": clean_pct,
            "label": label,
            "label_emoji": label_emoji,
        }
    except Exception:
        return None
