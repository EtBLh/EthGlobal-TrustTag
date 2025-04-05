import os
import json
import asyncio
import logging
from typing import Any, Dict

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

from app.config import (
    BLOCKCHAIN_RPC_URL,
    VOTE_CONTRACT_ADDRESS,
    LABEL_CONTRACT_ADDRESS,
    BACKEND_WALLET_PRIVATE_KEY,
)

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(__file__)  # backend/app/services

# ————————————————
# Correct ABI paths: up three levels to repo root, then into blockchain/TrustTag-contract/out/
vote_abi_path = os.path.abspath(os.path.join(
    BASE_DIR, os.pardir, os.pardir, os.pardir,
    "blockchain", "TrustTag-contract", "out",
    "TrustTagVoting.sol", "TrustTagVoting.json"
))
label_abi_path = os.path.abspath(os.path.join(
    BASE_DIR, os.pardir, os.pardir, os.pardir,
    "blockchain", "TrustTag-contract", "out",
    "TrustTagStorage.sol", "TrustTagStorage.json"
))

logger.info(f"Looking for vote ABI at: {vote_abi_path}")
logger.info(f"Looking for label ABI at: {label_abi_path}")

if not os.path.isfile(vote_abi_path):
    raise FileNotFoundError(f"Vote ABI not found at {vote_abi_path}")
if not os.path.isfile(label_abi_path):
    raise FileNotFoundError(f"Label ABI not found at {label_abi_path}")

with open(vote_abi_path, "r") as f:
    vote_contract_data = json.load(f)
    vote_contract_abi = vote_contract_data["abi"]

with open(label_abi_path, "r") as f:
    label_contract_data = json.load(f)
    label_contract_abi = label_contract_data["abi"]

# ————————————————
# Base class for common functionality
# ————————————————
class BaseContract:
    w3: Web3 = None

    @classmethod
    def _initialize_web3(cls):
        if cls.w3 is None:
            cls.w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC_URL))
            cls.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            if not cls.w3.eth.default_account:
                account = cls.w3.eth.account.from_key(BACKEND_WALLET_PRIVATE_KEY)
                cls.w3.eth.default_account = Web3.to_checksum_address(account.address)
                logger.info(f"Default account set to: {cls.w3.eth.default_account}")

# ————————————————
# VoteContract class
# ————————————————
class VoteContract(BaseContract):
    contract = None

    @classmethod
    def initialize(cls):
        cls._initialize_web3()
        cls.contract = cls.w3.eth.contract(
            address=Web3.to_checksum_address(VOTE_CONTRACT_ADDRESS),
            abi=vote_contract_abi,
        )
        logger.info("VoteContract initialized.")

    @classmethod
    async def call_contract(cls, method: str, args: Dict[str, Any]) -> str:
        fn = getattr(cls.contract.functions, method)
        txn = fn(**args).build_transaction({
            "from": cls.w3.eth.default_account,
            "nonce": cls.w3.eth.get_transaction_count(cls.w3.eth.default_account),
            "gas": 500000,  # Hardcoded gas value
            "gasPrice": cls.w3.eth.gas_price,
        })

        private_key = BACKEND_WALLET_PRIVATE_KEY
        if not private_key:
            raise RuntimeError("BACKEND_WALLET_PRIVATE_KEY not set")

        signed = cls.w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = cls.w3.eth.send_raw_transaction(signed.rawTransaction)
        tx_hex = tx_hash.hex()
        logger.info(f"Sent {method} tx: {tx_hex} args={args}")

        def _wait_receipt():
            return cls.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        receipt = await asyncio.get_event_loop().run_in_executor(None, _wait_receipt)
        if receipt.status != 1:
            raise RuntimeError(f"Transaction {tx_hex} failed: {receipt}")
        return tx_hex

    @classmethod
    async def call_view(cls, method: str, args: Dict[str, Any]) -> Any:
        fn = getattr(cls.contract.functions, method)
        def _call():
            return fn(**args).call({"from": cls.w3.eth.default_account})
        result = await asyncio.get_event_loop().run_in_executor(None, _call)
        return result

# ————————————————
# LabelContract class
# ————————————————
class LabelContract(BaseContract):
    contract = None

    @classmethod
    def initialize(cls):
        cls._initialize_web3()
        cls.contract = cls.w3.eth.contract(
            address=Web3.to_checksum_address(LABEL_CONTRACT_ADDRESS),
            abi=label_contract_abi,
        )
        logger.info("LabelContract initialized.")

    @classmethod
    async def call_contract(cls, method: str, args: Dict[str, Any]) -> str:
        fn = getattr(cls.contract.functions, method)
        txn = fn(**args).build_transaction({
            "from": cls.w3.eth.default_account,
            "nonce": cls.w3.eth.get_transaction_count(cls.w3.eth.default_account),
            "gas": 500000,  # Hardcoded gas value
            "gasPrice": cls.w3.eth.gas_price,
        })

        private_key = BACKEND_WALLET_PRIVATE_KEY
        if not private_key:
            raise RuntimeError("BACKEND_WALLET_PRIVATE_KEY not set")

        signed = cls.w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = cls.w3.eth.send_raw_transaction(signed.rawTransaction)
        tx_hex = tx_hash.hex()
        logger.info(f"Sent {method} tx: {tx_hex} args={args}")

        def _wait_receipt():
            return cls.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        receipt = await asyncio.get_event_loop().run_in_executor(None, _wait_receipt)
        if receipt.status != 1:
            raise RuntimeError(f"Transaction {tx_hex} failed: {receipt}")
        return tx_hex

# Initialize both contracts when the module is imported
VoteContract.initialize()
LabelContract.initialize()