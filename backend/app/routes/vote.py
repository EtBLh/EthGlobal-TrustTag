from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid, hashlib

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import call_contract

router = APIRouter(prefix="/api", tags=["votes"])


class VoteRequest(BaseModel):
    proposalId: str
    vote: bool
    prediction: int = Field(..., ge=0, le=100)
    verifyPayload: dict    # already verified by middleware


class VoteResponse(BaseModel):
    _id: str
    message: str
    hash: str | None = None


@router.post("/vote", response_model=VoteResponse)
async def cast_vote(req: VoteRequest, db=Depends(get_database)):
    salt = uuid.uuid4().hex
    packed = f"{req.vote}{req.prediction}{salt}".encode()
    vote_hash = hashlib.sha3_256(packed).hexdigest()

    tx_req = {"proposalId": req.proposalId, "voteHash": vote_hash}
    try:
        tx_hash = await call_contract("commitVote", tx_req)
    except Exception as e:
        raise HTTPException(500, f"Contract call failed: {e}")

    coll: Collection = db["votes_salts"]
    record_id = str(uuid.uuid4())
    await coll.insert_one({
        "_id": record_id,
        "proposal_id": req.proposalId,
        "vote": req.vote,
        "prediction": req.prediction,
        "salt": salt,
        "tx_hash": tx_hash,
        "created_at": datetime.utcnow(),
    })

    return VoteResponse(_id=record_id, message="success", hash=tx_hash)