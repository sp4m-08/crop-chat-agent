import httpx
from typing import Dict, Any
import os

OPENWEATHER_API = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_API = "https://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Set this in your .env file

async def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Fetches current weather from OpenWeather API for the given city name.
    Returns a dict with weather info or error.
    """
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(OPENWEATHER_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {
                "temp_c": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "rain_mm": data.get("rain", {}).get("1h", 0),
                "weather": data.get("weather", [{}])[0].get("description", "")
            }
        except Exception as e:
            return {"error": str(e)}
        


async def get_5day_forecast(location: str) -> Dict[str, Any]:
    """
    Fetches 5-day/3-hour forecast from OpenWeather API for the given city name.
    Returns a dict with forecast info or error.
    """
    params = {
        "q": location,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(OPENWEATHER_FORECAST_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            forecast_list = []
            for entry in data.get("list", []):
                forecast_list.append({
                    "dt_txt": entry.get("dt_txt"),
                    "temp_c": entry["main"]["temp"],
                    "humidity": entry["main"]["humidity"],
                    "rain_mm": entry.get("rain", {}).get("3h", 0),
                    "weather": entry.get("weather", [{}])[0].get("description", "")
                })
            return {"forecast": forecast_list}
        except Exception as e:
            return {"error": str(e)}
        
async def get_local_weather(location: str) -> Dict[str, Any]:
    """
    Combines current weather and 5-day forecast for the given city name.
    """
    now = await get_current_weather(location)
    forecast = await get_5day_forecast(location)
    return {
        "provider": "openweather",
        "location": location,
        "now": now,
        "forecast_5d": forecast.get("forecast", []),
        "forecast_error": forecast.get("error", "")
    }