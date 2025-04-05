# tests/test_e2e_proposals.py

import pytest
from fastapi.testclient import TestClient

# Assume your main FastAPI app is in app/main.py
from app.main import app

# Monkey-patch call_contract in the proposals module so it returns a dummy hash.
from app.routes import propose

async def fake_call_contract(method, params):
    return "dummy_tx_hash"

propose.call_contract = fake_call_contract

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_create_and_list_proposal(client: TestClient):
    # Create a proposal via POST /api/propose
    payload = {
        "address": "0xTestAddress",
        "tag": "Test Proposal",
        "proof": "someproof",
        "malicious": False,
        "verifyPayload": {}
    }
    response = client.post("/api/propose", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "success"
    assert data["hash"] == "dummy_tx_hash"
    
    # Now get the list of proposals via GET /api/propose/list
    list_response = client.get("/api/propose/list")
    assert list_response.status_code == 200, list_response.text
    list_data = list_response.json()
    assert "list" in list_data
    # Check that the newly created proposal is present in the list.
    assert any(item["address"] == "0xTestAddress" and item["tag"] == "Test Proposal" 
               for item in list_data["list"])