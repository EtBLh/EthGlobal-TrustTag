import os

# Basic configuration settings for the application

# Blockchain & Smart Contract settings
BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://localhost:8545")
SMART_CONTRACT_ADDRESS = os.getenv("SMART_CONTRACT_ADDRESS", "0xYourSmartContractAddress")

# TEE Service settings
TEE_SERVICE_URL = os.getenv("TEE_SERVICE_URL", "http://localhost:8001/tee")

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "decentralized_labeling")