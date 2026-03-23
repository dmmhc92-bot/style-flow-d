from pydantic import BaseModel
from typing import Optional
from datetime import datetime

REPORT_REASONS = [
    "harassment",
    "inappropriate", 
    "spam",
    "hate_speech",
    "sexual_content",
    "illegal",
    "impersonation",
    "other"
]

MODERATION_ACTIONS = ["dismiss", "warn", "remove_content", "restrict", "suspend", "ban"]
APPEAL_STATUSES = ["pending", "under_review", "approved", "denied"]

class ReportCreate(BaseModel):
    reported_user_id: str
    content_type: str
    content_id: Optional[str] = None
    reason: str
    details: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: str
    content_type: str
    content_id: Optional[str] = None
    reason: str
    details: Optional[str] = None
    status: str
    created_at: datetime

class BlockCreate(BaseModel):
    blocked_user_id: str

class ModerationAction(BaseModel):
    action: str
    reason: Optional[str] = None
    duration_days: Optional[int] = None

class AppealCreate(BaseModel):
    reason: str
    additional_details: Optional[str] = None

class AppealAction(BaseModel):
    action: str
    admin_notes: Optional[str] = None
