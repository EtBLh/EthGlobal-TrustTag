import asyncio
import logging

from fastapi import FastAPI
from app.routes import router as api_router
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.services import blockchain_listener
from app.routes import salt_router, vote_router

app = FastAPI(title="Decentralized Labeling Backend")

# Global variable to hold the background task
background_task = None

logger = logging.getLogger("uvicorn.error")

async def cronjob():
    """Background task that runs every 3 seconds."""
    while True:
        try:
            # Process blockchain votes (listen for events, call TEE, update smart contract, update DB)
            await blockchain_listener.process_votes()
        except Exception as e:
            logger.error(f"Error in cronjob: {e}")
        await asyncio.sleep(3)

@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB
    await connect_to_mongo()
    # Start the background cronjob
    global background_task
    background_task = asyncio.create_task(cronjob())
    logger.info("Startup event complete, cronjob started.")

@app.on_event("shutdown")
async def shutdown_event():
    # Cancel the background task
    global background_task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("Background task cancelled.")
    # Close MongoDB connection
    await close_mongo_connection()
    logger.info("Shutdown event complete.")
    
app.include_router(salt_router)
app.include_router(vote_router)