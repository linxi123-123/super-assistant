from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from server.config import get_settings

CITY_MAP = {
    "深圳": "Shenzhen", "新加坡": "Singapore", "北京": "Beijing", "上海": "Shanghai",
    "广州": "Guangzhou", "香港": "Hong Kong", "东京": "Tokyo", "纽约": "New York", "伦敦": "London",
}
CITY_COORDS = {
    "深圳": (22.5431, 114.0579), "新加坡": (1.3521, 103.8198), "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737), "广州": (23.1291, 113.2644), "香港": (22.3193, 114.1694),
    "东京": (35.6762, 139.6503), "纽约": (40.7128, -74.0060), "伦敦": (51.5072, -0.1276),
}
WEATHER_CODE_DESC = {0:"晴",1:"大部晴朗",2:"局部多云",3:"阴",45:"雾",48:"雾凇",51:"小毛毛雨",53:"中等毛毛雨",55:"大毛毛雨",61:"小雨",63:"中雨",65:"大雨",80:"阵雨",95:"雷暴"}

def detect_city_from_message(message: str) -> str:
    for city in CITY_MAP:
        if city in message: return city
    return ""

def _now() -> str: return datetime.now(timezone.utc).isoformat()

# ── Main weather entry ────────────────────────────────────

def get_weather(city: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.weather_provider == "openmeteo":
        return get_openmeteo_weather(city) if city else _need_city()
    if settings.weather_provider != "openweather":
        return _not_configured(settings.weather_provider)
    if not settings.openweather_api_key:
        return _not_configured("openweather")
    if not city:
        return _need_city()
    try:
        current = _openweather_current(city, settings)
        forecast = _openweather_forecast(city, settings)
        air = _openweather_air(city, settings)
        return _build_weather_result(city, current, forecast, air)
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"weather_error:{exc.__class__.__name__}"]}

def _need_city() -> dict[str, Any]:
    return {"data_status": "need_city", "items": [], "warnings": ["需要先补充城市，不能乱猜天气。"]}

def _not_configured(prov: str) -> dict[str, Any]:
    return {"data_status": "not_configured", "items": [], "warnings": [f"Weather provider {prov} not supported or not configured."]}

# ── OpenWeather ───────────────────────────────────────────

def _openweather_current(city: str, settings: Any) -> dict[str, Any]:
    r = httpx.get(f"{settings.openweather_base_url}/data/2.5/weather", params={"q": CITY_MAP.get(city, city), "appid": settings.openweather_api_key, "units": "metric", "lang": "zh_cn"}, timeout=10)
    r.raise_for_status()
    d = r.json()
    w = (d.get("weather") or [{}])[0]
    m = d.get("main") or {}
    wind = d.get("wind") or {}
    return {"description": w.get("description",""), "temp": m.get("temp"), "feels_like": m.get("feels_like"), "humidity": m.get("humidity"), "wind_speed": wind.get("speed"), "icon": w.get("icon","")}

def _openweather_forecast(city: str, settings: Any) -> list[dict[str, Any]]:
    lat, lon = CITY_COORDS.get(city, (22.5431, 114.0579))
    try:
        r = httpx.get(f"{settings.openweather_base_url}/data/2.5/forecast", params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key, "units": "metric", "lang": "zh_cn", "cnt": 24}, timeout=10)
        r.raise_for_status()
        items = r.json().get("list", [])
        daily = {}
        for item in items:
            dt = item.get("dt_txt", "")[:10]
            if dt not in daily:
                daily[dt] = {"date": dt, "temp_min": 99, "temp_max": -99, "descriptions": []}
            m = item.get("main", {})
            daily[dt]["temp_min"] = min(daily[dt]["temp_min"], m.get("temp_min", 99))
            daily[dt]["temp_max"] = max(daily[dt]["temp_max"], m.get("temp_max", -99))
            daily[dt]["descriptions"].append(((item.get("weather") or [{}])[0]).get("description", ""))
        result = []
        for d in sorted(daily.values(), key=lambda x: x["date"])[:5]:
            top = max(set(d["descriptions"]), key=d["descriptions"].count)
            result.append({"date": d["date"], "temp_min": round(d["temp_min"]), "temp_max": round(d["temp_max"]), "description": top})
        return result
    except Exception:
        return []

def _openweather_air(city: str, settings: Any) -> dict[str, Any] | None:
    lat, lon = CITY_COORDS.get(city, (22.5431, 114.0579))
    try:
        r = httpx.get(f"{settings.openweather_base_url}/data/2.5/air_pollution", params={"lat": lat, "lon": lon, "appid": settings.openweather_api_key}, timeout=8)
        r.raise_for_status()
        items = r.json().get("list", [])
        if not items: return None
        aqi = items[0]["main"]["aqi"]
        labels = {1:"优",2:"良",3:"轻度污染",4:"中度污染",5:"重度污染"}
        return {"aqi": aqi, "label": labels.get(aqi, str(aqi)), "pm25": items[0]["components"].get("pm2_5"), "pm10": items[0]["components"].get("pm10")}
    except Exception:
        return None

def _build_weather_result(city: str, current: dict, forecast: list, air: dict | None) -> dict[str, Any]:
    summary_parts = [f"{city}当前{city}天气：{current['description']}，{current['temp']}°C（体感{current['feels_like']}°C），湿度{current['humidity']}%"]
    if air:
        summary_parts.append(f"空气质量{air['label']}（AQI {air['aqi']}）")
    if forecast:
        lines = [f"{d['date'][5:]} {d['description']} {d['temp_min']}~{d['temp_max']}°C" for d in forecast[:4]]
        summary_parts.append("未来几天：" + "；".join(lines))
    item = {"source":"OpenWeather","source_name":"OpenWeather","provider":"openweather","title":f"{city}天气","summary":"。".join(summary_parts)+"。","url":"https://openweathermap.org","source_url":"https://openweathermap.org","timestamp":_now(),"fetched_at":_now(),"event_time":_now(),"confidence":"provider_reported","data_type":"weather","city":city,"temperature":current["temp"],"feels_like":current["feels_like"],"humidity":current["humidity"],"wind_speed":current["wind_speed"],"description":current["description"],"forecast":forecast,"air_quality":air}
    return {"data_status":"available","items":[item],"warnings":[]}

# ── Open-Meteo (free, no key) ─────────────────────────────

def get_openmeteo_weather(city: str) -> dict[str, Any]:
    settings = get_settings()
    coords = CITY_COORDS.get(city)
    if not coords: return {"data_status":"not_supported","items":[],"warnings":[f"Open-Meteo暂不支持：{city}"]}
    try:
        lat, lon = coords
        r = httpx.get(settings.openmeteo_base_url, params={"latitude":lat,"longitude":lon,"current":"temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m","daily":"temperature_2m_max,temperature_2m_min,weather_code","timezone":"auto","forecast_days":5}, timeout=10)
        r.raise_for_status()
        d = r.json()
        cur = d.get("current") or {}
        code = cur.get("weather_code")
        desc = WEATHER_CODE_DESC.get(code, f"代码{code}")
        daily = []
        for i in range(len(d.get("daily",{}).get("time",[]))):
            dc = d["daily"]["weather_code"][i]
            daily.append({"date":d["daily"]["time"][i],"temp_max":round(d["daily"]["temperature_2m_max"][i]),"temp_min":round(d["daily"]["temperature_2m_min"][i]),"description":WEATHER_CODE_DESC.get(dc,f"代码{dc}")})
        summary = f"{city}当前：{desc}，{cur.get('temperature_2m')}°C（体感{cur.get('apparent_temperature')}°C），湿度{cur.get('relative_humidity_2m')}%。"
        if daily:
            lines = [f"{d['date']} {d['description']} {d['temp_min']}~{d['temp_max']}°C" for d in daily[:4]]
            summary += "未来几天：" + "；".join(lines) + "。"
        item = {"source":"Open-Meteo","source_name":"Open-Meteo","provider":"openmeteo","title":f"{city}天气","summary":summary,"url":"https://open-meteo.com","source_url":"https://open-meteo.com","timestamp":cur.get("time",_now()),"fetched_at":_now(),"event_time":cur.get("time",_now()),"confidence":"provider_reported","data_type":"weather","city":city,"temperature":cur.get("temperature_2m"),"feels_like":cur.get("apparent_temperature"),"humidity":cur.get("relative_humidity_2m"),"wind_speed":cur.get("wind_speed_10m"),"description":desc,"forecast":daily,"air_quality":None}
        return {"data_status":"available","items":[item],"warnings":[]}
    except Exception as exc:
        return {"data_status":"error","items":[],"warnings":[f"weather_error:{exc.__class__.__name__}"]}
