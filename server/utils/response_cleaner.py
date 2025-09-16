import re
from typing import Any, Dict

def format_market_price(market_price: Dict[str, Any]) -> str:
    """
    Formats the latest market price info for the LLM prompt.
    """
    data = market_price.get("data", [])
    if not data:
        return "Market price data not available."
    latest = data[0]
    return (
        f"Latest market price for {latest['Commodity']} in {latest['Market']} ({latest['Date']}):\n"
        f"Min Price: ₹{latest['Min Price']}, Max Price: ₹{latest['Max Price']}, Modal Price: ₹{latest['Modal Price']}"
    )

def format_weather(weather: Dict[str, Any]) -> str:
    """
    Formats current and 5-day forecast weather data for LLM prompt.
    """
    now = weather.get("now", {})
    forecast = weather.get("forecast_5d", [])
    lines = []
    if now:
        lines.append(
            f"Current weather in {weather.get('location','')}: "
            f"{now.get('temp_c','?')}°C, Humidity: {now.get('humidity','?')}%, "
            f"Rain (last hour): {now.get('rain_mm',0)} mm, {now.get('weather','')}"
        )
    if forecast:
        lines.append("5-day forecast (3-hour intervals):")
        for entry in forecast:  
            lines.append(
                f"{entry['dt_txt']}: {entry['temp_c']}°C, Humidity: {entry['humidity']}%, "
                f"Rain: {entry['rain_mm']} mm, {entry['weather']}"
            )
    elif weather.get("forecast_error"):
        lines.append(f"Forecast error: {weather['forecast_error']}")
    return "\n".join(lines)

def clean_response(text: str) -> str:
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[\*\-\•]+\s*", "", line)
        line = re.sub(r"\*+", "", line)
        lines.append(line)

    cleaned = " ".join(lines)

    # remove any Action: ... part
    cleaned = re.sub(r"Action:.*", "", cleaned, flags=re.I).strip()

    return cleaned
