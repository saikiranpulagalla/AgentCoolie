"""
Website opening routes for handling user requests to open websites.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from urllib.parse import urlparse
import ipaddress
import logging
import re

from app.services import firebase_service, plan_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["website"])

BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}


def _is_safe_public_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.strip().strip(".").lower()
    if not host or host in BLOCKED_HOSTS or host.endswith(".localhost"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)
    except ValueError:
        return bool(re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}", host))


def _safe_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        if not (
            settings.is_local_runtime()
            and parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        ):
            return None
    if not _is_safe_public_host(parsed.hostname):
        if not (settings.is_local_runtime() and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
            return None
    return parsed.geturl()


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


class WebsiteRequest(BaseModel):
    """Request to open a website."""
    query: str


class WebsiteResponse(BaseModel):
    """Response from website opening request."""
    status: str
    final_url: Optional[str] = None
    opened: bool = False
    opened_in_system_browser: bool = False


@router.post("/website/open", response_model=WebsiteResponse)
async def open_website(
    request: WebsiteRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Handle website opening requests.
    
    This endpoint receives a query (typically a URL or website name) and
    attempts to extract and return the website URL. The frontend will
    then open it using window.open().
    
    Args:
        request: Website opening request with query
        
    Returns:
        Response with website URL if found
    """
    try:
        query = request.query.strip()
        
        if not query:
            return {
                "status": "error",
                "opened": False,
                "opened_in_system_browser": False
            }

        # Simple URL extraction - look for URLs in the query
        url_pattern = r'https?://[^\s\)"\']+'
        urls = re.findall(url_pattern, query)
        
        if urls:
            # Found a full URL
            final_url = _safe_url(urls[0])
            if not final_url:
                raise HTTPException(status_code=400, detail="That URL is not allowed.")
            await plan_service.check_and_consume(
                user_id,
                "website_opens",
                metadata={"source": "website_api", "mode": "url"},
            )
            logger.info(f"Website endpoint: Found URL in query: {final_url}")
            return {
                "status": "success",
                "final_url": final_url,
                "opened": False,
                "opened_in_system_browser": False
            }
        
        # Check for domain-like patterns (www.example.com or example.com)
        # This is best-effort extraction, frontend can further handle
        domain_pattern = r'(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        domains = re.findall(domain_pattern, query)
        
        if domains:
            domain = domains[0]
            # Add https:// if not present
            if not domain.startswith('www.'):
                domain = f"www.{domain}"
            final_url = f"https://{domain}"
            if not _safe_url(final_url):
                raise HTTPException(status_code=400, detail="That website is not allowed.")
            await plan_service.check_and_consume(
                user_id,
                "website_opens",
                metadata={"source": "website_api", "mode": "domain"},
            )
            logger.info(f"Website endpoint: Detected domain: {final_url}")
            return {
                "status": "success",
                "final_url": final_url,
                "opened": False,
                "opened_in_system_browser": False
            }

        # Handle common "open <site>" requests without a dot, e.g. "open amazon".
        stop_words = {
            "open", "go", "to", "visit", "show", "me", "navigate", "launch",
            "website", "site", "link", "the", "a", "an", "can", "you", "u",
            "please", "in", "browser",
        }
        tokens = re.findall(r"[a-zA-Z0-9-]+", query.lower())
        candidates = [token for token in tokens if token not in stop_words]
        if candidates:
            site = candidates[-1]
            final_url = f"https://www.{site}.com"
            if not _safe_url(final_url):
                raise HTTPException(status_code=400, detail="That website is not allowed.")
            await plan_service.check_and_consume(
                user_id,
                "website_opens",
                metadata={"source": "website_api", "mode": "inferred"},
            )
            logger.info(f"Website endpoint: Inferred site name: {final_url}")
            return {
                "status": "success",
                "final_url": final_url,
                "opened": False,
                "opened_in_system_browser": False
            }
        
        # No URL found
        logger.debug(f"Website endpoint: No URL found in query: {query}")
        return {
            "status": "success",
            "opened": False,
            "opened_in_system_browser": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Website opening error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process website request"
        )
