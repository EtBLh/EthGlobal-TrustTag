from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import get_database
from pymongo.collection import Collection

# Set '/votes' as the base route path for this router
vote_router = APIRouter(prefix="/votes")

@vote_router.get("")
async def list_votes(db=Depends(get_database)):
    """
    Retrieve all available votes from the database.
    """
    try:
        votes_collection: Collection = db["votes"]
        votes = await votes_collection.find().to_list(length=100)
        return votes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))