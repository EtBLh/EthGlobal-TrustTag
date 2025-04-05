# backend/app/services/tee_client.py

import math
import logging
from typing import List, Dict
from app.config import TEE_SERVICE_URL
from app.db.mongodb import get_database

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
    
    '''
    @staticmethod
    async def compute_rewards(proposal_id: str, voters: List[str]) -> List[Dict]:
        """
        Compute rewards for a given proposal and list of voters via the TEE service.
        
        In a production environment, this method would POST the payload to your TEE service.
        Here, it simulates a response for demonstration purposes.
        
        Args:
            proposal_id: The ID of the proposal.
            voters: A list of voter addresses.
            
        Returns:
            A list of reward dictionaries.
            Example: [{"address": "0xRewardAddress1", "score": 10}, {"address": "0xRewardAddress2", "score": 5}]
        """
        payload = {
            "proposalId": proposal_id,
            "voters": voters
        }
        async with aiohttp.ClientSession() as session:
            try:
                # In a real implementation, you might uncomment the following lines:
                # async with session.post(TEE_SERVICE_URL, json=payload) as response:
                #     response_data = await response.json()
                # Simulated TEE response:
                response_data = {
                    "rewards": [
                        {"address": "0xRewardAddress1", "score": 10},
                        {"address": "0xRewardAddress2", "score": 5},
                    ]
                }
                logger.info(f"TEE service simulated response for proposal {proposal_id}")
                return response_data["rewards"]
            except Exception as e:
                logger.error(f"Error calling TEE service for proposal {proposal_id}: {e}")
                raise
    '''