import asyncio
from datetime import datetime
from app.services.tee_client import TeeClient
from app.db.mongodb import connect_to_mongo

async def main():
    # Setup
    await connect_to_mongo()

    # Define your test input
    proposal_id = "test_proposal_tee"
    voters = [
        "0x1111111111111111111111111111111111111111",
        "0x2222222222222222222222222222222222222222",
        "0x3333333333333333333333333333333333333333"
    ]

    print("Calling compute_rewards...")
    rewards = await TeeClient.compute_rewards(proposal_id, voters)

    print("\n✅ BTS Reward Output:")
    for r in rewards:
        print(f"- {r['address']}: {r['score']:.4f}")

if __name__ == "__main__":
    asyncio.run(main())