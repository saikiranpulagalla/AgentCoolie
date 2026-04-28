"""
Authentication routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.models import TokenResponse, FirebaseUser
from app.services import firebase_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Extract and verify Firebase token from Authorization header.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Decoded token with user info

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract bearer token
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        token = parts[1]
        
        # Verify with Firebase
        decoded = firebase_service.verify_id_token(token)
        return decoded
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/verify", response_model=FirebaseUser)
async def verify_token(decoded: dict = Depends(get_current_user)) -> dict:
    """
    Verify Firebase ID token from Authorization header.

    Returns:
        User information if token is valid
    """
    user_data = firebase_service.get_user(decoded["uid"])
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    return user_data


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str) -> TokenResponse:
    """
    Refresh Firebase token.
    Note: Firebase client SDK handles token refresh on the frontend.
    This endpoint is for reference/custom implementations.

    Args:
        refresh_token: Firebase refresh token

    Returns:
        New access token
    """
    # Firebase token refresh is typically handled client-side
    # This is a placeholder for custom implementations
    raise HTTPException(status_code=501, detail="Use Firebase SDK for token refresh")
