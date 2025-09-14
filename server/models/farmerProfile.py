from pydantic import BaseModel, Field
from typing import List 
class FarmerProfile(BaseModel):
    farmer_id: str
    name: str = "Farmer"
    location: str = "Village A"
    land_size_acres: float = 2.0
    crops: List[str] = Field(default_factory=lambda: ["wheat"])
   