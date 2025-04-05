import pytest
import uuid
from datetime import datetime, timedelta, timezone
import asyncio

from app.db.mongodb import get_database
from app.jobs.scheduler import start_reveal_phase_job, finalize_reward_job
from app.services.tee_client import TeeClient
from app.services.smart_contract_client import call_contract

# Save original implementations so we can restore them after tests.
_original_call_contract = call_contract
_original_compute_rewards = TeeClient.compute_rewards

# Fake external call implementations
async def fake_call_contract(method, params):
    if method == "startRevealPhase":
        return "start_reveal_dummy_tx_hash"
    elif method == "getProposalVoters":
        return ["0xVoter1", "0xVoter2"]
    elif method == "finalize":
        return "finalize_dummy_tx_hash"
    else:
        return "dummy_tx_hash"

async def fake_compute_rewards(proposal_id, voters):
    # Return a fixed reward for each voter.
    return [{"address": voter, "score": 10} for voter in voters]

# Register the asyncio marker (if not already registered in pytest.ini)
pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_start_reveal_phase_job():
    db = await get_database()
    proposals = db["proposals"]

    # Insert a test proposal in "Commit" phase with a past deadline.
    proposal_id = str(uuid.uuid4())
    past_deadline = datetime.now(timezone.utc) - timedelta(minutes=10)
    proposal_doc = {
        "_id": proposal_id,
        "address": "0xTestAddress",
        "description": "Test Proposal for reveal",
        "malicious": False,
        "deadline": past_deadline,
        "phase": "Commit",
        "tx_hash": "dummy",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await proposals.insert_one(proposal_doc)

    # Override the call_contract function to simulate the blockchain call.
    from app.services import smart_contract_client
    smart_contract_client.call_contract = fake_call_contract

    # Run the start_reveal_phase_job.
    await start_reveal_phase_job()

    # Verify that the proposal's phase is updated to "Reveal" and the deadline is extended.
    updated = await proposals.find({"_id": proposal_id}).to_list(1)
    assert len(updated) == 1
    updated_doc = updated[0]
    assert updated_doc["phase"] == "Reveal"
    new_deadline = updated_doc["deadline"]
    now = datetime.now(timezone.utc)
    assert new_deadline > now

    # Clean up: remove the test proposal.
    await proposals.delete_one({"_id": proposal_id})


@pytest.mark.asyncio
async def test_finalize_reward_job():
    db = await get_database()
    proposals = db["proposals"]
    rewards = db["rewards"]

    # Insert a test proposal in "Reveal" phase with a past deadline.
    proposal_id = str(uuid.uuid4())
    past_deadline = datetime.now(timezone.utc) - timedelta(minutes=10)
    proposal_doc = {
        "_id": proposal_id,
        "address": "0xTestAddress",
        "description": "Test Proposal for finalize",
        "malicious": False,
        "deadline": past_deadline,
        "phase": "Reveal",
        "tx_hash": "dummy",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    await proposals.insert_one(proposal_doc)

    # Remove any existing rewards for this proposal.
    await rewards.delete_many({"proposal_id": proposal_id})

    # Override external calls.
    from app.services import smart_contract_client
    smart_contract_client.call_contract = fake_call_contract
    TeeClient.compute_rewards = fake_compute_rewards

    # Run the finalize_reward_job.
    await finalize_reward_job()

    # Verify that the proposal's phase is updated to "Finished".
    updated = await proposals.find({"_id": proposal_id}).to_list(1)
    assert len(updated) == 1
    updated_doc = updated[0]
    assert updated_doc["phase"] == "Finished"

    # Verify that reward documents have been inserted.
    # Our fake getProposalVoters returns two voters, so we expect two reward docs.
    reward_docs = await rewards.find({"proposal_id": proposal_id}).to_list(10)
    assert len(reward_docs) == 2
    for doc in reward_docs:
        # Each reward _id should combine the proposal_id and the voter address.
        assert doc["_id"] == f"{proposal_id}:{doc['address']}"
        assert doc["amount"] == 10
        assert doc["tx_hash"] == "finalize_dummy_tx_hash"
        assert doc["claimed_at"] is None

    # Clean up: remove the test proposal and its rewards.
    await proposals.delete_one({"_id": proposal_id})
    await rewards.delete_many({"proposal_id": proposal_id})

    # Restore the original external call implementations.
    smart_contract_client.call_contract = _original_call_contract
    TeeClient.compute_rewards = _original_compute_rewards