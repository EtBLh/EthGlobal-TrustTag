from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import time, re
from eth_account import Account
from eth_account.messages import encode_defunct
import re
from datetime import datetime
from web3 import Web3
from eth_account.messages import encode_defunct

from app.services.worldchain import Worldchain

# Constants from TypeScript
PREAMBLE = ' wants you to sign in with your Ethereum account:'
URI_TAG = 'URI: '
VERSION_TAG = 'Version: '
CHAIN_TAG = 'Chain ID: '
NONCE_TAG = 'Nonce: '
IAT_TAG = 'Issued At: '
EXP_TAG = 'Expiration Time: '
NBF_TAG = 'Not Before: '
RID_TAG = 'Request ID: '
ERC_191_PREFIX = '\x19Ethereum Signed Message:\n'

# SAFE contract ABI for isOwner function
SAFE_CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "isOwner",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def tagged(line, tag):
    """Extract value from a tagged line."""
    if line and tag in line:
        return line.replace(tag, '')
    else:
        raise ValueError(f"Missing '{tag}'")

def parse_siwe_message(input_string):
    """Parse a SIWE message into its components."""
    lines = iter(input_string.split('\n'))
    
    try:
        # Parse domain from first line
        first_line = next(lines)
        domain = first_line.replace(PREAMBLE, '')
        
        # Parse address from second line
        address = next(lines)
        
        # Skip empty line
        next(lines)
        
        # Check for statement (optional)
        next_value = next(lines)
        statement = None
        if next_value and not next_value.startswith(URI_TAG):
            statement = next_value
            next(lines)  # Skip line after statement
        
        # Parse required fields
        uri = tagged(next(lines), URI_TAG)
        version = tagged(next(lines), VERSION_TAG)
        chain_id = tagged(next(lines), CHAIN_TAG)
        nonce = tagged(next(lines), NONCE_TAG)
        issued_at = tagged(next(lines), IAT_TAG)
        
        # Parse optional fields
        expiration_time = None
        not_before = None
        request_id = None
        
        for line in lines:
            if line.startswith(EXP_TAG):
                expiration_time = tagged(line, EXP_TAG)
            elif line.startswith(NBF_TAG):
                not_before = tagged(line, NBF_TAG)
            elif line.startswith(RID_TAG):
                request_id = tagged(line, RID_TAG)
        
        # Create SIWE message data dictionary
        siwe_message_data = {
            'domain': domain,
            'address': address,
            'statement': statement,
            'uri': uri,
            'version': version,
            'chain_id': chain_id,
            'nonce': nonce,
            'issued_at': issued_at,
            'expiration_time': expiration_time,
            'not_before': not_before,
            'request_id': request_id
        }
        
        return siwe_message_data
    
    except StopIteration:
        raise ValueError("Invalid SIWE message format: incomplete message")

async def verify_siwe_message(payload, nonce, statement=None, request_id=None, rpc_url=None):
    """
    Verify a Sign-In with Ethereum (SIWE) message.
    
    Args:
        payload: Dict with 'message', 'signature', and 'address'
        nonce: Expected nonce value to validate
        statement: Expected statement text (optional)
        request_id: Expected request ID (optional)
        rpc_url: Ethereum RPC endpoint URL (optional)
        
    Returns:
        Dict with 'is_valid' and 'siwe_message_data'
        
    Raises:
        ValueError: If verification fails
    """
    message = payload.get('message')
    signature = payload.get('signature')
    address = payload.get('address')
    
    if not all([message, signature, address]):
        raise ValueError("Missing required fields in payload")
    
    # Parse the SIWE message
    siwe_message_data = parse_siwe_message(message)
    
    # Check expiration time
    if siwe_message_data.get('expiration_time'):
        expiration_time = datetime.fromisoformat(siwe_message_data['expiration_time'].replace('Z', '+00:00'))
        if expiration_time < datetime.now():
            raise ValueError("Expired message")
    
    # Check not_before time
    if siwe_message_data.get('not_before'):
        not_before = datetime.fromisoformat(siwe_message_data['not_before'].replace('Z', '+00:00'))
        if not_before > datetime.now():
            raise ValueError("Not Before time has not passed")
    
    # Validate nonce
    if nonce and siwe_message_data.get('nonce') != nonce:
        raise ValueError(f"Nonce mismatch. Got: {siwe_message_data.get('nonce')}, Expected: {nonce}")
    
    # Validate statement
    if statement and siwe_message_data.get('statement') != statement:
        raise ValueError(f"Statement mismatch. Got: {siwe_message_data.get('statement')}, Expected: {statement}")
    
    # Validate request ID
    if request_id and siwe_message_data.get('request_id') != request_id:
        raise ValueError(f"Request ID mismatch. Got: {siwe_message_data.get('request_id')}, Expected: {request_id}")
    
    # Initialize Web3 connection
    w3 = Web3(Web3.HTTPProvider(rpc_url or 'https://4801.rpc.thirdweb.com'))
    
    try:
        # Create a message object for signing
        message_obj = encode_defunct(text=message)
        
        # Ensure signature has 0x prefix
        if not signature.startswith('0x'):
            signature = '0x' + signature
        
        # Recover the signer's address
        recovered_address = w3.eth.account.recover_message(message_obj, signature=signature)
        
        # Check if recovered address is an owner using the Safe contract
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=SAFE_CONTRACT_ABI)
        is_owner = contract.functions.isOwner(recovered_address).call()
        
        if not is_owner:
            raise ValueError("Signature verification failed, invalid owner")
        
        return {
            'is_valid': True,
            'siwe_message_data': siwe_message_data
        }
    
    except Exception as e:
        raise ValueError(f"Signature verification failed: {str(e)}")

async def handle_siwe_auth(payload):
    try:
        # Get stored nonce from your database/cache
        stored_nonce = NONCE_STORAGE.get("nonce")
        
        # Verify the SIWE message
        result = await verify_siwe_message(
            payload=payload,
            nonce=stored_nonce,
            rpc_url="https://4801.rpc.thirdweb.com"
        )
        
        if result['is_valid']:
            # Authentication successful, create session/token
            user_address = result['siwe_message_data']['address']
            return {"success": True, "address": user_address}
        
    except ValueError as e:
        return {"success": False, "error": str(e)}

router = APIRouter(prefix="/api", tags=["world"])

class VerifyPayload(BaseModel):
    verifyPayload: dict

# this api only calls the wo
@router.post("/verify")
async def verify(payload: VerifyPayload):
    ok = await Worldchain.verify_worldid(payload.verifyPayload)
    if not ok:
        raise HTTPException(400, "WorldID verification failed")
    return {"verified": True}

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
    try:
        # Get the stored nonce
        stored_nonce = NONCE_STORAGE.get("nonce")
        if not stored_nonce:
            raise HTTPException(status_code=400, detail="No active nonce found. Please request a new nonce.")
        
        # Call the handler with the payload and stored nonce
        result = await handle_siwe_auth({
            "message": payload.message,
            "signature": payload.signature,
            "address": payload.address
        })
        
        if result.get("success"):
            # Clear the used nonce
            NONCE_STORAGE.pop("nonce", None)
            
            # In a real application, you would create a session or JWT token here
            return {
                "success": True, 
                "address": result["address"],
                "message": "Successfully authenticated with Ethereum"
            }
        else:
            raise HTTPException(
                status_code=401, 
                detail=f"Authentication failed: {result.get('error', 'Unknown error')}"
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing authentication: {str(e)}")