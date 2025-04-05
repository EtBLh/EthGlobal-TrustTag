import aiohttp
import logging
from app.config import TEE_SERVICE_URL

logger = logging.getLogger(__name__)

async def call_tee(vote):
    """
    Call the TEE service with a given vote and return the TEE output.
    For demonstration, this function simulates a TEE response.
    """
    async with aiohttp.ClientSession() as session:
        try:
            # In a real implementation, you'd send the vote data to the TEE service:
            # async with session.post(TEE_SERVICE_URL, json=vote.dict()) as response:
            #     response_data = await response.json()
            # Simulating a TEE response:
            response_data = {
                "voteId": vote.voteId,
                "target_address": vote.target_address,
                "proove": vote.proove,
                "expire": vote.expire,
                "max_vote_limit": vote.max_vote_limit,
                "result": {"yes": 7, "no": 3},
                "rewards": [
                    {"address": "0xRewardAddress1", "amount": 10.0},
                    {"address": "0xRewardAddress2", "amount": 5.0},
                ]
            }
            logger.info(f"TEE service simulated response for vote {vote.voteId}")
            return TEEOutput(**response_data)
        except Exception as e:
            logger.error(f"Error calling TEE service: {e}")
            raise