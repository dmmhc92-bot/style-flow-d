from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    hair_goals: Optional[str] = None
    is_vip: bool = False
    last_visit: Optional[datetime] = None
    rebook_interval_days: Optional[int] = 42

class ClientResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    hair_goals: Optional[str] = None
    is_vip: bool = False
    visit_count: int = 0
    last_visit: Optional[datetime] = None
    created_at: datetime
    rebook_interval_days: Optional[int] = 42
    next_visit_due: Optional[datetime] = None
    rebook_status: Optional[str] = None
