from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AppointmentCreate(BaseModel):
    client_id: str
    appointment_date: datetime
    service: str
    duration_minutes: Optional[int] = 60
    notes: Optional[str] = None
    status: str = "scheduled"

class AppointmentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    client_name: Optional[str] = None
    appointment_date: datetime
    service: str
    duration_minutes: int
    notes: Optional[str] = None
    status: str
