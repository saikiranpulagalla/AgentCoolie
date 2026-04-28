"""
WhatsApp integration routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.models import WhatsappWebhookRequest
from app.agents import WhatsappAgent
from app.services import supabase_service, firebase_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


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
        return decoded.get("uid")
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


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
    # Implement verification logic based on your WhatsApp provider
    return {"challenge": challenge}


@router.post("/webhook")
async def handle_webhook(request: WhatsappWebhookRequest) -> dict:
    """
    Handle incoming WhatsApp messages.

    Args:
        request: WhatsApp webhook request

    Returns:
        Success response
    """
    try:
        if not request.messages:
            return {"status": "success"}

        # Process each message
        for msg in request.messages:
            try:
                user_id = msg.get("from")  # Phone number as user ID
                message_text = msg.get("text", {}).get("body", "")
                message_type = msg.get("type", "text")

                # Initialize WhatsApp agent
                agent = WhatsappAgent(user_id)

                # Process message
                result = await agent.process_message(message_text, user_id)

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
                logger.error(f"Failed to process WhatsApp message: {e}")
                continue

        return {"status": "success", "processed": len(request.messages)}

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

        # TODO: Implement actual WhatsApp send via Twilio/Vonage
        # For now, just log and save to database
        logger.info(f"Sending WhatsApp message to {to_number}: {message}")

        # Save sent message
        if user_id:
            await supabase_service.create_message(
                user_id=user_id,
                content=message,
                role="assistant",
            )

        return {
            "status": "success",
            "message": "Message queued for sending",
            "to": to_number,
        }

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
