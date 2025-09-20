# Crop Chat Agent

An LLM-powered assistant for farmers that answers questions about market prices, weather, crop health, disease risk, and short‑term planning. Backend is FastAPI + LangGraph; data is fetched from OpenWeather and AgMarket APIs.

Live frontend
- https://sih-crop-frontend-sigma.vercel.app/

## Features
- Multi-intent routing: market, weather, health, disease, plan (supports combined queries)
- Location and crop taken from user message with fallback to profile
- Agri market prices via AgMarket API
- Weather: current + 5‑day/3‑hour forecast via OpenWeather
- Sensor-aware crop health and disease risk (LLM + tools)
- In‑memory chat history (no database required)
- Clean, farmer-friendly responses (response cleaner + formatters)

## Architecture
- Orchestrator (LangGraph): `server/agents/orchestrator.py`
  - Nodes (return deltas only; no in-place mutation):
    - chat_history: load & summarize past turns
    - farmer_interaction: detect multiple intents, extract crop from query
    - farmer_profile: load farmer profile (stub/dummy)
    - agmarket_price: extract location (query > profile), fetch mandi price
    - weather: extract location (query > profile), fetch current + 5‑day forecast
    - sensor_data: latest sensor readings (stub/dummy)
    - crop_health: agronomy advice from sensors + context
    - disease_prediction: near‑term disease risks
    - lifecycle_planning: short‑term operational plan
    - response: synthesize final answer using only relevant parts
- Tools
  - `weather_tool.py`: OpenWeather client + formatter
  - `market_tool.py`: AgMarket client
  - `history_tool.py`: in‑memory chat history
  - `profile_tool.py`, `sensor_tool.py`: stubs for now
- Utilities
  - `response_cleaner.py`: `clean_response`, `format_market_price`, `format_weather`
- LLM config
  - `server/agents/agent_roles.py` (uses Gemini via API key)

## Project structure
- server/
  - main.py — FastAPI app
  - routes/
    - chat.py — POST /chat endpoint
  - agents/
    - orchestrator.py — LangGraph graph and nodes
    - agent_roles.py — LLM setup (Gemini)
    - tools/
      - weather_tool.py — OpenWeather current + 5‑day forecast + formatter
      - market_tool.py — AgMarket API client
      - profile_tool.py — profile provider (stub)
      - sensor_tool.py — sensor provider (stub)
      - history_tool.py — in‑memory chat history
  - utils/
    - response_cleaner.py — cleaners/formatters
- requirements.txt
- .env

Ensure each package folder (server/, routes/, agents/, tools/, utils/) contains `__init__.py`.

## Requirements
- Python 3.10+
- API keys:
  - Google Gemini (LLM)
  - OpenWeather (free 5‑day/3‑hour forecast)



## Setup (Windows)
1) Create and activate a virtual environment, install dependencies:
````bash
py -m venv .venv
[activate](http://_vscodecontentref_/0)
pip install -r [requirements.txt](http://_vscodecontentref_/1)

