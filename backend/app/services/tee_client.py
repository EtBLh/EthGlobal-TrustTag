# backend/app/services/tee_client.py

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

logger = logging.getLogger(__name__)


class TeeClient:
    @staticmethod
    async def compute_rewards(proposal_id: str, voters: List[str]) -> List[Dict]:
        """
        Compute rewards for a given proposal and list of voters using a mocked
        Bayesian Truth Serum (BTS) algorithm.
        
        This method retrieves votes from the database for the given proposal,
        then computes a score for each voter based on:
        
            Score_i = log( f(x_i) / p̄(x_i) ) + [ p_i(yes)*log( p̄(yes)/ f(yes) ) + p_i(no)*log( p̄(no)/ f(no) ) ]
        
        where:
          - f(x) is the actual frequency of answer x among all votes,
          - p̄(x) is the geometric mean of all participants' predictions for x,
          - p_i(yes) is the voter's prediction (as a fraction) for "yes",
          - p_i(no) is 1 - p_i(yes), and
          - x_i is the voter's actual vote (True for "yes", False for "no").
        
        Args:
            proposal_id: The ID of the proposal.
            voters: A list of voter addresses to include in the computation.
            
        Returns:
            A list of reward dictionaries.
            Example: [{"address": "0xRewardAddress1", "score": 10}, {"address": "0xRewardAddress2", "score": 5}]
        """
        # Retrieve votes for the given proposal from the database.
        db = await get_database()
        votes = await db["votes"].find({
            "proposal_id": proposal_id,
            "address": {"$in": voters}
        }).to_list(None)
        
        if not votes:
            logger.info(f"No votes found for proposal {proposal_id}")
            return []
        
        epsilon = 1e-6  # to avoid log(0)
        n = len(votes)
        
        # Count votes for "yes" and "no".
        count_yes = sum(1 for vote in votes if vote.get("vote") is True)
        count_no = n - count_yes
        
        # Compute actual frequencies (f) with smoothing.
        f_yes = max(count_yes / n, epsilon)
        f_no = max(count_no / n, epsilon)
        
        # Compute geometric means (p̄) of predictions for yes and no.
        # Each vote record has a "prediction" (integer 0-100), representing percentage for yes.
        sum_log_yes = 0.0
        sum_log_no = 0.0
        for vote in votes:
            # Convert prediction to a fraction.
            pred_fraction = vote.get("prediction", 50) / 100.0  # default to 50% if missing
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
            
            # Determine the voter's actual vote.
            if vote.get("vote") is True:
                # Voter answered "yes".
                term_a = math.log(f_yes / pbar_yes)
            else:
                # Voter answered "no".
                term_a = math.log(f_no / pbar_no)
            
            # Compute the weighted sum of predictions.
            term_b = p_i_yes * math.log(pbar_yes / f_yes) + p_i_no * math.log(pbar_no / f_no)
            
            score = term_a + term_b
            rewards.append({"address": address, "score": score})
        
        logger.info(f"Computed rewards for proposal {proposal_id} based on {n} votes")
        return rewards
    
    @staticmethod
    async def compute_rewards_op_tee(proposal_id: str, voters: List[str]) -> List[Dict]:
        """
        Compute rewards for a given proposal and list of voters via an actual TEE service call.
        *Without* storing the JSON on local disk, we build it in memory from DB data.

        Steps:
          1) Query DB for votes (matching `proposal_id` and `voters`).
          2) Build an in-memory JSON object: {"votes": [...] }.
          3) Upload that JSON to TEE /upload (multipart/form-data).
          4) Call TEE /vote to compute final user_scores.
          5) Parse and return a list [{"address": ..., "score": ...}].
        """

        # 1) Query the DB
        db = get_database()
        votes_cursor = db["votes"].find({
            "proposal_id": proposal_id,
            "address": {"$in": voters}
        })
        votes = await votes_cursor.to_list(None)

        if not votes:
            logger.info(f"No votes found for proposal {proposal_id} among {voters}.")
            return []

        # 2) Build the JSON structure in memory
        #    Adjust fields as needed based on how your DB columns map to the JSON schema.
        #    We'll assume "vote" is stored as boolean in DB, and we want "yes"/"no" in JSON, etc.
        payload_dict = {"votes": []}
        for v in votes:
            vote_str = "yes" if v["vote"] else "no"
            payload_dict["votes"].append({
                "user": v["address"],
                "vote": vote_str,
                "prediction_yes": float(v.get("prediction", 0.0)) / 100.0,
                "prediction_no": (100 - float(v.get("prediction", 0.0))) / 100.0,
            })

        # Convert dict -> bytes for uploading
        json_bytes = io.BytesIO(json.dumps(payload_dict).encode("utf-8"))

        # TEE endpoints
        TEE_BASE_URL = TEE_CLIENT_URL
        upload_url = f"{TEE_BASE_URL}/upload"
        vote_url = f"{TEE_BASE_URL}/vote"

        # We’ll name our in-memory file "<proposal_id>.json"
        # because the TEE might expect a ".json" extension.
        file_name = f"{proposal_id}.json"

        # 3) Use an async HTTP client to upload the in-memory JSON to TEE /upload
        async with httpx.AsyncClient() as client:
            try:
                # Create a "file" field that references our JSON in memory
                files = {
                    "file": (file_name, json_bytes, "application/json")
                }
                # TEE expects a form field "filename" that ends with .json
                data = {"filename": file_name}

                resp = await client.post(upload_url, files=files, data=data)
                resp.raise_for_status()
                logger.info(f"Uploaded JSON to TEE /upload as '{file_name}'.")
            except Exception as e:
                logger.error(f"Failed to upload JSON to TEE: {e}")
                return []

            # 4) Call TEE /vote with the same filename
            try:
                payload = {"json_file_name": file_name}
                resp = await client.post(vote_url, json=payload)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"TEE /vote request failed for '{file_name}': {e}")
                return []

            # 5) Parse the TEE’s /vote response
            #    Expected shape:
            #    {
            #      "result": {
            #        "user_scores": { "0x001": 96, "0x002": 93, ... },
            #        "signature": "...",
            #      }
            #    }
            tee_response = resp.json()
            result_obj = tee_response.get("result", {})
            user_scores = result_obj.get("user_scores", {})

            if not user_scores:
                logger.warning(f"No 'user_scores' found in TEE response: {tee_response}")
                return []

            # Convert user_scores into final list of { "address": x, "score": y }
            final_rewards = []
            for address in voters:
                score = user_scores.get(address, 0)
                final_rewards.append({"address": address, "score": score})

            return final_rewards