"""
YouTube video detection and opening routes.
Also serves as webhook proxy for chat messages.
"""

from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from app.services import gemini_service
from app.agents import ChatAgent
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["youtube", "webhook"])


class YouTubeRequest(BaseModel):
    """Request to detect and open YouTube videos."""
    query: str


class YouTubeResponse(BaseModel):
    """Response from YouTube detection."""
    status: str
    isVideoRequest: bool = False
    confidence: float = 0.0
    video: Optional[dict] = None


class ChatWebhookRequest(BaseModel):
    """Chat webhook request format."""
    message: str
    userId: Optional[str] = None
    userName: Optional[str] = None
    investigateMode: Optional[bool] = False
    investigateType: Optional[str] = None


@router.post("/youtube/open", response_model=YouTubeResponse)
async def detect_youtube_video(request: YouTubeRequest) -> dict:
    """
    Detect if user is asking to open a YouTube video and return video info.
    
    This endpoint uses AI (Gemini) to determine if the user is asking for
    a video and if so, searches for and returns video information.
    
    Args:
        request: YouTube detection request
        
    Returns:
        Response with video detection result and video info if found
    """
    try:
        query = request.query.strip()
        
        if not query:
            return {
                "status": "error",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }
        
        # Use Gemini to analyze if this is a video request
        # This is optional - if Gemini is not available, we return false
        if not gemini_service:
            logger.debug("Gemini service not available, skipping video detection")
            return {
                "status": "success",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }
        
        analysis = await gemini_service.analyze_text(
            text=query,
            task="detect_video_request"
        )
        
        # Try to parse the response
        try:
            result = json.loads(analysis) if isinstance(analysis, str) else analysis
            is_video_request = result.get("isVideoRequest", False)
            confidence = result.get("confidence", 0.0)
            video_info = result.get("video", None)
            
            logger.debug(f"Video detection result: isVideoRequest={is_video_request}, confidence={confidence}")
            
            return {
                "status": "success",
                "isVideoRequest": is_video_request,
                "confidence": confidence,
                "video": video_info
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Failed to parse Gemini response: {e}")
            return {
                "status": "success",
                "isVideoRequest": False,
                "confidence": 0.0,
                "video": None
            }
        
    except Exception as e:
        logger.error(f"YouTube detection error: {e}")
        # Return graceful failure instead of 500 - video detection is optional
        return {
            "status": "success",
            "isVideoRequest": False,
            "confidence": 0.0,
            "video": None
        }


@router.post("/webhook/proxy")
async def webhook_proxy(request: Request) -> dict:
    """
    Proxy endpoint for chat messages from frontend.
    Accepts both JSON and FormData (multipart) requests.
    
    This endpoint forwards messages to the ChatAgent for processing.
    Automatically detects request format and parses accordingly.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ChatAgent response
    """
    try:
        # Detect content type
        content_type = request.headers.get("content-type", "")
        
        if "application/json" in content_type:
            # JSON request
            data = await request.json()
            message = data.get("message")
            user_id = data.get("userId", "anonymous")
            user_name = data.get("userName", "Anonymous")
        else:
            # FormData request
            form_data = await request.form()
            message = form_data.get("message")
            user_id = form_data.get("userId", "anonymous")
            user_name = form_data.get("userName", "Anonymous")
            files = form_data.getlist("files") if "files" in form_data else []
        
        # Validate message
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        logger.debug(f"Webhook proxy received message: {str(message)[:50]}...")
        
        # Initialize chat agent with user ID
        chat_agent = ChatAgent(user_id=user_id)
        
        # Process message through agent
        response = await chat_agent.chat(message)
        
        return {
            "status": "success",
            "response": response,
            "userId": user_id,
            "userName": user_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook proxy error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.post("/webhook/proxy/json", response_model=dict)
async def webhook_proxy_json(request: ChatWebhookRequest) -> dict:
    """
    JSON version of webhook proxy for simpler requests without files.
    
    Args:
        request: Chat webhook request
        
    Returns:
        ChatAgent response
    """
    try:
        if not request.message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required"
            )
        
        logger.debug(f"Webhook JSON received message: {request.message[:50]}...")
        
        # Initialize chat agent with user ID
        user_id = request.userId or "anonymous"
        chat_agent = ChatAgent(user_id=user_id)
        
        # Process message through agent
        response = await chat_agent.chat(request.message)
        
        return {
            "status": "success",
            "response": response,
            "userId": request.userId,
            "userName": request.userName
        }
        
    except Exception as e:
        logger.error(f"Webhook JSON proxy error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )
