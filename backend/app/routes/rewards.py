from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import call_contract

router = APIRouter(prefix="/api", tags=["rewards"])


class RewardsQuery(BaseModel):
    address: str
    verifyPayload: dict   # already verified by middleware


class ClaimRequest(BaseModel):
    address: str
    verifyPayload: dict   # already verified by middleware


class RewardsListResponse(BaseModel):
    list: list[dict]


@router.get("/rewards", response_model=RewardsListResponse)
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

    proposal_ids = [d["_id"] for d in docs]
    tx_hash = await call_contract("claimReward", {
        "address": req.address,
        "proposalIds": proposal_ids
    })

    await db["rewards"].update_many(
        {"_id": {"$in": proposal_ids}},
        {"$set": {"tx_hash": tx_hash, "claimed_at": datetime.utcnow()}}
    )

    return {"tx_hash": tx_hash}