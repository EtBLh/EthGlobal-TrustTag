# tests/test_e2e_rewards.py

import uuid
import asyncio
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

# Import the main app and the get_database dependency.
from app.main import app
from app.db.mongodb import get_database
from app.routes import rewards

# --- Fake Database Implementation ---

class FakeRewardsCollection:
    def __init__(self):
        self.data = []

    async def insert_one(self, doc):
        self.data.append(doc)

    async def find(self, query: dict):
        # Naively filter the rewards based on query.
        results = []
        for doc in self.data:
            match = True
            for key, condition in query.items():
                if isinstance(condition, dict):
                    # Only handling $exists operator for 'claimed_at'
                    if "$exists" in condition:
                        exists = condition["$exists"]
                        if (key in doc) != exists:
                            match = False
                            break
                    else:
                        match = False
                        break
                else:
                    if doc.get(key) != condition:
                        match = False
                        break
            if match:
                results.append(doc)
        return FakeCursor(results)

    async def update_one(self, query: dict, update: dict):
        for doc in self.data:
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                # Only support the "$set" update operator.
                set_values = update.get("$set", {})
                for k, v in set_values.items():
                    doc[k] = v
                return

class FakeCursor:
    def __init__(self, data):
        self.data = data

    async def to_list(self, length: int = None):
        if length is None:
            return self.data
        return self.data[:length]

class FakeDatabase:
    def __init__(self):
        self.collections = {"rewards": FakeRewardsCollection()}

    def __getitem__(self, name):
        return self.collections[name]

fake_db = FakeDatabase()

# --- Dependency and Contract Overrides ---

# Override get_database to return our fake_db.
def fake_get_database():
    return fake_db

app.dependency_overrides[get_database] = fake_get_database

# Override call_contract in the rewards module to always return a dummy tx hash.
async def fake_call_contract(method, params):
    return "dummy_tx_hash"

rewards.call_contract = fake_call_contract

# Create a TestClient instance.
client = TestClient(app)

# --- End-to-End Tests ---

def test_get_rewards():
    """
    Test GET /api/rewards by prepopulating a reward and checking that it is returned.
    """
    # Clear the fake rewards collection.
    fake_db["rewards"].data.clear()
    
    reward_doc = {
        "_id": str(uuid.uuid4()),
        "address": "0xTestAddress",
        "amount": 10,
        "claimed_at": None,
        "tx_hash": None,
        "created_at": datetime.now(timezone.utc)
    }
    asyncio.get_event_loop().run_until_complete(fake_db["rewards"].insert_one(reward_doc))
    
    # Call GET /api/rewards with the address and a dummy verifyPayload.
    response = client.get("/api/rewards", params={"address": "0xTestAddress", "verifyPayload": "{}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "list" in data
    assert len(data["list"]) == 1
    assert data["list"][0]["address"] == "0xTestAddress"

def test_claim_rewards():
    """
    Test POST /api/rewards/claim by prepopulating an unclaimed reward, 
    calling the endpoint, and verifying that the reward is updated as claimed.
    """
    # Clear and then insert a fake reward.
    fake_db["rewards"].data.clear()
    reward_doc = {
        "_id": "proposal_1",
        "address": "0xTestAddress",
        "amount": 10,
        "claimed_at": None,
        "tx_hash": None,
        "created_at": datetime.now(timezone.utc)
    }
    asyncio.get_event_loop().run_until_complete(fake_db["rewards"].insert_one(reward_doc))
    
    # Call POST /api/rewards/claim.
    payload = {
        "address": "0xTestAddress",
        "verifyPayload": {}
    }
    response = client.post("/api/rewards/claim", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "tx_hashes" in data
    assert data["tx_hashes"].get("proposal_1") == "dummy_tx_hash"
    
    # Verify that the reward document has been updated.
    reward = None
    for doc in fake_db["rewards"].data:
        if doc["_id"] == "proposal_1":
            reward = doc
            break
    assert reward is not None
    assert reward["claimed_at"] is not None
    assert reward["tx_hash"] == "dummy_tx_hash"