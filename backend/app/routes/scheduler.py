from fastapi import APIRouter, HTTPException
from app.jobs.scheduler import start_reveal_phase_job, finalize_reward_job

router = APIRouter(prefix="/api/test", tags=["scheduler"])

@router.post("/start_reveal")
async def trigger_start_reveal():
    """
    Endpoint to trigger the start_reveal_phase_job.
    """
    try:
        await start_reveal_phase_job()
        return {"message": "start_reveal_phase_job executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@router.post("/finalize_reward")
async def trigger_finalize_reward():
    """
    Endpoint to trigger the finalize_reward_job.
    """
    try:
        await finalize_reward_job()
        return {"message": "finalize_reward_job executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")