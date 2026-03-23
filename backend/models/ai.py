from pydantic import BaseModel
from typing import Optional

class AIMessageRequest(BaseModel):
    message: str
    context: Optional[str] = None

class AIMessageResponse(BaseModel):
    response: str
