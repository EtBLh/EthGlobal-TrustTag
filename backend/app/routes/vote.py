from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.db.mongodb import get_database
from pymongo.collection import Collection
from app.services.smart_contract_client import VoteContract, w3

router = APIRouter(prefix="/api", tags=["votes"])

class SignedVoteRequest(BaseModel):
    proposalId: str
    signed_txn: str | None = None  # Optional signed transaction
    vote: bool
    prediction: int
    salt: str
    verifyPayload: dict  # Already verified by middleware

class VoteResponse(BaseModel):
    _id: str
    message: str
    hash: str | None = None

@router.post("/vote", response_model=VoteResponse)
async def cast_vote(req: SignedVoteRequest, db=Depends(get_database)):
    tx_hex = None

    # Only submit signed_txn if provided
    if req.signed_txn:
        try:
            tx_hash = w3.eth.send_raw_transaction(
                bytes.fromhex(req.signed_txn[2:] if req.signed_txn.startswith('0x') else req.signed_txn)
            )
            tx_hex = tx_hash.hex()
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status != 1:
                raise HTTPException(500, f"Transaction {tx_hex} failed: {receipt}")

        except Exception as e:
            from traceback import format_exc
            print(format_exc())
            raise HTTPException(500, f"Contract call failed: {e}")

    # Record the vote in the database regardless of signed_txn presence
    coll: Collection = db["votes"]
    record_id = str(uuid.uuid4())

    await coll.insert_one({
        "_id": record_id,
        "proposal_id": req.proposalId,
        "vote": req.vote,
        "prediction": req.prediction,
        "salt": req.salt,
        "tx_hash": tx_hex,
        "created_at": datetime.now(timezone.utc),
    })

    return VoteResponse(_id=record_id, message="success", hash=tx_hex)
