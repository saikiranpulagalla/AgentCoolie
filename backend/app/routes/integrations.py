"""Integration status and credential compatibility routes."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import settings
from app.services import call_reminder_service, firebase_service, plan_service, supabase_service
from app.services.call_reminder_service import normalize_phone_number
from app.services.supabase_service import is_connectivity_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["integrations"])


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


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


@router.get("/integrations/status")
async def get_integrations_status(user_id: str = Depends(get_current_user)) -> dict[str, bool]:
    try:
        gmail = await supabase_service.get_credentials(user_id, "gmail")
        whatsapp = await supabase_service.get_credentials(user_id, "whatsapp")
        call_reminder = await supabase_service.get_credentials(user_id, "call_reminder")
        return {"gmail": bool(gmail), "whatsapp": bool(whatsapp), "call_reminder": bool(call_reminder)}
    except Exception as e:
        logger.error(f"Failed to fetch integration status for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to fetch integration status")


@router.delete("/integrations/gmail")
async def disconnect_gmail(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    """Remove the authenticated user's stored Gmail OAuth credentials."""
    try:
        deleted = await supabase_service.delete_credentials(user_id, "gmail")
        return {"status": "success", "connected": False, "deleted": bool(deleted)}
    except Exception as e:
        logger.error(f"Failed to disconnect Gmail for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to disconnect Gmail")


@router.get("/integrations/call-reminder")
async def get_call_reminder_status(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    try:
        phone_number = await call_reminder_service.get_user_phone(user_id)
        return {
            "configured": await call_reminder_service.is_configured(),
            "connected": bool(phone_number),
            "phone_number": phone_number,
        }
    except Exception as e:
        logger.error(f"Failed to fetch call reminder status for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to fetch call reminder status")


@router.post("/integrations/call-reminder")
async def save_call_reminder_phone(
    request: dict[str, Any],
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        phone_number = request.get("phone_number")
        if phone_number is None or str(phone_number).strip() == "":
            await call_reminder_service.delete_user_phone(user_id)
            return {"status": "success", "connected": False}

        await call_reminder_service.save_user_phone(user_id, str(phone_number))
        saved_phone = await call_reminder_service.get_user_phone(user_id)
        return {
            "status": "success",
            "configured": await call_reminder_service.is_configured(),
            "connected": bool(saved_phone),
            "phone_number": saved_phone,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save call reminder phone for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to save call reminder phone")


@router.get("/integrations/whatsapp")
async def get_whatsapp_status(user_id: str = Depends(get_current_user)) -> dict[str, Any]:
    try:
        credentials = await supabase_service.get_credentials(user_id, "whatsapp")
        data = credentials.get("data") if isinstance(credentials, dict) else {}
        if not isinstance(data, dict):
            data = {}
        verified = bool(data.get("verified"))
        return {
            "configured": True,
            "connected": bool(data.get("phone_number")) and verified,
            "verification_required": bool(data.get("phone_number")) and not verified,
            "verification_code": data.get("verification_code") if not verified else None,
            "phone_number": data.get("phone_number"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch WhatsApp status for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to fetch WhatsApp status")


@router.post("/integrations/whatsapp")
async def save_whatsapp_phone(
    request: dict[str, Any],
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        phone_number = request.get("phone_number")
        if phone_number is None or str(phone_number).strip() == "":
            await supabase_service.delete_credentials(user_id, "whatsapp")
            return {"status": "success", "connected": False}

        normalized = normalize_phone_number(str(phone_number))
        if not normalized:
            raise HTTPException(status_code=400, detail="WhatsApp phone must be in E.164 format, e.g. +919000000000")

        await plan_service.ensure_feature_available(user_id, "whatsapp_messages")
        existing = await supabase_service.find_credential_by_phone(normalized, "whatsapp")
        if existing and existing.get("user_id") != user_id:
            raise HTTPException(status_code=409, detail="This WhatsApp number is already linked to another AgentCoolie account")
        existing_data = existing.get("data") if isinstance(existing, dict) else {}
        if isinstance(existing_data, dict) and existing_data.get("verified"):
            return {
                "status": "success",
                "configured": True,
                "connected": True,
                "phone_number": normalized,
            }

        now = datetime.now(timezone.utc)
        if isinstance(existing_data, dict) and existing_data.get("phone_number") == normalized:
            sent_at = _parse_iso_datetime(existing_data.get("verification_sent_at"))
            resend_seconds = max(15, int(settings.WHATSAPP_VERIFICATION_RESEND_SECONDS or 60))
            if sent_at and (now - sent_at).total_seconds() < resend_seconds:
                return {
                    "status": "success",
                    "configured": True,
                    "connected": False,
                    "verification_required": True,
                    "verification_code": existing_data.get("verification_code"),
                    "verification_expires_at": existing_data.get("verification_expires_at"),
                    "phone_number": normalized,
                    "message": "A verification code was already generated recently. Send LINK followed by that code from WhatsApp.",
                }

        verification_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = now + timedelta(minutes=max(1, int(settings.WHATSAPP_VERIFICATION_TTL_MINUTES or 15)))
        await supabase_service.save_credentials(
            user_id,
            "whatsapp",
            {
                "phone_number": normalized,
                "provider": "twilio",
                "verified": False,
                "verification_code": verification_code,
                "verification_sent_at": now.isoformat(),
                "verification_expires_at": expires_at.isoformat(),
            },
        )
        return {
            "status": "success",
            "configured": True,
            "connected": False,
            "verification_required": True,
            "verification_code": verification_code,
            "verification_expires_at": expires_at.isoformat(),
            "phone_number": normalized,
            "message": f"Send LINK {verification_code} from this WhatsApp number to finish linking.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save WhatsApp phone for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to save WhatsApp phone")
