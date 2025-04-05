import os

# Basic configuration settings for the application


BACKEND_WALLET_PRIVATE_KEY = os.getenv("BACKEND_WALLET_PRIVATE_KEY", "136da899f326e8919b396fc2f37e01397091a9bec00e86eb7e1d990ea738ed53")

# Blockchain & Smart Contract settings
BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://localhost:8545")
VOTE_CONTRACT_ADDRESS = os.getenv("VOTE_CONTRACT_ADDRESS", "0xYourSmartContractAddress")
LABEL_CONTRACT_ADDRESS = os.getenv("LABEL_CONTRACT_ADDRESS", "0xYourLabelContractAddress")

WORLDCOIN_APP_ID = os.getenv("WORLDCOIN_APP_ID", "app_fe9854eb1759ee4b1bd45aa9ca486891")

# TEE Service settings
TEE_SERVICE_URL = os.getenv("TEE_SERVICE_URL", "http://localhost:8001/tee")

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trustag")