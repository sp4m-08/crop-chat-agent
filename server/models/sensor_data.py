from pydantic import BaseModel

class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: int
    gas_level: int
    timestamp: str