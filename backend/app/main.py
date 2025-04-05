import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.routes.middleware import WorldIDMiddleware
from app.routes.propose import router as propose_router
from app.routes.vote import router as vote_router
from app.routes.rewards import router as rewards_router
from app.routes.scheduler import router as scheduler_router
from app.routes.world import router as world_router

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="TrusTag Backend")

# Setup CORS to accept any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(WorldIDMiddleware)

# Global background task handle
background_task = None

async def cronjob():
    from app.jobs.scheduler import start_reveal_phase_job, finalize_reward_job
    while True:
        try:
            await start_reveal_phase_job()
            await finalize_reward_job()
        except Exception as e:
            logger.error(f"Error in cronjob: {e}")
        await asyncio.sleep(3)

@app.on_event("startup")
async def on_startup():
    await connect_to_mongo()
    global background_task
    # background_task = asyncio.create_task(cronjob())
    logger.info("Startup complete — background scheduler started.")

@app.on_event("shutdown")
async def on_shutdown():
    global background_task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background scheduler cancelled.")
    await close_mongo_connection()
    logger.info("Shutdown complete — MongoDB connection closed.")

# Include your API routers
app.include_router(propose_router)
app.include_router(vote_router)
app.include_router(rewards_router)
app.include_router(scheduler_router)
app.include_router(world_router)