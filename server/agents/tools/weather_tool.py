from typing import Dict, Any

# Replace with OpenWeather/IMD
async def get_local_weather(location: str) -> Dict[str, Any]:
    return {
        "provider": "mock",
        "location": location,
        "now": {"temp_c": 29.0, "humidity": 72, "rain_mm": 0},
        "forecast_48h": "No rain expected, light winds, temp 26–33°C.",
    }