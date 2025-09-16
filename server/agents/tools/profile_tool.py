from typing import Dict, Any
from datetime import datetime

# Replace with real MongoDB call later
async def get_farmer_profile(user_id: str) -> Dict[str, Any]:
    return {
        "farmer_id": "farmer123",
        "name": "Ravi",
        "location": "kota",
        "land_size_acres": 3.2,
        "crops": ["wheat"],
        "updated_at": datetime.now().isoformat() + "Z",
    }