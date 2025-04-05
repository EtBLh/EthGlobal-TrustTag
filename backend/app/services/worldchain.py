import os
import httpx
import logging
from typing import Dict, Any
from app.config import WORLDCOIN_APP_ID

logger = logging.getLogger(__name__)

class Worldchain:
    BASE_URL = "https://developer.worldcoin.org"
    APP_ID = WORLDCOIN_APP_ID  # must be set in your environment
    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "YourAppName/1.0",
    }

    @staticmethod
    async def verify_worldid(payload: Dict[str, Any]) -> bool:
        """
        Verify a World ID proof via Worldcoin Developer API v2.

        payload must include:
          - nullifier_hash: str
          - proof: str
          - merkle_root: str
          - verification_level: str
          - action: str
          - signal_hash: str (optional)
        """
        if not Worldchain.APP_ID:
            logger.error("WORLDCOIN_APP_ID not set")
            return False

        url = f"{Worldchain.BASE_URL}/api/v2/verify/{Worldchain.APP_ID}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=Worldchain.HEADERS, timeout=10.0)
                if resp.status_code == 200:
                    return True
                logger.warning(f"WorldID verification failed [{resp.status_code}]: {resp.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"WorldID request error: {e}")
            return False