"""
Notifications routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from app.services import supabase_service, firebase_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_current_user(authorization: str = Header(None)) -> str:
    """Extract user ID from Firebase token in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        token = parts[1]
        
        decoded = firebase_service.verify_id_token(token)
        return decoded.get("uid")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("")
async def get_notifications(
    user_id: str = Depends(get_current_user),
    unread_only: bool = False,
) -> list[dict]:
    """
    Get notifications for current user.
    """
    try:
        notifications = await supabase_service.get_notifications(user_id, unread_only)
        return notifications
    except Exception as e:
        logger.error(f"Failed to fetch notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))
