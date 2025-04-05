from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from web3 import Web3

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
    # Generate a random salt (32 hex characters, representing 16 bytes)
    salt = uuid.uuid4().hex  
    salt_bytes = bytes.fromhex(salt)
    
    # Use web3.py to replicate Solidity's keccak256(abi.encodePacked(...))
    vote_hash = Web3.solidityKeccak(
        ["bool", "uint256", "bytes16"],
        [req.vote, req.prediction, salt_bytes]
    ).hex()

    tx_req = {"proposalId": req.proposalId, "voteHash": vote_hash}
    try:
        tx_hash = await call_contract("commitVote", tx_req)
    except Exception as e:
        raise HTTPException(500, f"Contract call failed: {e}")

    coll: Collection = db["votes"]
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