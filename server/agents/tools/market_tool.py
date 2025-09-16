import httpx
from typing import Dict, Any

AGMARKET_API = "https://agmarket-api-main.onrender.com/request"

async def get_agri_market_price(commodity: str, state: str, market: str) -> Dict[str, Any]:
    params = {
        "commodity": commodity,
        "state": state,
        "market": market
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(AGMARKET_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            # You can adjust this structure as needed
            return {
                "commodity": commodity,
                "state": state,
                "market": market,
                "data": data
            }
        except Exception as e:
            return {
                "error": str(e),
                "commodity": commodity,
                "state": state,
                "market": market
            }