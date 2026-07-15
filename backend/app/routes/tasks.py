"""
Task management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.models import Task, TaskCreate, TaskUpdate
from app.services import supabase_service, firebase_service, plan_service
from app.services.supabase_service import is_connectivity_error
from app.agents import TaskAgent
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


SUPABASE_UNREACHABLE_DETAIL = "Could not reach Supabase. Check internet/DNS and SUPABASE_URL in .env."


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


@router.post("", response_model=Task)
async def create_task(
    task_request: TaskCreate,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Create a new task.

    Args:
        task_request: Task creation request
        user_id: User ID

    Returns:
        Created task
    """
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing uid")
        await plan_service.ensure_active_task_slot(user_id)
        if task_request.type.value == "gmail":
            raise HTTPException(
                status_code=400,
                detail="Create scheduled Gmail sends through the chat confirmation flow so the exact recipient and content are approved.",
            )
        if task_request.type.value == "whatsapp":
            await plan_service.ensure_feature_available(user_id, "whatsapp_messages")
        await plan_service.check_and_consume(
            user_id,
            "task_creations",
            metadata={"source": "tasks_api", "task_type": task_request.type.value},
        )
        task = await supabase_service.create_task(
            user_id=user_id,
            title=task_request.title,
            description=task_request.description,
            task_type=task_request.type.value,
            priority=task_request.priority.value,
            due_date=task_request.due_date.isoformat() if task_request.due_date else None,
        )
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to create task")


@router.post("/from-text")
async def create_task_from_text(
    request: dict,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Create task from natural language text.

    Args:
        request: {"text": "string"}
        user_id: User ID

    Returns:
        Created task details
    """
    try:
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing uid")
        agent = TaskAgent(user_id)
        text = request.get("text", "")

        # Extract task details from text
        task_details = await agent.create_from_text(text)

        # Save task to database
        if task_details.get("status") == "success":
            task_data = task_details.get("task", {})
            await plan_service.ensure_active_task_slot(user_id)
            if task_data.get("type") == "gmail":
                raise HTTPException(
                    status_code=400,
                    detail="Create scheduled Gmail sends through the chat confirmation flow so the exact recipient and content are approved.",
                )
            if task_data.get("type") == "whatsapp":
                await plan_service.ensure_feature_available(user_id, "whatsapp_messages")
            await plan_service.check_and_consume(
                user_id,
                "task_creations",
                metadata={"source": "tasks_from_text", "task_type": task_data.get("type", "general")},
            )
            saved_task = await supabase_service.create_task(
                user_id=user_id,
                title=task_data.get("title", "Untitled"),
                description=task_data.get("description"),
                task_type=task_data.get("type", "general"),
                priority=task_data.get("priority", "medium"),
                due_date=task_data.get("due_date"),
            )
            return saved_task

        return {"status": "error", "error": "Failed to extract task details"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task from text: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to create task from text")


@router.get("", response_model=list[Task])
async def get_tasks(user_id: str = Depends(get_current_user)) -> list[dict]:
    """
    Get all tasks for user.

    Args:
        user_id: User ID

    Returns:
        List of tasks
    """
    try:
        tasks = await supabase_service.get_tasks(user_id)
        return tasks
    except Exception as e:
        logger.error(f"Failed to fetch tasks: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to fetch tasks")


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Get a specific task."""
    try:
        task = await supabase_service.get_task(task_id, user_id=user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch task: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to fetch task")


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    user_id: str = Depends(get_current_user),
) -> dict:
    """
    Update a task.

    Args:
        task_id: Task ID
        task_update: Updates to apply
        user_id: User ID

    Returns:
        Updated task
    """
    try:
        update_data = task_update.dict(exclude_unset=True)
        if "type" in update_data:
            update_data["type"] = update_data["type"].value
            if update_data["type"] == "gmail":
                raise HTTPException(
                    status_code=400,
                    detail="Changing a task into a Gmail action is not allowed. Create it through the chat confirmation flow.",
                )
            if update_data["type"] == "whatsapp":
                await plan_service.ensure_feature_available(user_id, "whatsapp_messages")
        if "priority" in update_data:
            update_data["priority"] = update_data["priority"].value
        if "due_date" in update_data and update_data["due_date"]:
            update_data["due_date"] = update_data["due_date"].isoformat()

        task = await supabase_service.update_task(task_id, user_id=user_id, **update_data)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to update task")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    """Delete a task."""
    try:
        success = await supabase_service.delete_task(task_id, user_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        if is_connectivity_error(e):
            raise HTTPException(status_code=503, detail=SUPABASE_UNREACHABLE_DETAIL)
        raise HTTPException(status_code=500, detail="Failed to delete task")
