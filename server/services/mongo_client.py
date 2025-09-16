# from functools import lru_cache
# from motor.motor_asyncio import AsyncIOMotorClient
# import os

# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# DB_NAME = os.getenv("MONGO_DB", "crop_chat")

# @lru_cache
# def _client() -> AsyncIOMotorClient:
#     return AsyncIOMotorClient(MONGO_URI)

# def get_db():
#     return _client()[DB_NAME]