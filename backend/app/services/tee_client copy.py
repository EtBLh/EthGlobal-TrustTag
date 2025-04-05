# backend/app/services/tee_client.py

import aiohttp
import logging
from typing import List, Dict
from app.config import TEE_SERVICE_URL

logger = logging.getLogger(__name__)

class TeeClient:
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