from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    business_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    email: EmailStr
    full_name: str
    business_name: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[str] = None
    salon_name: Optional[str] = None
    city: Optional[str] = None
    profile_photo: Optional[str] = None
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    website_url: Optional[str] = None
    profile_visibility: str = "public"
    created_at: datetime

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
