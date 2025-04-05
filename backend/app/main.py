import asyncio
import logging

from fastapi import FastAPI
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.jobs.scheduler import start_reveal_phase_job, finalize_reward_job
from app.routes.middleware import WorldIDMiddleware
from app.routes.propose import router as propose_router
from app.routes.vote import router as vote_router
from app.routes.rewards import router as rewards_router

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Decentralized Labeling Backend")
app.add_middleware(WorldIDMiddleware)

# Global background task handle
background_task = None

async def cronjob():
    """Background task that runs every 3 seconds to drive the commit‑reveal‑finalize workflow."""
    while True:
        try:
            # 1) Start reveal phase for proposals whose commit-deadline has passed
            await start_reveal_phase_job()
            # 2) Finalize rewards for proposals whose reveal-deadline has passed
            await finalize_reward_job()
        except Exception as e:
            logger.error(f"Error in cronjob: {e}")
        await asyncio.sleep(3)


@app.on_event("startup")
async def on_startup():
    # Connect to MongoDB
    await connect_to_mongo()
    # Launch background scheduler
    global background_task
    background_task = asyncio.create_task(cronjob())
    logger.info("Startup complete — background scheduler started.")


@app.on_event("shutdown")
async def on_shutdown():
    # Cancel the background scheduler
    global background_task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background scheduler cancelled.")
    # Close MongoDB connection
    await close_mongo_connection()
    logger.info("Shutdown complete — MongoDB connection closed.")


# Include your API routers
app.include_router(propose_router)
app.include_router(vote_router)
app.include_router(rewards_router)