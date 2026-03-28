# ═══════════════════════════════════════════════════════════════════════════════
# STYLIST PROFILE MODELS - Core Schema for Stylist Hub
# ═══════════════════════════════════════════════════════════════════════════════
# Defines the canonical data structure for stylist profiles
# ═══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class StylistProfile(BaseModel):
    """
    Core Stylist Profile Schema
    Used for Stylist Hub, Discovery, and Profile Management
    """
    
    # --- Core Identity ---
    full_name: str
    email: EmailStr
    profile_icon_url: Optional[str] = None  # Link to the uploaded picture
    
    # --- The Stylist Hub (Viral Features) ---
    bio: Optional[str] = "Professional Hairstylist"
    specialties: List[str] = []  # e.g., ["Colorist", "Extensions", "Braiding"]
    credentials: Optional[str] = None  # License number or certifications
    is_verified: bool = False  # For the "Upper Hand" verified badge
    
    # --- Location & Business ---
    city: Optional[str] = None
    salon_name: Optional[str] = None
    business_name: Optional[str] = None
    
    # --- Networking / Social Links ---
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    website_url: Optional[str] = None
    portfolio_images: List[str] = []  # List of links to their work photos
    
    # --- System Controls ---
    is_tester: bool = False  # The "Apple Reviewer" pass - bypasses paywall
    subscription_active: bool = False  # The 3-use/paywall gate
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Sarah Mitchell",
                "email": "sarah@styleflow.com",
                "profile_icon_url": "https://cdn.styleflow.com/avatars/sarah.jpg",
                "bio": "Color specialist with 10+ years of experience",
                "specialties": ["Colorist", "Balayage", "Highlights"],
                "credentials": "CA License #12345",
                "is_verified": True,
                "city": "Los Angeles",
                "salon_name": "Luxe Hair Studio",
                "instagram_handle": "@sarahmitchellhair",
                "portfolio_images": [
                    "https://cdn.styleflow.com/portfolio/work1.jpg",
                    "https://cdn.styleflow.com/portfolio/work2.jpg"
                ],
                "is_tester": False,
                "subscription_active": True
            }
        }


class StylistProfileUpdate(BaseModel):
    """Schema for updating stylist profile fields"""
    
    full_name: Optional[str] = None
    profile_icon_url: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    credentials: Optional[str] = None
    city: Optional[str] = None
    salon_name: Optional[str] = None
    business_name: Optional[str] = None
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    website_url: Optional[str] = None


class StylistProfileResponse(BaseModel):
    """Response schema for stylist profile with stats"""
    
    id: str
    full_name: str
    email: Optional[str] = None  # Hidden for privacy in public views
    profile_icon_url: Optional[str] = None
    
    # Hub features
    bio: Optional[str] = None
    specialties: List[str] = []
    credentials: Optional[str] = None
    is_verified: bool = False
    
    # Location
    city: Optional[str] = None
    salon_name: Optional[str] = None
    business_name: Optional[str] = None
    
    # Social
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    website_url: Optional[str] = None
    portfolio_images: List[str] = []
    
    # Stats (computed)
    followers_count: int = 0
    following_count: int = 0
    portfolio_count: int = 0
    
    # Relationship flags
    is_following: bool = False
    is_own_profile: bool = False
    
    # System
    is_tester: bool = False
    subscription_active: bool = False


class StylistDiscoveryItem(BaseModel):
    """Compact schema for discovery/search results"""
    
    id: str
    full_name: str
    profile_icon_url: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    specialties: List[str] = []
    is_verified: bool = False
    is_featured: bool = False
    followers_count: int = 0
    portfolio_count: int = 0


class PortfolioImage(BaseModel):
    """Schema for portfolio images"""
    
    id: str
    image_url: str
    caption: Optional[str] = None
    created_at: Optional[datetime] = None


class CredentialsUpdate(BaseModel):
    """Schema for updating credentials/verification"""
    
    license_number: Optional[str] = None
    license_state: Optional[str] = None
    certifications: Optional[List[str]] = []
    
    # Combined credentials string for display
    @property
    def credentials_display(self) -> str:
        parts = []
        if self.license_state and self.license_number:
            parts.append(f"{self.license_state} License #{self.license_number}")
        if self.certifications:
            parts.extend(self.certifications)
        return " | ".join(parts) if parts else ""
