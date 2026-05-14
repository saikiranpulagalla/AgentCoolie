"""Web search routes."""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.services import firebase_service, plan_service, web_search_service

router = APIRouter(prefix="/api/search", tags=["search"])


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


class WebSearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/web")
async def web_search(
    request: WebSearchRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    limit = min(max(request.limit, 1), 10)
    await plan_service.check_and_consume(
        user_id,
        "web_searches",
        metadata={"source": "search_api", "limit": limit},
    )
    results = await web_search_service.search(query, limit=limit)
    return {"status": "success", "query": query, "results": results}
