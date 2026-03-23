from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GalleryCreate(BaseModel):
    client_id: str
    before_photo: Optional[str] = None
    after_photo: Optional[str] = None
    notes: Optional[str] = None
    date_taken: Optional[datetime] = None

class GalleryResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    before_photo: Optional[str] = None
    after_photo: Optional[str] = None
    notes: Optional[str] = None
    date_taken: datetime
