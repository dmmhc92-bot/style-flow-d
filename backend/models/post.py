from pydantic import BaseModel
from typing import List, Optional

TREND_TAGS = [
    "balayage", "colortrend", "transformation", "mensstyle", "curlyhair",
    "blondehair", "brunette", "redhead", "highlights", "lowlights",
    "ombre", "sombre", "haircut", "pixiecut", "bobcut", "layers",
    "extensions", "braids", "updo", "wedding", "editorial", "natural",
    "vivids", "pastels", "colorcorrection", "keratintreatment", "textured"
]

class PostCreate(BaseModel):
    images: List[str]
    caption: Optional[str] = None
    tags: Optional[List[str]] = []

class PostUpdate(BaseModel):
    caption: Optional[str] = None
    tags: Optional[List[str]] = None

class CommentCreate(BaseModel):
    text: str

class ShareCreate(BaseModel):
    caption: Optional[str] = None
