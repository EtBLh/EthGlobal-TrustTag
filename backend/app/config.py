import os

# Basic configuration settings for the application


BACKEND_WALLET_PRIVATE_KEY = os.getenv("BACKEND_WALLET_PRIVATE_KEY", "0x6c156ca8d84657e2072639f8cad5f8ef4e26e3bc64299231e10f45fe4e736f3c")

# Blockchain & Smart Contract settings
BLOCKCHAIN_RPC_URL = os.getenv("BLOCKCHAIN_RPC_URL", "http://localhost:8545")
VOTE_CONTRACT_ADDRESS = os.getenv("VOTE_CONTRACT_ADDRESS", "0x39CB184af026c05B6BcB507aA8365B2dbb377dcD")
LABEL_CONTRACT_ADDRESS = os.getenv("LABEL_CONTRACT_ADDRESS", "0xe9D4186dBB7aa4E4054e6F5176e0206f58b6F64e")

WORLDCOIN_APP_ID = os.getenv("WORLDCOIN_APP_ID", "app_fe9854eb1759ee4b1bd45aa9ca486891")

# TEE Service settings
TEE_SERVICE_URL = os.getenv("TEE_SERVICE_URL", "http://localhost:8001/tee")

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "trustag")