from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FormulaCreate(BaseModel):
    client_id: str
    formula_name: str
    formula_details: str
    date_created: Optional[datetime] = None

class FormulaResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    formula_name: str
    formula_details: str
    date_created: datetime
