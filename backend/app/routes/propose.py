from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import call_contract

router = APIRouter(prefix="/api", tags=["proposals"])


class ProposeRequest(BaseModel):
    address: str
    tag: str               # description in contract
    proof: str
    malicious: bool
    verifyPayload: dict    # already verified by middleware


class ProposeResponse(BaseModel):
    message: str
    hash: str | None = None


class ProposalListItem(BaseModel):
    _id: str
    address: str
    tag: str
    malicious: bool
    deadline: datetime


class ProposalListResponse(BaseModel):
    list: list[ProposalListItem]


@router.post("/propose", response_model=ProposeResponse)
async def propose_tag(req: ProposeRequest, db=Depends(get_database)):
    proposal_id = str(uuid.uuid4())
    deadline = datetime.utcnow() + timedelta(hours=24)

    tx_req = {
        "proposalId": proposal_id,
        "deadline": int(deadline.timestamp()),
        "target": req.address,
        "malicious": req.malicious,
        "description": req.tag,
    }

    try:
        tx_hash = await call_contract("createProposal", tx_req)
    except Exception as e:
        raise HTTPException(500, f"Contract call failed: {e}")

    coll: Collection = db["proposals"]
    await coll.insert_one({
        "_id": proposal_id,
        "address": req.address,
        "description": req.tag,
        "malicious": req.malicious,
        "deadline": deadline,
        "tx_hash": tx_hash,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    return ProposeResponse(message="success", hash=tx_hash)


@router.get("/propose/list", response_model=ProposalListResponse)
async def list_proposals(db=Depends(get_database)):
    docs = await db["proposals"].find().to_list(length=100)
    items = [
        ProposalListItem(
            _id=d["_id"],
            address=d["address"],
            tag=d["description"],
            malicious=d["malicious"],
            deadline=d["deadline"],
        )
        for d in docs
    ]
    return ProposalListResponse(list=items)