# backend/app/routes/propose.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid
from web3 import Web3  # Import Web3 to use its to_checksum_address function

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
    phase: str             # new field


class ProposalListResponse(BaseModel):
    list: list[ProposalListItem]


@router.post("/propose", response_model=ProposeResponse)
async def propose_tag(req: ProposeRequest, db=Depends(get_database)):
    proposal_id = str(uuid.uuid4())
    deadline = datetime.now(timezone.utc) + timedelta(hours=24)

    # Convert the provided address to a checksummed address.
    try:
        target_address = Web3.to_checksum_address(req.address)
    except Exception as e:
        raise HTTPException(400, f"Invalid address format: {req.address}")

    tx_req = {
        "proposalId": proposal_id,
        "deadline": int(deadline.timestamp()),
        "target": target_address,  # Use the checksummed address
        "malicious": req.malicious,
        "description": req.tag,
    }

    try:
        tx_hash = await call_contract("createProposal", tx_req)
    except Exception as e:
        from traceback import format_exc
        # Log the error for debugging
        print(format_exc())
        raise HTTPException(500, f"Contract call failed: {e}")

    coll: Collection = db["proposals"]
    await coll.insert_one({
        "_id": proposal_id,
        "address": target_address,
        "description": req.tag,
        "malicious": req.malicious,
        "deadline": deadline,
        "phase": "Commit",                  # initialize phase
        "tx_hash": tx_hash,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    return ProposeResponse(message="success", hash=tx_hash)


@router.get("/propose/list", response_model=ProposalListResponse)
async def list_proposals(db=Depends(get_database)):
    docs = await db["proposals"].find({"phase": "Commit"}).to_list(length=100)
    items = [
        ProposalListItem(
            _id=d["_id"],
            address=d["address"],
            tag=d["description"],
            malicious=d["malicious"],
            deadline=d["deadline"],
            phase=d.get("phase", "Unknown")
        )
        for d in docs
    ]
    return ProposalListResponse(list=items)