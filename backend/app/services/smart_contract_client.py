# backend/app/services/smart_contract_client.py

import os
import json
import asyncio
import logging
from typing import Any, Dict

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from app.config import BLOCKCHAIN_RPC_URL, VOTE_CONTRACT_ADDRESS, LABEL_CONTRACT_ADDRESS, BACKEND_WALLET_PRIVATE_KEY

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(__file__)  # backend/app/services

# ————————————————
# Correct ABI paths: up three levels to repo root, then into blockchain/TrustTag-contract/out/
vote_abi_path = os.path.abspath(os.path.join(
    BASE_DIR, os.pardir, os.pardir, os.pardir,
    "blockchain", "TrustTag-contract", "out",
    "TrustTagVoting.sol", "CommitRevealLabelVoting.json"
))
label_abi_path = os.path.abspath(os.path.join(
    BASE_DIR, os.pardir, os.pardir, os.pardir,
    "blockchain", "TrustTag-contract", "out",
    "TrustTagStorage.sol", "TagStorage.json"
))

logger.info(f"Looking for vote ABI at: {vote_abi_path}")
logger.info(f"Looking for label ABI at: {label_abi_path}")

if not os.path.isfile(vote_abi_path):
    raise FileNotFoundError(f"Vote ABI not found at {vote_abi_path}")
if not os.path.isfile(label_abi_path):
    raise FileNotFoundError(f"Label ABI not found at {label_abi_path}")

with open(vote_abi_path, "r") as f:
    vote_contract_abi = json.load(f)
with open(label_abi_path, "r") as f:
    label_contract_abi = json.load(f)

# ————————————————
# Web3 Setup
# ————————————————
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# vote_contract = w3.eth.contract(
#     address=Web3.to_checksum_address(VOTE_CONTRACT_ADDRESS),
#     abi=vote_contract_abi,
# )
# label_contract = w3.eth.contract(
#     address=Web3.to_checksum_address(LABEL_CONTRACT_ADDRESS),
#     abi=label_contract_abi,
# )


async def call_contract(method: str, args: Dict[str, Any]) -> str:
    vote_contract = w3.eth.contract(
        address=Web3.to_checksum_address(VOTE_CONTRACT_ADDRESS),
        abi=vote_contract_abi,
    )
    label_contract = w3.eth.contract(
        address=Web3.to_checksum_address(LABEL_CONTRACT_ADDRESS),
        abi=label_contract_abi,
    )
    fn = getattr(vote_contract.functions, method)
    txn = fn(**args).build_transaction({
        "from": w3.eth.default_account,
        "nonce": w3.eth.get_transaction_count(w3.eth.default_account),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
    })

    private_key = os.getenv("BACKEND_WALLET_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("BACKEND_WALLET_PRIVATE_KEY not set")

    signed = w3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    logger.info(f"Sent {method} tx: {tx_hex} args={args}")

    def _wait_receipt():
        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    receipt = await asyncio.get_event_loop().run_in_executor(None, _wait_receipt)
    if receipt.status != 1:
        raise RuntimeError(f"Transaction {tx_hex} failed: {receipt}")
    return tx_hex