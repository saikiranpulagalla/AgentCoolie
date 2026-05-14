"""
Website opening routes for handling user requests to open websites.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["website"])


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
async def open_website(request: WebsiteRequest) -> dict:
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
        import re
        url_pattern = r'https?://[^\s\)"\']+'
        urls = re.findall(url_pattern, query)
        
        if urls:
            # Found a full URL
            final_url = urls[0]
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
        
    except Exception as e:
        logger.error(f"Website opening error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process website request"
        )
