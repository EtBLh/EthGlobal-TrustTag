import logging
from datetime import datetime, timezone
from typing import List

from pymongo.collection import Collection
from app.db.mongodb import get_database
from app.services.smart_contract_client import VoteContract
from app.services.tee_client import TeeClient

logger = logging.getLogger(__name__)

async def start_reveal_phase_job():
    db = get_database()
    proposals: Collection = db["proposals"]

    now = datetime.now(timezone.utc)
    to_start = await proposals.find({
        "phase": "Commit",
        "deadline": {"$lte": now}
    }).to_list()

    logger.info(f"[Reveal Job] Found {len(to_start)} proposals to transition to Reveal phase.")

    for p in to_start:
        proposal_id = p["_id"]
        reveal_deadline = int((now.timestamp() + 3600))

        logger.info(f"[Reveal Job] Processing proposal {proposal_id} — setting reveal deadline.")

        try:
            tx_hash = await VoteContract.call_contract("startRevealPhase", {
                "proposalId": proposal_id,
                "deadline": reveal_deadline
            })

            await proposals.update_one(
                {"_id": proposal_id},
                {"$set": {
                    "phase": "Reveal",
                    "deadline": datetime.fromtimestamp(reveal_deadline, tz=timezone.utc),
                    "updated_at": now
                }}
            )
            logger.info(f"[Reveal Job] Updated proposal {proposal_id} to 'Reveal' phase. TX: {tx_hash}")
        except Exception as e:
            logger.error(f"[Reveal Job] Failed for proposal {proposal_id}: {e}")


async def finalize_reward_job():
    db = get_database()
    proposals: Collection = db["proposals"]
    rewards: Collection = db["rewards"]

    now = datetime.now(timezone.utc)
    to_finalize = await proposals.find({
        "phase": "Reveal",
        "deadline": {"$lte": now}
    }).to_list(length=50)

    logger.info(f"[Finalize Job] Found {len(to_finalize)} proposals to finalize.")

    for p in to_finalize:
        proposal_id = p["_id"]
        logger.info(f"[Finalize Job] Finalizing proposal {proposal_id}")

        try:
            voters: List[str] = await VoteContract.call_view("getProposalVoters", {"proposalId": proposal_id})
            logger.info(f"[Finalize Job] Retrieved {len(voters)} voters for proposal {proposal_id}")
        except Exception as e:
            logger.warning(f"[Finalize Job] Could not retrieve voters for proposal {proposal_id}: {e}")
            continue

        try:
            tee_results = await TeeClient.compute_rewards_op_tee(proposal_id, voters)
            logger.info(f"[Finalize Job] Computed rewards for {len(tee_results)} voters on proposal {proposal_id}")
        except Exception as e:
            logger.error(f"[Finalize Job] TEE compute failed for proposal {proposal_id}: {e}")
            continue

        voter_list = [r["address"] for r in tee_results]
        reward_list = [r["score"] for r in tee_results]

        try:
            tx_hash = await VoteContract.call_contract("finalize", {
                "proposalId": proposal_id,
                "voterList": voter_list,
                "rewardList": reward_list
            })
            logger.info(f"[Finalize Job] Finalize transaction sent for proposal {proposal_id}. TX: {tx_hash}")
        except Exception as e:
            logger.error(f"[Finalize Job] Finalize contract call failed for proposal {proposal_id}: {e}")
            continue

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
            logger.info(f"[Finalize Job] Inserted {len(docs)} reward records for proposal {proposal_id}")

        await proposals.update_one(
            {"_id": proposal_id},
            {"$set": {"phase": "Finished", "updated_at": now}}
        )
        logger.info(f"[Finalize Job] Proposal {proposal_id} updated to 'Finished' phase.")