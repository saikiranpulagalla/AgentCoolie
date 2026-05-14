"""Integration status and credential compatibility routes."""

from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.services import call_reminder_service, firebase_service, n8n_service, plan_service, supabase_service
from app.services.call_reminder_service import normalize_phone_number
from app.services.supabase_service import is_connectivity_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["integrations"])


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

        verification_code = f"{secrets.randbelow(900000) + 100000}"
        await supabase_service.save_credentials(
            user_id,
            "whatsapp",
            {
                "phone_number": normalized,
                "provider": "twilio",
                "verified": False,
                "verification_code": verification_code,
            },
        )
        return {
            "status": "success",
            "configured": True,
            "connected": False,
            "verification_required": True,
            "verification_code": verification_code,
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


@router.post("/external/save-gmail-credentials")
async def save_gmail_credentials(
    request: dict[str, Any],
    user_id: str = Depends(get_current_user),
) -> dict[str, str]:
    try:
        credentials = request.get("credentials")
        if credentials is None:
            await supabase_service.delete_credentials(user_id, "gmail")
            return {"status": "success", "message": "Gmail disconnected"}

        if not isinstance(credentials, dict):
            raise HTTPException(status_code=400, detail="credentials must be an object or null")

        await plan_service.ensure_feature_available(user_id, "gmail_sends")
        await supabase_service.save_credentials(user_id, "gmail", credentials)
        return {"status": "success", "message": "Gmail credentials saved"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save Gmail credentials for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to save Gmail credentials")


@router.post("/external/gmail-action")
async def run_gmail_action(
    request: dict[str, Any],
    user_id: str = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        message = str(request.get("message") or request.get("query") or "").strip()
        action = request.get("action")
        payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
        if not message and not action:
            raise HTTPException(status_code=400, detail="message or action is required")

        result = await n8n_service.run_gmail_action(
            user_id=user_id,
            message=message,
            action=str(action) if action else None,
            payload=payload,
        )
        if not result.get("ok"):
            status_code = int(result.get("status") or 502)
            detail = result.get("message") or result.get("body") or "Gmail workflow failed"
            raise HTTPException(status_code=status_code if status_code < 600 else 502, detail=detail)

        return {
            "status": "success",
            "result": result.get("body"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run Gmail action for {user_id}: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to run Gmail action")
