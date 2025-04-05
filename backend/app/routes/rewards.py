from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from app.db.mongodb import get_database
from pymongo.collection import Collection

router = APIRouter(prefix="/api", tags=["rewards"])


class RewardsQuery(BaseModel):
    address: str


class ClaimRequest(BaseModel):
    reward_ids: List[str]  # List of reward document _ids


class RewardsListResponse(BaseModel):
    list: list[dict]


@router.post("/rewards", response_model=RewardsListResponse)
async def get_rewards(req: RewardsQuery, db=Depends(get_database)):
    docs = await db["rewards"].find({"address": req.address}).to_list(length=100)
    return RewardsListResponse(list=docs)


@router.post("/rewards/claim")
async def claim_rewards(req: ClaimRequest, db=Depends(get_database)):
    if not req.reward_ids:
        raise HTTPException(400, "No reward IDs provided")

    rewards: Collection = db["rewards"]
    updated_ids = []

    for reward_id in req.reward_ids:
        result = await rewards.update_one(
            {"_id": reward_id, "claimed_at": {"$exists": False}},
            {"$set": {"claimed_at": datetime.now(timezone.utc)}}
        )
        if result.modified_count:
            updated_ids.append(reward_id)

    if not updated_ids:
        raise HTTPException(404, "No rewards were updated (already claimed or not found)")

    return {"updated": updated_ids}