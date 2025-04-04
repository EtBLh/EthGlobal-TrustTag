from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "votes_db"

client = AsyncIOMotorClient(MONGO_URI)

def get_database() -> Database:
    """
    Get the MongoDB database instance.
    """
    return client[DATABASE_NAME]