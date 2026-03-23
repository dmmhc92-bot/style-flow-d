from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IncomeCreate(BaseModel):
    client_id: Optional[str] = None
    amount: float
    service: str
    date: Optional[datetime] = None
    payment_method: Optional[str] = None

class IncomeResponse(BaseModel):
    id: str
    user_id: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    amount: float
    service: str
    date: datetime
    payment_method: Optional[str] = None

class RetailCreate(BaseModel):
    client_id: str
    product_name: str
    recommended: bool = True
    purchased: bool = False
    date: Optional[datetime] = None

class RetailResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    client_name: Optional[str] = None
    product_name: str
    recommended: bool
    purchased: bool
    date: datetime

class NoShowCreate(BaseModel):
    client_id: str
    appointment_date: datetime
    notes: Optional[str] = None

class NoShowResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    client_name: Optional[str] = None
    appointment_date: datetime
    notes: Optional[str] = None
    created_at: datetime
