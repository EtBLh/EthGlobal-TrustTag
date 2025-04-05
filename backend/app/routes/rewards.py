from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import VoteContract  # Use the new VoteContract class

router = APIRouter(prefix="/api", tags=["rewards"])


class RewardsQuery(BaseModel):
    address: str
    verifyPayload: dict   # already verified by middleware


class ClaimRequest(BaseModel):
    address: str
    verifyPayload: dict   # already verified by middleware


class RewardsListResponse(BaseModel):
    list: list[dict]


@router.post("/rewards", response_model=RewardsListResponse)
async def get_rewards(q: RewardsQuery, db=Depends(get_database)):
    docs = await db["rewards"].find({"address": q.address}).to_list(length=100)
    return RewardsListResponse(list=docs)


@router.post("/rewards/claim")
async def claim_rewards(req: ClaimRequest, db=Depends(get_database)):
    docs = await db["rewards"].find({
        "address": req.address,
        "claimed_at": {"$exists": False}
    }).to_list(length=100)

    if not docs:
        raise HTTPException(404, "No rewards to claim")

    # Claim each reward individually
    tx_hashes = {}
    for doc in docs:
        proposal_id = doc["_id"]
        try:
            # Call the contract for each reward proposal separately using the new VoteContract class.
            # The claimReward function expects a single argument: proposalId.
            tx_hash = await VoteContract.call_contract("claimReward", {
                "proposalId": proposal_id
            })
        except Exception as e:
            raise HTTPException(500, f"Contract call failed for proposal {proposal_id}: {e}")

        tx_hashes[proposal_id] = tx_hash

        # Update the reward document as claimed
        await db["rewards"].update_one(
            {"_id": proposal_id},
            {"$set": {"tx_hash": tx_hash, "claimed_at": datetime.now(timezone.utc)}}
        )

    return {"tx_hashes": tx_hashes}