"""Plan and usage endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import settings
from app.services import firebase_service, plan_service
from app.services.supabase_service import is_connectivity_error

router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_current_user(authorization: str = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    try:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        decoded = firebase_service.verify_id_token(parts[1])
        user_id = decoded.get("uid")
        if not user_id:
            raise ValueError("Invalid token: missing uid")
        return user_id
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/plans")
async def get_public_plans() -> dict:
    return {"plans": plan_service.public_plans()}


@router.get("/plan")
async def get_account_plan(user_id: str = Depends(get_current_user)) -> dict:
    try:
        return await plan_service.account_summary(user_id)
    except Exception as e:
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise


@router.post("/demo-upgrade")
async def demo_upgrade_to_autopilot(user_id: str = Depends(get_current_user)) -> dict:
    """Temporary checkout endpoint: marks the user as Autopilot without charging money."""
    if not settings.DEMO_BILLING_ENABLED:
        raise HTTPException(status_code=403, detail="Demo billing is disabled for this deployment.")
    try:
        return await plan_service.activate_demo_autopilot(user_id)
    except Exception as e:
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Could not activate Autopilot")
