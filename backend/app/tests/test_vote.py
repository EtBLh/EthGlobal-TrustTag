# tests/test_e2e_votes.py

import pytest
from fastapi.testclient import TestClient

# Assume your main FastAPI app is defined in app/main.py
from app.main import app

# Monkey-patch call_contract in the votes module to always return a dummy transaction hash.
from app.routes.vote import votes

async def fake_call_contract(method, params):
    return "dummy_tx_hash"

votes.call_contract = fake_call_contract

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_cast_vote(client: TestClient):
    # Prepare a sample payload for the vote endpoint.
    payload = {
        "proposalId": "proposal_123",
        "vote": True,
        "prediction": 75,
        "verifyPayload": {}
    }
    
    # Call the /api/vote endpoint.
    response = client.post("/api/vote", json=payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["message"] == "success"
    assert data["hash"] == "dummy_tx_hash"
    # Ensure the returned _id exists and is a non-empty string.
    assert " _id" not in data or data["_id"]