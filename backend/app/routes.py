from fastapi import APIRouter, HTTPException, Depends
from app.db.mongodb import get_database
from pymongo.collection import Collection

router = APIRouter()

@router.get("/votes")
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

@router.post("/vote")
async def create_vote(vote: str, salt: str, db=Depends(get_database)):
    """
    Create a new vote with a salt and save it in MongoDB.
    """
    try:
        votes_collection: Collection = db["votes"]
        existing_vote = await votes_collection.find_one({"voteId": vote})
        if existing_vote:
            raise HTTPException(status_code=400, detail="Vote already exists.")
        
        vote_data = {"voteId": vote, "salt": salt}
        await votes_collection.insert_one(vote_data)
        return {"vote": vote, "salt": salt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vote")
async def get_vote(vote: str, db=Depends(get_database)):
    """
    Retrieve a vote and its salt from MongoDB.
    """
    try:
        votes_collection: Collection = db["votes"]
        vote_data = await votes_collection.find_one({"voteId": vote})
        if not vote_data:
            raise HTTPException(status_code=404, detail="Vote not found.")
        return {"vote": vote_data["voteId"], "salt": vote_data["salt"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))