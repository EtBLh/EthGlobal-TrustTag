# backend/app/db/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "votes_db")

_client: AsyncIOMotorClient | None = None


async def connect_to_mongo():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    # Optionally, ping to verify connection
    await _client.admin.command("ping")


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        _client = None


def get_database() -> Database:
    """
    Return the Motor Database instance.
    """
    if _client is None:
        raise RuntimeError("Mongo client not initialized. Call connect_to_mongo() first.")
    return _client[DATABASE_NAME]