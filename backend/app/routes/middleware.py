# backend/app/middleware/middleware.py

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.worldchain import Worldchain

logger = logging.getLogger(__name__)


class WorldIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Enforce middleware only on specific routes
        if request.method == "POST" and request.url.path in ("/api/propose", "/api/vote"):
            try:
                body = await request.json()
            except Exception:
                raise HTTPException(400, "Invalid JSON body")

            payload = body.get("verifyPayload")
            if not payload:
                raise HTTPException(400, "Missing verifyPayload")

            ok = await Worldchain.verify_worldid(payload)
            if not ok:
                logger.warning("WorldID verification failed")
                raise HTTPException(400, "WorldID verification failed")

        return await call_next(request)
