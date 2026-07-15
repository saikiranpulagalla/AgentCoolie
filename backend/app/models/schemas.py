"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ User Models ============
class UserBase(BaseModel):
    """Base user model."""
    username: str
    email: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = None
    email: Optional[str] = None


class User(UserBase):
    """User response model."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Chat Models ============
class ChatMessageRequest(BaseModel):
    """Chat message request."""
    content: str = Field(min_length=1, max_length=12000)
    attachments: Optional[List[dict]] = Field(default=None, max_length=4)
    conversationId: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: str
    content: str
    role: str  # "user" | "assistant"
    timestamp: datetime
    model: Optional[str] = None
    attachments: Optional[List[dict]] = None

    class Config:
        from_attributes = True


# ============ Task Models ============
class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, Enum):
    """Task types."""
    GENERAL = "general"
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    REMINDER = "reminder"
    YOUTUBE = "youtube"
    WEBSITE = "website"


class TaskCreate(BaseModel):
    """Task creation model."""
    title: str
    description: Optional[str] = None
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Task update model."""
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    priority: Optional[TaskPriority] = None
    completed: Optional[bool] = None
    due_date: Optional[datetime] = None


class Task(TaskCreate):
    """Task response model."""
    id: str
    completed: bool = False
    created_at: datetime
    user_id: str

    class Config:
        from_attributes = True


# ============ Personalization Models ============
class Tone(str, Enum):
    """Response tone."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"


class ResponseLength(str, Enum):
    """Response length preference."""
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"


class Formality(str, Enum):
    """Supported response formality values shared with the preferences API."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PersonalizationSettings(BaseModel):
    """Personalization settings."""
    tone: Tone = Tone.PROFESSIONAL
    response_length: ResponseLength = ResponseLength.MODERATE
    formality: Formality = Formality.MEDIUM
    include_emojis: bool = False


# ============ User Preferences Models ============
class Theme(str, Enum):
    """Theme preference."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class UserPreferences(BaseModel):
    """User preferences."""
    theme: Theme = Theme.SYSTEM
    notifications_enabled: bool = True
    language: str = "en"
    personalization: PersonalizationSettings = PersonalizationSettings()

    class Config:
        from_attributes = True


# ============ WhatsApp Models ============
class WhatsappMessage(BaseModel):
    """WhatsApp message model."""
    from_number: str
    to_number: str
    message_text: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None


class WhatsappWebhookRequest(BaseModel):
    """WhatsApp webhook request."""
    messages: Optional[List[dict]] = None
    statuses: Optional[List[dict]] = None


# ============ Gmail Models ============
class GmailCredentials(BaseModel):
    """Gmail credentials (after OAuth)."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: datetime


class GmailMessage(BaseModel):
    """Gmail message model."""
    subject: str
    from_email: str
    to_email: str
    body_text: str
    body_html: Optional[str] = None
    attachments: Optional[List[dict]] = None


# ============ Generic Response Models ============
class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str
    data: Optional[dict] = None


# ============ Authentication Models ============
class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class FirebaseUser(BaseModel):
    """Firebase user information."""
    uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
