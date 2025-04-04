from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Vote(BaseModel):
    voteId: str
    target_address: str
    proove: str
    expire: int
    max_vote_limit: int

class Reward(BaseModel):
    address: str
    amount: float

class TEEOutput(BaseModel):
    voteId: str
    target_address: str
    proove: str
    expire: int
    max_vote_limit: int
    result: Dict[str, int]  # Example: {"yes": 0, "no": 0}
    rewards: List[Reward]