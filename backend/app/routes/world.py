from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import time, re
from eth_account import Account
from eth_account.messages import encode_defunct

router = APIRouter(prefix="/api", tags=["scheduler"])

# In-memory storage for the nonce (for demo purposes only)
NONCE_STORAGE = {}

@router.get("/nonce")
async def get_nonce():
    try:
        # Generate a nonce; here we use the current timestamp as a string
        nonce = str(time.time())
        # Save the nonce in memory (associate with a session or user ID in production)
        NONCE_STORAGE["nonce"] = nonce
        return {"nonce": nonce}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Define the expected request body for SIWE completion
class SIWEPayload(BaseModel):
    message: str   # The full SIWE message string
    signature: str # The hex signature produced by the wallet
    address: str   # The wallet address (e.g., from World App)

@router.post("/complete-siwe")
async def complete_siwe(payload: SIWEPayload):
    """
    Verify the SIWE message by:
      1. Checking that the nonce in the SIWE message matches the stored nonce.
      2. Recovering the signer's address from the message and signature.
      3. Confirming that the recovered address matches the expected wallet address.
    """
    try:
        # 1. Extract nonce from the SIWE message.
        # Assumes the SIWE message includes a line like "Nonce: <nonce_value>"
        nonce_pattern = r"Nonce:\s*(\S+)"
        match = re.search(nonce_pattern, payload.message)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid SIWE message: nonce not found.")
        message_nonce = match.group(1)

        # Retrieve the stored nonce (in production, retrieve from persistent storage associated with the user)
        stored_nonce = NONCE_STORAGE.get("nonce")
        if not stored_nonce or stored_nonce != message_nonce:
            raise HTTPException(status_code=400, detail="Nonce mismatch or expired. Please fetch a new nonce.")

        # 2. Recover the signer's address from the SIWE message using eth_account.
        message = encode_defunct(text=payload.message)
        recovered_address = Account.recover_message(message, signature=payload.signature)

        # 3. Compare the recovered address with the address provided.
        if recovered_address.lower() != payload.address.lower():
            raise HTTPException(status_code=400, detail="Signature verification failed.")

        # If you have additional checks (e.g., checking message expiry), perform them here.
        # Optionally, clear the nonce from storage to prevent replays:
        NONCE_STORAGE.pop("nonce", None)

        # Successful verification: you can now create a session or return a token.
        return {"status": "success", "address": recovered_address}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
