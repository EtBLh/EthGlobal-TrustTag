# backend/app/jobs/scheduler.py

import logging
from datetime import datetime, timezone
from typing import List

from pymongo.collection import Collection
from web3 import Web3

from app.db.mongodb import get_database
from app.services.smart_contract_client import call_contract
from app.services.tee_client import TeeClient

logger = logging.getLogger(__name__)

async def start_reveal_phase_job():
    """
    Find proposals whose commit-deadline has passed and whose phase is still 'Commit'.
    For each, call the contract to start the reveal phase and set a new reveal-deadline.
    """
    db = await get_database()
    proposals: Collection = db["proposals"]

    now = datetime.now(timezone.utc)
    to_start = await proposals.find({
        "phase": "Commit",
        "deadline": {"$lte": now}
    }).to_list()

    for p in to_start:
        proposal_id = p["_id"]
        # e.g. 1 hour reveal window
        reveal_deadline = int((now.timestamp() + 3600))

        try:
            tx_hash = await call_contract("startRevealPhase", {
                "proposalId": proposal_id,
                "deadline": reveal_deadline
            })
            
            # update DB
            await proposals.update_one(
                {"_id": proposal_id},
                {"$set": {
                    "phase": "Reveal",
                    "deadline": datetime.fromtimestamp(reveal_deadline, tz=timezone.utc),
                    "updated_at": now
                }}
            )
            logger.info(f"start_reveal_phase_job: proposal={proposal_id} tx={tx_hash}")
        except Exception as e:
            logger.error(f"start_reveal_phase_job failed for {proposal_id}: {e}")


async def finalize_reward_job():
    """
    Find proposals whose reveal-deadline has passed and whose phase is 'Reveal'.
    For each, gather voters, compute rewards, call finalize on-chain, and persist rewards.
    """
    db = await get_database()
    proposals: Collection = db["proposals"]
    rewards: Collection = db["rewards"]

    now = datetime.now(timezone.utc)
    to_finalize = await proposals.find({
        "phase": "Reveal",
        "deadline": {"$lte": now}
    }).to_list(length=50)

    for p in to_finalize:
        proposal_id = p["_id"]

        # 1) fetch voters from chain
        try:
            voters: List[str] = await call_contract("getProposalVoters", {"proposalId": proposal_id})
        except Exception as e:
            logger.error(f"finalize_reward_job: getProposalVoters failed for {proposal_id}: {e}")
            continue

        # 2) compute rewards via TEE
        try:
            # tee_results = await TeeClient.compute_rewards(proposal_id, voters)
            tee_results = await TeeClient.compute_rewards_op_tee(proposal_id, voters)
            # tee_results: List[{"address": str, "score": int}]
        except Exception as e:
            logger.error(f"finalize_reward_job: compute_rewards failed for {proposal_id}: {e}")
            continue

        # 3) call finalize on-chain
        voter_list = [r["address"] for r in tee_results]
        reward_list = [r["score"] for r in tee_results]
        try:
            tx_hash = await call_contract("finalize", {
                "proposalId": proposal_id,
                "voterList": voter_list,
                "rewardList": reward_list
            })
            logger.info(f"finalize_reward_job: proposal={proposal_id} tx={tx_hash}")
        except Exception as e:
            logger.error(f"finalize_reward_job: finalize failed for {proposal_id}: {e}")
            continue

        # 4) persist rewards
        docs = []
        for r in tee_results:
            docs.append({
                "_id": f"{proposal_id}:{r['address']}",
                "address": r["address"],
                "proposal_id": proposal_id,
                "amount": r["score"],
                "tx_hash": tx_hash,
                "claimed_at": None
            })
        if docs:
            await rewards.insert_many(docs)

        # 5) update proposal phase to Finished
        await proposals.update_one(
            {"_id": proposal_id},
            {"$set": {"phase": "Finished", "updated_at": now}}
        )