from typing import Dict, Any
from datetime import datetime
import random

# Replace with AWS IoT fetch
async def get_latest_sensor_data(user_id: str) -> Dict[str, Any]:
    return {
        "temperature": round(24 + random.uniform(-2, 2), 2),
        "humidity": round(68 + random.uniform(-5, 5), 1),
        "soil_moisture": int(520 + random.uniform(-80, 80)),
        "rainfall_mm": round(max(0, random.uniform(-0.2, 3.0)), 2),
        "gas_level": 140,
        "timestamp": datetime.now().isoformat() + "Z",
    }