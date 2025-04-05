import math
import logging
import os
import io
import json
import httpx
from typing import List, Dict
from app.config import TEE_SERVICE_URL
from app.db.mongodb import get_database
from app.config import TEE_CLIENT_URL
from app.utils import get_logger

logger = get_logger(__name__)

class TeeClient:
    @staticmethod
    async def compute_rewards(proposal_id: str, voters: List[str]) -> List[Dict]:
        db = get_database()
        votes = await db["votes"].find({
            "proposal_id": proposal_id,
            "address": {"$in": voters}
        }).to_list(None)

        if not votes:
            logger.info(f"No votes found for proposal {proposal_id}")
            return []

        epsilon = 1e-6
        n = len(votes)

        count_yes = sum(1 for vote in votes if vote.get("vote") is True)
        count_no = n - count_yes

        f_yes = max(count_yes / n, epsilon)
        f_no = max(count_no / n, epsilon)

        sum_log_yes = 0.0
        sum_log_no = 0.0
        for vote in votes:
            pred_fraction = vote.get("prediction", 50) / 100.0
            p_i_yes = max(pred_fraction, epsilon)
            p_i_no = max(1 - pred_fraction, epsilon)
            sum_log_yes += math.log(p_i_yes)
            sum_log_no += math.log(p_i_no)

        pbar_yes = math.exp(sum_log_yes / n)
        pbar_no = math.exp(sum_log_no / n)

        rewards = []
        for vote in votes:
            address = vote.get("address")
            pred_fraction = vote.get("prediction", 50) / 100.0
            p_i_yes = max(pred_fraction, epsilon)
            p_i_no = max(1 - pred_fraction, epsilon)

            if vote.get("vote") is True:
                term_a = math.log(f_yes / pbar_yes)
            else:
                term_a = math.log(f_no / pbar_no)

            term_b = p_i_yes * math.log(pbar_yes / f_yes) + p_i_no * math.log(pbar_no / f_no)

            score = term_a + term_b
            rewards.append({"address": address, "score": score})

        logger.info(f"Computed rewards for proposal {proposal_id} based on {n} votes")
        return rewards

    @staticmethod
    async def compute_rewards_op_tee(proposal_id: str, voters: List[str]) -> List[Dict]:
        logger.info(f"Starting compute_rewards_op_tee for proposal_id={proposal_id}, voters={voters}")

        db = get_database()
        votes_cursor = db["votes"].find({
            "proposal_id": proposal_id,
            "address": {"$in": voters}
        })
        votes = await votes_cursor.to_list(None)
        logger.info(f"Retrieved {len(votes)} votes for proposal {proposal_id}")
        if not votes:
            logger.info(f"No votes found for proposal {proposal_id} among {voters}.")
            return []

        payload_dict = {"votes": []}
        for v in votes:
            vote_str = "yes" if v["vote"] else "no"
            payload_dict["votes"].append({
                "user": v["address"],
                "vote": vote_str,
                "prediction_yes": float(v.get("prediction", 0.0)) / 100.0,
                "prediction_no": (100 - float(v.get("prediction", 0.0))) / 100.0,
            })

        json_bytes = io.BytesIO(json.dumps(payload_dict).encode("utf-8"))

        TEE_BASE_URL = TEE_CLIENT_URL
        upload_url = f"{TEE_BASE_URL}/upload"
        vote_url = f"{TEE_BASE_URL}/vote"

        file_name = f"{proposal_id}.json"

        async with httpx.AsyncClient() as client:
            try:
                files = {
                    "file": (file_name, json_bytes, "application/json")
                }
                data = {"filename": file_name}

                logger.info(f"Uploading payload to TEE /upload: {file_name}")
                resp = await client.post(upload_url, files=files, data=data)
                resp.raise_for_status()
                logger.info(f"Successfully uploaded JSON to TEE /upload as '{file_name}'.")
            except Exception as e:
                logger.error(f"Failed to upload JSON to TEE: {e}")
                return []

            try:
                payload = {"json_file_name": file_name}
                logger.info(f"Requesting score calculation from TEE /vote for '{file_name}'")
                resp = await client.post(vote_url, json=payload)
                resp.raise_for_status()
                logger.info(f"TEE /vote responded successfully for '{file_name}'")
            except Exception as e:
                logger.error(f"TEE /vote request failed for '{file_name}': {e}")
                return []

            tee_response = resp.json()
            result_obj = tee_response.get("result", {})
            user_scores = result_obj.get("user_scores", {})

            if not user_scores:
                logger.warning(f"No 'user_scores' found in TEE response: {tee_response}")
                return []

            logger.info(f"TEE returned scores for {len(user_scores)} users")

            final_rewards = []
            for address in voters:
                score = user_scores.get(address, 0)
                final_rewards.append({"address": address, "score": score})

            return final_rewards
