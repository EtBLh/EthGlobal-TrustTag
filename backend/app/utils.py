import logging
import os
import aiohttp
from typing import Dict, Any

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Utility to get a configured logger.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        # Set a default handler if no handlers exist
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

async def verify_world_id(is_success_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the World ID API to verify the provided proof data.
    
    Args:
        is_success_result: Dictionary containing verification data
        
    Returns:
        dict: The API response
    """
    logger = get_logger(__name__)
    
    # Extract required fields from the input
    nullifier_hash = is_success_result.get("nullifier_hash")
    merkle_root = is_success_result.get("merkle_root")
    proof = is_success_result.get("proof")
    verification_level = is_success_result.get("verification_level")
    app_id = os.getenv("WORLD_ID_APP_ID")
    action = os.getenv("WORLD_ID_ACTION")
    
    # Construct the endpoint URL
    url = f"https://developer.worldcoin.org/api/v2/verify/{app_id}"
    
    # Prepare the request payload
    payload = {
        "nullifier_hash": nullifier_hash,
        "merkle_root": merkle_root,
        "proof": proof,
        "verification_level": verification_level,
        "action": action
    }
    
    # Set the headers
    headers = {"Content-Type": "application/json"}
    
    logger.info(f"Calling World ID verification API for action: {action}")
    
    try:
        # Use aiohttp for async HTTP requests
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse the JSON response
                result = await response.json()
                logger.info("World ID API call completed successfully")
                return result
                
    except aiohttp.ClientError as e:
        logger.error(f"World ID API call failed: {str(e)}")
        raise Exception(f"World ID verification failed: {str(e)}")
    
def get_salt() -> str:
    """
    Generate a random salt value.
    
    Returns:
        str: A random salt value
    """
    return os.urandom(16).hex()