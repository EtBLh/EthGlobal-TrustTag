from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid
from web3 import Web3

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import w3

router = APIRouter(prefix="/api", tags=["proposals"])

class ProposeRequest(BaseModel):
    address: str
    tag: str
    proof: str
    malicious: bool
    # verifyPayload: dict
    signed_txn: str | None = None  # Optional signed transaction

class ProposeResponse(BaseModel):
    message: str
    hash: str | None = None

class ProposalListItem(BaseModel):
    id: str
    address: str
    tag: str
    malicious: bool
    proof: str
    deadline: datetime
    phase: str

class ProposalListResponse(BaseModel):
    list: list[ProposalListItem]

@router.post("/propose", response_model=ProposeResponse)
async def propose_tag(req: ProposeRequest, db=Depends(get_database)):
    proposal_id = str(uuid.uuid4())
    deadline = datetime.now(timezone.utc) + timedelta(hours=24)

    try:
        target_address = Web3.to_checksum_address(req.address)
    except Exception:
        raise HTTPException(400, f"Invalid address format: {req.address}")

    tx_hex = None

    # Only submit the signed transaction if provided
    if req.signed_txn:
        try:
            signed_txn_bytes = bytes.fromhex(req.signed_txn.replace('0x', ''))
            tx_hash = w3.eth.send_raw_transaction(signed_txn_bytes)
            tx_hex = tx_hash.hex()
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.status != 1:
                raise RuntimeError(f"Transaction {tx_hex} failed: {receipt}")
        except Exception as e:
            from traceback import format_exc
            print(format_exc())
            raise HTTPException(500, f"Transaction submission failed: {e}")

    coll: Collection = db["proposals"]
    await coll.insert_one({
        "_id": proposal_id,
        "id": proposal_id,
        "address": target_address,
        "description": req.tag,
        "malicious": req.malicious,
        "proof": req.proof,
        "deadline": deadline,
        "phase": "Commit",
        "tx_hash": tx_hex,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    return ProposeResponse(message="success", hash=tx_hex)

@router.get("/propose/list", response_model=ProposalListResponse)
async def list_proposals(db=Depends(get_database)):
    docs = await db["proposals"].find().to_list(length=100)
    items = [
        ProposalListItem(
            id=d["_id"],
            _id=d["_id"],
            address=d["address"],
            tag=d.get("description", d.get("tag", "Unknown")),
            malicious=d["malicious"],
            deadline=d["deadline"],
            proof=d.get("proof", ""),
            phase=d.get("phase", "Unknown")
        )
        for d in docs
    ]
    return ProposalListResponse(list=items)