"""
Gmail integration routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from app.agents import GmailAgent
from app.services import supabase_service, firebase_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gmail", tags=["gmail"])


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


@router.post("/webhook")
async def handle_gmail_webhook(request: dict) -> dict:
    """
    Handle Gmail webhook notifications.

    Args:
        request: Gmail push notification

    Returns:
        Success response
    """
    try:
        # Gmail push notifications contain message ID, not full email
        # You need to fetch the full email from Gmail API using credentials
        message_id = request.get("message", {}).get("data")

        if not message_id:
            return {"status": "success"}

        # TODO: Fetch email from Gmail API
        # For now, just acknowledge
        logger.info(f"Received Gmail notification for message {message_id}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/process-email")
async def process_email(
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Process email with AI agent.

    Args:
        request: {"email_id": "...", "subject": "...", "body": "...", "from": "..."}
        user_id: Authenticated user ID

    Returns:
        Processing result
    """
    try:
        email_id = request.get("email_id")
        subject = request.get("subject", "")
        body = request.get("body", "")
        sender = request.get("from", "")

        if not email_id or not subject:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Initialize Gmail agent
        agent = GmailAgent(user_id)

        # Process email
        result = await agent.process_email(email_id, subject, body, sender)

        # Save email analysis to database
        if user_id:
            await supabase_service.create_message(
                user_id=user_id,
                content=f"Email from {sender}: {subject}",
                role="user",
            )

            # Create notification
            await supabase_service.create_notification(
                user_id=user_id,
                title="Email Processed",
                message=f"Email from {sender}: {subject}",
                notification_type="gmail",
            )

        return result

    except Exception as e:
        logger.error(f"Failed to process email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/authorize")
async def authorize_gmail(user_id: str = Depends(get_current_user)) -> dict:
    """
    Generate Gmail OAuth authorization URL.

    Args:
        user_id: User ID

    Returns:
        OAuth authorization URL
    """
    try:
        # TODO: Implement Google OAuth flow
        # Generate authorization URL
        from google_auth_oauthlib.flow import Flow
        from app.core.config import settings

        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )

        flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI

        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )

        return {"auth_url": auth_url, "state": state}

    except Exception as e:
        logger.error(f"Failed to authorize Gmail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oauth/callback")
async def oauth_callback(code: str, state: str, user_id: str = Depends(get_current_user)) -> dict:
    """
    Handle Gmail OAuth callback.

    Args:
        code: Authorization code
        state: State from authorization
        user_id: User ID

    Returns:
        Status
    """
    try:
        # TODO: Exchange code for access token
        # Save credentials to Supabase
        logger.info(f"Gmail OAuth callback for user {user_id}")

        return {"status": "success", "message": "Gmail connected"}

    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
