"""
WhatsApp integration routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.responses import Response
from app.models import WhatsappWebhookRequest
from app.services import chat_workflow_service, supabase_service, firebase_service, plan_service
from app.services.call_reminder_service import normalize_phone_number
from app.services.runtime_config_service import runtime_config_service
from app.services.redis_memory_service import redis_memory_service
from app.services.supabase_service import is_connectivity_error
from app.core.config import settings
import asyncio
import base64
import hashlib
import hmac
import html
import logging
import re
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


def _parse_iso_datetime(value: str | None) -> datetime | None:
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
    """Extract user ID from Firebase token in Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract bearer token
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format")
        token = parts[1]
        
        # Verify with Firebase and extract user ID
        decoded = firebase_service.verify_id_token(token)
        user_id = decoded.get("uid")
        if not user_id:
            raise ValueError("Invalid token: missing uid")
        return user_id
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def _strip_whatsapp_prefix(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("whatsapp:", "").strip()


def _twiml_message(message: str) -> Response:
    safe = html.escape((message or "").strip()[:1500] or "AgentCoolie could not generate a reply.")
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


def _twiml_empty() -> Response:
    """Acknowledge a duplicate provider retry without sending another message."""
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response/>', media_type="application/xml")


def _validate_twilio_signature(url: str, form_data: dict[str, str], signature: str | None, auth_token: str | None) -> bool:
    # Twilio signs the public request URL plus sorted form parameters.
    if not auth_token or not signature:
        return False
    payload = url + "".join(f"{key}{form_data[key]}" for key in sorted(form_data))
    digest = hmac.new(
        auth_token.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)


@router.post("/twilio-webhook")
async def handle_twilio_whatsapp_webhook(request: Request) -> Response:
    """Receive WhatsApp Sandbox/Business messages from Twilio and reply as AgentCoolie."""
    form = await request.form()
    form_data = {str(key): str(value) for key, value in form.items()}

    if settings.TWILIO_VALIDATE_WEBHOOK_SIGNATURE:
        signature = request.headers.get("x-twilio-signature")
        url = str(request.url)
        auth_token = await runtime_config_service.get_secret("TWILIO_AUTH_TOKEN")
        if not _validate_twilio_signature(url, form_data, signature, auth_token):
            logger.warning("Rejected Twilio WhatsApp webhook with invalid signature")
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    from_number = normalize_phone_number(_strip_whatsapp_prefix(form_data.get("From")))
    message = (form_data.get("Body") or "").strip()
    profile_name = (form_data.get("ProfileName") or "").strip() or None

    if not from_number:
        return _twiml_message("I could not read your WhatsApp phone number.")
    if not message:
        return _twiml_message("Send a text message and I will help from WhatsApp.")

    message_sid = str(form_data.get("MessageSid") or "").strip()
    if not message_sid:
        logger.warning("Rejected Twilio WhatsApp webhook without MessageSid")
        raise HTTPException(status_code=400, detail="Missing Twilio MessageSid")
    idempotency_id = f"twilio-whatsapp:{message_sid}"
    reserved = await redis_memory_service.reserve_idempotency_key(
        idempotency_id,
        settings.WEBHOOK_IDEMPOTENCY_TTL_SECONDS,
    )
    if reserved is None:
        logger.error("Cannot safely process Twilio WhatsApp webhook because Redis is unavailable")
        raise HTTPException(status_code=503, detail="Webhook idempotency storage is unavailable")
    if not reserved:
        logger.info("Ignoring duplicate Twilio WhatsApp webhook %s", message_sid)
        return _twiml_empty()

    try:
        credential = await supabase_service.find_credential_by_phone(from_number, "whatsapp")
        if not credential:
            return _twiml_message(
                "This WhatsApp number is not linked to AgentCoolie yet. "
                "Open AgentCoolie Settings and save this same number under WhatsApp Access first."
            )

        user_id = str(credential.get("user_id") or "")
        credential_data = credential.get("data") if isinstance(credential.get("data"), dict) else {}
        if not credential_data.get("verified"):
            expected_code = str(credential_data.get("verification_code") or "").strip()
            expires_at = _parse_iso_datetime(credential_data.get("verification_expires_at"))
            if expires_at and datetime.now(timezone.utc) > expires_at:
                return _twiml_message(
                    "This WhatsApp verification code expired. Open AgentCoolie Settings and request a new code."
                )
            code_match = re.search(r"\blink\s+(\d{6})\b", message, re.IGNORECASE)
            if expected_code and code_match and code_match.group(1) == expected_code:
                updated_data = {
                    **credential_data,
                    "verified": True,
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }
                updated_data.pop("verification_code", None)
                await supabase_service.save_credentials(user_id, "whatsapp", updated_data)
                return _twiml_message("WhatsApp is now connected to your AgentCoolie account.")

            return _twiml_message(
                "This WhatsApp number is waiting for verification. "
                "Open AgentCoolie Settings, copy the code, and send LINK followed by that code here."
            )

        try:
            await plan_service.check_and_consume(
                user_id,
                "whatsapp_messages",
                metadata={"source": "twilio_inbound"},
            )
        except HTTPException as e:
            return _twiml_message(str(e.detail))

        result = await chat_workflow_service.process(
            user_id=user_id,
            message=message,
            user_name=profile_name,
            save_messages=True,
        )
        return _twiml_message(result.get("response") or "Done.")

    except Exception as e:
        await redis_memory_service.release_idempotency_key(idempotency_id)
        logger.exception(f"Twilio WhatsApp webhook failed for {from_number}: {e}")
        return _twiml_message("Something went wrong in AgentCoolie while handling your WhatsApp message.")


@router.get("/verify")
async def verify_webhook(token: str, challenge: str) -> dict:
    """
    Verify WhatsApp webhook (Twilio/Vonage verification).

    Args:
        token: Verification token
        challenge: Challenge string

    Returns:
        Challenge response
    """
    if not settings.WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=503, detail="WhatsApp verify token not configured")
    if token != settings.WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verification token")
    return {"challenge": challenge}


@router.post("/webhook")
async def handle_webhook(
    request: WhatsappWebhookRequest,
    x_webhook_token: str = Header(None),
) -> dict:
    """
    Handle incoming WhatsApp messages.

    Args:
        request: WhatsApp webhook request

    Returns:
        Success response
    """
    try:
        if settings.is_production():
            raise HTTPException(
                status_code=410,
                detail="The generic WhatsApp webhook is disabled outside local development. Use the signed Twilio webhook endpoint.",
            )
        if not settings.WHATSAPP_WEBHOOK_SECRET:
            raise HTTPException(status_code=503, detail="WhatsApp webhook secret not configured")
        if x_webhook_token != settings.WHATSAPP_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid webhook token")

        if not request.messages:
            return {"status": "success"}

        # Process each message
        for msg in request.messages:
            idempotency_id: str | None = None
            try:
                from_number = normalize_phone_number(_strip_whatsapp_prefix(str(msg.get("from") or "")))
                message_text = msg.get("text", {}).get("body", "")
                if not from_number or not message_text:
                    continue

                provider_message_id = str(
                    msg.get("id") or msg.get("message_id") or msg.get("MessageSid") or ""
                ).strip()
                if not provider_message_id:
                    logger.warning("Ignoring generic WhatsApp event without a provider message id")
                    continue
                idempotency_id = f"generic-whatsapp:{provider_message_id}"
                reserved = await redis_memory_service.reserve_idempotency_key(
                    idempotency_id,
                    settings.WEBHOOK_IDEMPOTENCY_TTL_SECONDS,
                )
                if reserved is None:
                    raise RuntimeError("Webhook idempotency storage is unavailable")
                if not reserved:
                    logger.info("Ignoring duplicate generic WhatsApp webhook %s", provider_message_id)
                    continue

                credential = await supabase_service.find_credential_by_phone(from_number, "whatsapp")
                credential_data = credential.get("data") if credential and isinstance(credential.get("data"), dict) else {}
                if not credential or not credential_data.get("verified"):
                    logger.warning("Ignoring WhatsApp webhook message from unlinked or unverified number")
                    continue

                user_id = str(credential.get("user_id") or "")
                try:
                    await plan_service.check_and_consume(
                        user_id,
                        "whatsapp_messages",
                        metadata={"source": "generic_webhook"},
                    )
                except HTTPException as e:
                    logger.warning(f"WhatsApp usage limit reached for {user_id}: {e.detail}")
                    continue

                result = await chat_workflow_service.process(
                    user_id=user_id,
                    message=message_text,
                    save_messages=False,
                )

                # Save message to database
                await supabase_service.create_message(
                    user_id=user_id,
                    content=message_text,
                    role="user",
                )

                # Create notification for user
                await supabase_service.create_notification(
                    user_id=user_id,
                    title="WhatsApp Message",
                    message=f"New message: {message_text[:50]}...",
                    notification_type="whatsapp",
                )

                logger.info(f"Processed WhatsApp message from {user_id}")

            except Exception as e:
                if idempotency_id:
                    await redis_memory_service.release_idempotency_key(idempotency_id)
                logger.error(f"Failed to process WhatsApp message: {e}")
                continue

        return {"status": "success", "processed": len(request.messages)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/send")
async def send_whatsapp_message(
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Send WhatsApp message to a phone number.

    Args:
        request: {"to": "+1234567890", "message": "text"}
        user_id: Authenticated user ID

    Returns:
        Send status
    """
    try:
        to_number = request.get("to")
        message = request.get("message")

        if not to_number or not message:
            raise HTTPException(status_code=400, detail="Missing 'to' or 'message'")

        sender_credentials = await supabase_service.get_credentials(user_id, "whatsapp")
        sender_data = sender_credentials.get("data") if isinstance(sender_credentials, dict) else {}
        if not isinstance(sender_data, dict) or not sender_data.get("verified"):
            raise HTTPException(status_code=409, detail="Connect and verify WhatsApp in Settings before sending messages.")

        twilio_config = await runtime_config_service.get_secrets(
            ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM"]
        )
        account_sid = twilio_config.get("TWILIO_ACCOUNT_SID")
        auth_token = twilio_config.get("TWILIO_AUTH_TOKEN")
        whatsapp_from = twilio_config.get("TWILIO_WHATSAPP_FROM")
        if not account_sid or not auth_token or not whatsapp_from:
            raise HTTPException(status_code=503, detail="Twilio WhatsApp is not configured")

        normalized_to = normalize_phone_number(_strip_whatsapp_prefix(str(to_number)))
        if not normalized_to:
            raise HTTPException(status_code=400, detail="Invalid WhatsApp phone number")

        await plan_service.check_and_consume(
            user_id,
            "whatsapp_messages",
            metadata={"source": "whatsapp_send", "to": normalized_to},
        )

        def _send() -> requests.Response:
            return requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                data={
                    "To": f"whatsapp:{normalized_to}",
                    "From": whatsapp_from,
                    "Body": str(message)[:1500],
                },
                auth=(account_sid, auth_token),
                timeout=30,
            )

        response = await asyncio.to_thread(_send)
        if response.status_code >= 400:
            raise RuntimeError(f"Twilio WhatsApp send failed ({response.status_code}): {response.text[:300]}")
        twilio_payload = response.json()
        logger.info(f"Sent WhatsApp message to {normalized_to}: {twilio_payload.get('sid')}")

        # Save sent message
        if user_id:
            await supabase_service.create_message(
                user_id=user_id,
                content=message,
                role="assistant",
            )

        return {
            "status": "success",
            "message": "Message sent",
            "to": normalized_to,
            "sid": twilio_payload.get("sid"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail="Could not reach Supabase.")
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")
