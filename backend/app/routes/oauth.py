"""Google OAuth routes for Gmail integration."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.services import firebase_service, plan_service, supabase_service
from app.services.runtime_config_service import runtime_config_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/oauth", tags=["oauth"])

GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _frontend_url() -> str:
    if settings.FRONTEND_URL:
        return settings.FRONTEND_URL.rstrip("/")

    if settings.ENV != "development":
        for origin in settings.CORS_ORIGINS:
            normalized = origin.rstrip("/")
            if normalized.startswith("https://") and "localhost" not in normalized and "127.0.0.1" not in normalized:
                return normalized

    for origin in settings.CORS_ORIGINS:
        if "localhost:5173" in origin or "127.0.0.1:5173" in origin:
            return origin.rstrip("/")
    return (settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:5173").rstrip("/")


async def _redirect_uri() -> str:
    return (
        await runtime_config_service.get_secret("GOOGLE_OAUTH_REDIRECT_URI")
        or f"http://localhost:{settings.PORT}/api/oauth/google/callback"
    )


async def _client_config() -> dict:
    client_id = await runtime_config_service.get_secret("GOOGLE_CLIENT_ID")
    client_secret = await runtime_config_service.get_secret("GOOGLE_CLIENT_SECRET")
    redirect_uri = await _redirect_uri()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Gmail OAuth is not configured. Add GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, "
                f"and GOOGLE_OAUTH_REDIRECT_URI={redirect_uri} to app_secrets or .env, then add the same "
                "redirect URI in Google Cloud OAuth settings."
            ),
        )

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }


def _state_signature(payload: str) -> str:
    secret = settings.SESSION_SECRET_KEY
    if settings.ENV != "development" and (
        not secret or secret == "your-secret-key-change-in-production"
    ):
        raise HTTPException(
            status_code=503,
            detail="SESSION_SECRET_KEY must be set to a strong production secret before starting OAuth.",
        )
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _make_state(user_id: str) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"uid": user_id, "ts": datetime.now(timezone.utc).isoformat()}).encode("utf-8")
    ).decode("ascii")
    return f"{payload}.{_state_signature(payload)}"


def _read_state(state: str) -> str:
    try:
        payload, signature = state.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    if not hmac.compare_digest(signature, _state_signature(payload)):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from e

    user_id = str(data.get("uid") or "").strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        issued_at = datetime.fromisoformat(str(data.get("ts") or ""))
        if issued_at.tzinfo is None:
            issued_at = issued_at.replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from e

    max_age = max(60, int(settings.OAUTH_STATE_MAX_AGE_SECONDS or 600))
    age_seconds = (datetime.now(timezone.utc) - issued_at.astimezone(timezone.utc)).total_seconds()
    if age_seconds < -60 or age_seconds > max_age:
        raise HTTPException(status_code=400, detail="OAuth state expired")
    return user_id


def _user_from_auth_or_dev_uid(authorization: Optional[str], uid: Optional[str]) -> str:
    if authorization:
        try:
            parts = authorization.split(" ")
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise ValueError("Invalid authorization header format")
            decoded = firebase_service.verify_id_token(parts[1])
            user_id = decoded.get("uid")
            if user_id:
                return user_id
        except ValueError as e:
            logger.warning(f"OAuth start auth failed: {e}")

    if settings.ENV == "development" and uid:
        return uid

    raise HTTPException(status_code=401, detail="Missing or invalid authorization")


@router.get("/google/start")
async def start_google_oauth(
    authorization: Optional[str] = Header(None),
    uid: Optional[str] = Query(default=None),
) -> dict[str, str]:
    user_id = _user_from_auth_or_dev_uid(authorization, uid)
    await plan_service.ensure_feature_available(user_id, "gmail_sends")

    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as e:
        raise HTTPException(status_code=500, detail="google-auth-oauthlib is not installed") from e

    flow = Flow.from_client_config(
        await _client_config(),
        scopes=GMAIL_SCOPES,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = await _redirect_uri()
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=_make_state(user_id),
    )
    return {"url": url}


@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
) -> RedirectResponse:
    frontend_settings_url = f"{_frontend_url()}/settings"
    if error:
        return RedirectResponse(f"{frontend_settings_url}?connected=gmail&error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(f"{frontend_settings_url}?connected=gmail&error=missing_code", status_code=302)

    try:
        from google_auth_oauthlib.flow import Flow

        user_id = _read_state(state)
        await plan_service.ensure_feature_available(user_id, "gmail_sends")
        flow = Flow.from_client_config(
            await _client_config(),
            scopes=GMAIL_SCOPES,
            autogenerate_code_verifier=False,
        )
        flow.redirect_uri = await _redirect_uri()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        credential_data = json.loads(credentials.to_json())
        credential_data["connected_at"] = datetime.now(timezone.utc).isoformat()

        saved = await supabase_service.save_credentials(user_id, "gmail", credential_data)
        logger.info(
            "Saved Gmail OAuth credentials for user %s (row=%s, refresh_token=%s)",
            user_id,
            bool(saved),
            bool(credential_data.get("refresh_token")),
        )
        try:
            await supabase_service.create_notification(
                user_id=user_id,
                title="Gmail connected",
                message="AgentCoolie can now use your Gmail permission for approved automations.",
                notification_type="gmail",
            )
        except Exception as e:
            logger.warning(f"Gmail connected, but notification write failed for {user_id}: {e}")
        return RedirectResponse(f"{frontend_settings_url}?connected=gmail", status_code=302)
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}", exc_info=True)
        return RedirectResponse(f"{frontend_settings_url}?connected=gmail&error=callback_failed", status_code=302)
