pip install -r requirements.txt


from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models import Vote
from app.db.mongodb import get_all_votes

router = APIRouter()

# In-memory storage for votes and salts (replace with database logic if needed)
votes_salts = {}

@router.get("/votes", response_model=List[Vote])
async def list_votes():
    """
    Retrieve all available votes from the database.
    """
    try:
        votes = await get_all_votes()
        return votes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vote")
async def create_vote(vote: str, salt: str):
    """
    Create a new vote with a salt.
    """
    if vote in votes_salts:
        raise HTTPException(status_code=400, detail="Vote already exists.")
    votes_salts[vote] = salt
    return {"vote": vote, "salt": salt}

@router.get("/vote")
async def get_vote(vote: str):
    """
    Retrieve a vote and its salt.
    """
    salt = votes_salts.get(vote)
    if salt is None:
        raise HTTPException(status_code=404, detail="Vote not found.")
    return {"vote": vote, "salt": salt}


REQUIREMENTS:
