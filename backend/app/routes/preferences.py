"""Personalization preference routes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.services import firebase_service, supabase_service
from app.services.supabase_service import is_connectivity_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/preferences", tags=["preferences"])

DEFAULT_PREFERENCES = {
    "tone": "friendly",
    "response_length": "moderate",
    "formality": "medium",
    "include_emojis": False,
}

ALLOWED_TONES = {"professional", "casual", "friendly", "formal"}
ALLOWED_LENGTHS = {"brief", "moderate", "detailed"}
ALLOWED_FORMALITY = {"low", "medium", "high"}


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


def _normalize_formality(value: Any) -> str:
    if isinstance(value, int):
        if value <= 3:
            return "low"
        if value >= 8:
            return "high"
        return "medium"

    formality = str(value or DEFAULT_PREFERENCES["formality"]).strip().lower()
    return formality if formality in ALLOWED_FORMALITY else DEFAULT_PREFERENCES["formality"]


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def _normalize_preferences(payload: dict[str, Any]) -> dict[str, Any]:
    tone = str(payload.get("tone") or DEFAULT_PREFERENCES["tone"]).strip().lower()
    response_length = str(
        payload.get("response_length")
        or payload.get("responseLength")
        or DEFAULT_PREFERENCES["response_length"]
    ).strip().lower()

    return {
        "tone": tone if tone in ALLOWED_TONES else DEFAULT_PREFERENCES["tone"],
        "response_length": response_length if response_length in ALLOWED_LENGTHS else DEFAULT_PREFERENCES["response_length"],
        "formality": _normalize_formality(payload.get("formality")),
        "include_emojis": _normalize_bool(payload.get("include_emojis", payload.get("includeEmojis", False))),
    }


def _with_defaults(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return dict(DEFAULT_PREFERENCES)
    return {**DEFAULT_PREFERENCES, **{key: row.get(key) for key in DEFAULT_PREFERENCES if row.get(key) is not None}}


@router.get("/{target_user_id}")
async def get_preferences(
    target_user_id: str,
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    if target_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot read another user's preferences")

    try:
        return _with_defaults(await supabase_service.get_preferences(user_id))
    except Exception as e:
        logger.error(f"Failed to fetch preferences for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")


@router.put("/{target_user_id}")
async def update_preferences(
    target_user_id: str,
    request: dict[str, Any],
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    if target_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update another user's preferences")

    preferences = _normalize_preferences(request)
    try:
        saved = await supabase_service.upsert_preferences(user_id, preferences)
        return _with_defaults(saved)
    except Exception as e:
        logger.error(f"Failed to save preferences for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to save preferences")
