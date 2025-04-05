from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "votes_db"

client = AsyncIOMotorClient(MONGO_URI)

'''
DB_SCHEMA
// 1) proposals collection
{
  "_id": "string (proposalId)",
  "address": "string",
  "description": "string",              // description in contract
  "malicious": "bool",
  "deadline": "Date",
  "tx_hash": "string",
  "created_at": "Date"
  "updated_at": "Date",
}

// 2) rewards collection
{
  "_id": "string",
  "address": "string",
  "proposal_id": "string",
  "amount": "number",
  "tx_hash": "string",       // on‐chain claim tx
  "claimed_at": "Date"
}
'''

def get_database() -> Database:
    """
    Get the MongoDB database instance.
    """
    return client[DATABASE_NAME]