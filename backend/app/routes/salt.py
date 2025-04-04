from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import get_database
from pymongo.collection import Collection

# Set the base route path as '/salt'
salt_router = APIRouter(prefix="/salt")

@salt_router.post("")
async def stake_vote_salt(vote: str, salt: str, db=Depends(get_database)):
    """
    Stake a vote/salt pair by storing it in MongoDB.
    If the vote already exists, update the salt.
    """
    try:
        votes_collection: Collection = db["vote_salts"]
        existing_vote = await votes_collection.find_one({"voteId": vote})
        
        if existing_vote:
            # Update the salt for the existing vote
            await votes_collection.update_one(
                {"voteId": vote},
                {"$set": {"salt": salt}}
            )
        else:
            # Insert a new vote/salt pair
            vote_data = {"voteId": vote, "salt": salt}
            await votes_collection.insert_one(vote_data)
        
        return {"vote": vote, "salt": salt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@salt_router.get("")
async def get_vote_salt(vote: str, db=Depends(get_database)):
    """
    Retrieve the salt for a given vote from MongoDB.
    """
    try:
        votes_collection: Collection = db["vote_salts"]
        vote_data = await votes_collection.find_one({"voteId": vote})
        
        if not vote_data:
            raise HTTPException(status_code=404, detail="Vote not found.")
        
        return {"vote": vote_data["voteId"], "salt": vote_data["salt"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))