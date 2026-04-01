# ═══════════════════════════════════════════════════════════════════════════════
# PROFILES.PY - Stylist Hub Profile & Avatar Management
# ═══════════════════════════════════════════════════════════════════════════════
# LOCK_STYLIST_HUB_V1: 2025-03-28
# PRODUCTION: Cloudinary CDN with unsigned upload preset
#
# Features:
#   - Cloudinary avatar upload (JPG/PNG, optimized delivery)
#   - Portfolio image management
#   - Credential/License badge management
#   - Enhanced discovery search (City, Name, Specialty)
#   - Tester account pre-population for App Store review
#
# Cloudinary Production Config:
#   - Cloud Name: dqq3nmkgd
#   - Upload Preset: Emergent (Unsigned)
#   - Asset Folder: styleflow_uploads
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import cloudinary
import cloudinary.uploader
import base64
import logging
import re

from core.database import db
from core.config import settings
from core.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["Stylist Hub"])

# ==================== CONSTANTS ====================

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB limit for ultimate speed
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']

# ==================== BASIC PROFILE ENDPOINTS ====================

@router.get("/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's basic profile information"""
    user_id = str(current_user["_id"])
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "business_name": user.get("business_name"),
        "bio": user.get("bio"),
        "profile_photo": user.get("profile_photo"),
        "city": user.get("city"),
        "specialties": user.get("specialties"),
        "social_links": user.get("social_links", {}),
        "subscription_status": user.get("subscription_status"),
        "is_tester": user.get("is_tester", False),
        "is_admin": user.get("is_admin", False),
        "created_at": user.get("created_at"),
    }

# Cloudinary Production Settings
CLOUDINARY_FOLDER = getattr(settings, 'CLOUDINARY_ASSET_FOLDER', 'styleflow_uploads')
CLOUDINARY_UPLOAD_PRESET = getattr(settings, 'CLOUDINARY_UPLOAD_PRESET', 'Emergent')

# Initialize Cloudinary
cloudinary.config(
    cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'dqq3nmkgd'),
    api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
    api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
    secure=True
)

# ==================== MODELS ====================

class AvatarUpload(BaseModel):
    image_base64: str  # Base64 encoded JPG/PNG
    
    @validator('image_base64')
    def validate_image(cls, v):
        if not v:
            raise ValueError('No image data provided')
        
        # Remove data URL prefix if present
        clean_data = v
        if 'base64,' in v:
            # Extract mime type for validation
            header = v.split('base64,')[0]
            if not any(mime in header.lower() for mime in ['image/jpeg', 'image/jpg', 'image/png']):
                raise ValueError('Only JPG and PNG images are allowed')
            clean_data = v.split('base64,')[1]
        
        # Check base64 size (approximate - base64 is ~33% larger than binary)
        try:
            decoded_size = len(base64.b64decode(clean_data))
            if decoded_size > MAX_IMAGE_SIZE_BYTES:
                raise ValueError(f'Image too large. Maximum size is 5MB, got {decoded_size / (1024*1024):.1f}MB')
        except Exception as e:
            if 'Image too large' in str(e):
                raise
            raise ValueError('Invalid base64 image data')
        
        return v

class PortfolioImageUpload(BaseModel):
    image_base64: str
    caption: Optional[str] = None
    
    @validator('image_base64')
    def validate_image(cls, v):
        if not v:
            raise ValueError('No image data provided')
        
        clean_data = v
        if 'base64,' in v:
            header = v.split('base64,')[0]
            if not any(mime in header.lower() for mime in ['image/jpeg', 'image/jpg', 'image/png']):
                raise ValueError('Only JPG and PNG images are allowed')
            clean_data = v.split('base64,')[1]
        
        try:
            decoded_size = len(base64.b64decode(clean_data))
            if decoded_size > MAX_IMAGE_SIZE_BYTES:
                raise ValueError(f'Image too large. Maximum size is 5MB')
        except Exception as e:
            if 'Image too large' in str(e):
                raise
            raise ValueError('Invalid base64 image data')
        
        return v

class CredentialUpdate(BaseModel):
    license_number: Optional[str] = None
    license_state: Optional[str] = None
    is_verified: Optional[bool] = False
    certifications: Optional[List[str]] = []

# ==================== TESTER PORTFOLIOS ====================

TESTER_PORTFOLIO_IMAGES = [
    {
        "image": "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=600",
        "caption": "Balayage masterpiece - warm caramel tones"
    },
    {
        "image": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600",
        "caption": "Platinum blonde transformation"
    },
    {
        "image": "https://images.unsplash.com/photo-1595475038784-bbe439ff41e6?w=600",
        "caption": "Dimensional highlights - sun-kissed finish"
    },
    {
        "image": "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=600",
        "caption": "Vivid fashion color - galaxy blend"
    },
    {
        "image": "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=600",
        "caption": "Classic bob cut - sleek finish"
    },
    {
        "image": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=600",
        "caption": "Natural curls - moisture treatment"
    }
]

async def populate_tester_portfolio(user_id: str):
    """Pre-populate portfolio for tester accounts (App Store Review)"""
    existing = await db.portfolio.count_documents({"user_id": user_id})
    if existing > 0:
        return  # Already has portfolio
    
    for item in TESTER_PORTFOLIO_IMAGES:
        await db.portfolio.insert_one({
            "user_id": user_id,
            "image": item["image"],
            "caption": item["caption"],
            "created_at": datetime.utcnow()
        })

# ==================== AVATAR UPLOAD ====================

@router.post("/avatar")
async def upload_avatar(
    data: AvatarUpload,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload profile picture to Cloudinary
    
    VALIDATION RULES:
    - Only JPG/PNG images allowed
    - Maximum file size: 5MB
    - Images auto-cropped to 400x400 with face detection
    
    Returns: Optimized Cloudinary URL or base64 fallback
    """
    try:
        # Get clean base64 data
        image_data = data.image_base64
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        # Check Cloudinary configuration
        cloudinary_configured = bool(getattr(settings, 'CLOUDINARY_API_KEY', ''))
        
        if cloudinary_configured:
            # Upload to Cloudinary with production settings
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{image_data}",
                folder=f"{CLOUDINARY_FOLDER}/avatars",
                public_id=f"user_{str(current_user['_id'])}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            avatar_url = upload_result.get("secure_url")
            storage_type = "cloudinary"
        else:
            # Fallback: Store as base64 if Cloudinary not configured
            avatar_url = f"data:image/jpeg;base64,{image_data}"
            storage_type = "base64"
        
        # Update user profile with both fields for compatibility
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {
                "profile_photo": avatar_url,
                "profile_image_url": avatar_url,  # Schema field
                "avatar_updated_at": datetime.utcnow(),
                "avatar_storage_type": storage_type
            }}
        )
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "storage_type": storage_type,
            "message": "Avatar uploaded successfully"
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ==================== PORTFOLIO IMAGE UPLOAD ====================

@router.post("/portfolio")
async def upload_portfolio_image(
    data: PortfolioImageUpload,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a portfolio/work image
    
    VALIDATION RULES:
    - Only JPG/PNG images allowed
    - Maximum file size: 5MB
    - Images optimized for gallery display
    """
    user_id = str(current_user["_id"])
    
    try:
        # Get clean base64 data
        image_data = data.image_base64
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        # Check Cloudinary configuration
        cloudinary_configured = bool(getattr(settings, 'CLOUDINARY_API_KEY', ''))
        
        # Generate unique ID for this portfolio item
        import uuid
        portfolio_id = str(uuid.uuid4())[:8]
        
        if cloudinary_configured:
            # Upload to Cloudinary with production settings
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{image_data}",
                folder=f"{CLOUDINARY_FOLDER}/portfolio",
                public_id=f"user_{user_id}_{portfolio_id}",
                resource_type="image",
                transformation=[
                    {"width": 800, "height": 800, "crop": "limit"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            image_url = upload_result.get("secure_url")
        else:
            # Fallback: Store as base64
            image_url = f"data:image/jpeg;base64,{image_data}"
        
        # Create portfolio document
        portfolio_doc = {
            "user_id": user_id,
            "image": image_url,
            "caption": data.caption or "",
            "created_at": datetime.utcnow()
        }
        
        result = await db.portfolio.insert_one(portfolio_doc)
        
        # Also update user's portfolio_images array
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$push": {"portfolio_images": image_url}}
        )
        
        return {
            "success": True,
            "portfolio_id": str(result.inserted_id),
            "image_url": image_url,
            "message": "Portfolio image uploaded successfully"
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logging.error(f"Portfolio upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.delete("/portfolio/{portfolio_id}")
async def delete_portfolio_image(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a portfolio image"""
    user_id = str(current_user["_id"])
    
    try:
        # Find the portfolio item
        item = await db.portfolio.find_one({
            "_id": ObjectId(portfolio_id),
            "user_id": user_id
        })
        
        if not item:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
        
        # Delete from database
        await db.portfolio.delete_one({"_id": ObjectId(portfolio_id)})
        
        # Remove from user's portfolio_images array
        image_url = item.get("image")
        if image_url:
            await db.users.update_one(
                {"_id": current_user["_id"]},
                {"$pull": {"portfolio_images": image_url}}
            )
        
        return {"success": True, "message": "Portfolio image deleted"}
        
    except Exception as e:
        logging.error(f"Portfolio delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CREDENTIAL BADGES ====================

@router.post("/credentials")
async def update_credentials(
    data: CredentialUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update stylist credentials/license information"""
    update_data = {
        "credentials": {
            "license_number": data.license_number,
            "license_state": data.license_state,
            "is_verified": data.is_verified,
            "certifications": data.certifications or [],
            "updated_at": datetime.utcnow()
        }
    }
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Credentials updated"}

@router.get("/credentials")
async def get_credentials(current_user: dict = Depends(get_current_user)):
    """Get current user's credentials"""
    credentials = current_user.get("credentials", {})
    return {
        "license_number": credentials.get("license_number"),
        "license_state": credentials.get("license_state"),
        "is_verified": credentials.get("is_verified", False),
        "certifications": credentials.get("certifications", [])
    }

# ==================== ENHANCED DISCOVERY ====================

@router.get("/discover")
async def discover_stylists(
    city: Optional[str] = None,
    name: Optional[str] = None,
    specialty: Optional[str] = None,
    featured: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Enhanced stylist discovery with filters
    - city: Filter by city/location
    - name: Search by name or business name
    - specialty: Filter by specialty (e.g., "balayage", "color")
    - featured: Show only featured/verified stylists
    """
    current_user_id = str(current_user["_id"])
    
    # Build exclusion list (blocked users)
    blocked_by_me = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    blocked_me = await db.blocks.find({"blocked_id": current_user_id}).to_list(1000)
    blocked_ids = [b["blocked_id"] for b in blocked_by_me] + [b["blocker_id"] for b in blocked_me]
    blocked_object_ids = [ObjectId(bid) for bid in blocked_ids if bid]
    
    # Base query
    query = {
        "profile_visibility": {"$in": ["public", None]},
        "moderation_status": {"$nin": ["banned", "suspended"]},
        "_id": {"$nin": blocked_object_ids + [current_user["_id"]]}
    }
    
    # Apply filters
    filters = []
    
    if city:
        filters.append({"city": {"$regex": city, "$options": "i"}})
    
    if name:
        filters.append({
            "$or": [
                {"full_name": {"$regex": name, "$options": "i"}},
                {"business_name": {"$regex": name, "$options": "i"}}
            ]
        })
    
    if specialty:
        filters.append({"specialties": {"$regex": specialty, "$options": "i"}})
    
    if featured:
        filters.append({
            "$or": [
                {"credentials.is_verified": True},
                {"is_tester": True}  # Testers show as featured for demo
            ]
        })
    
    if filters:
        query["$and"] = filters
    
    # Execute query with sorting (verified first, then by followers)
    users = await db.users.find(query).sort([
        ("credentials.is_verified", -1),
        ("is_tester", -1)
    ]).limit(limit).to_list(limit)
    
    # Enrich results with follower counts
    results = []
    for user in users:
        user_id = str(user["_id"])
        
        # Get follower count
        followers_count = await db.follows.count_documents({"following_id": user_id})
        
        # Get portfolio count
        portfolio_count = await db.portfolio.count_documents({"user_id": user_id})
        
        credentials = user.get("credentials", {})
        
        # Ensure specialties is a list
        specialties_raw = user.get("specialties", [])
        if isinstance(specialties_raw, str):
            specialties_list = [s.strip() for s in specialties_raw.split(",") if s.strip()]
        else:
            specialties_list = specialties_raw or []
        
        results.append({
            "id": user_id,
            "full_name": user.get("full_name"),
            "profile_icon_url": user.get("profile_photo") or user.get("profile_icon_url"),
            "profile_photo": user.get("profile_photo"),  # Legacy support
            "bio": user.get("bio", "Professional Hairstylist"),
            "city": user.get("city"),
            "specialties": specialties_list,
            "business_name": user.get("business_name"),
            "is_verified": credentials.get("is_verified", False),
            "is_featured": user.get("is_tester", False) or credentials.get("is_verified", False),
            "followers_count": followers_count,
            "portfolio_count": portfolio_count
        })
    
    return results

# ==================== FULL PROFILE WITH PORTFOLIO ====================

@router.get("/{user_id}")
async def get_stylist_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full stylist profile with portfolio for Stylist Hub
    Returns Instagram-style profile data
    """
    current_user_id = str(current_user["_id"])
    
    # Check block status
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": current_user_id, "blocked_id": user_id},
            {"blocker_id": user_id, "blocked_id": current_user_id}
        ]
    })
    
    if block:
        raise HTTPException(status_code=403, detail="Cannot view this profile")
    
    # Get user
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check moderation status
    if user.get("moderation_status") == "banned":
        raise HTTPException(status_code=404, detail="User not found")
    
    # Populate tester portfolio if needed
    if user.get("is_tester"):
        await populate_tester_portfolio(user_id)
    
    # Get social stats
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})
    
    # Check if current user follows
    is_following = await db.follows.find_one({
        "follower_id": current_user_id,
        "following_id": user_id
    }) is not None
    
    # Get portfolio
    portfolio = await db.portfolio.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    portfolio_items = [{
        "id": str(item["_id"]),
        "image": item.get("image"),
        "caption": item.get("caption"),
        "created_at": item.get("created_at")
    } for item in portfolio]
    
    # Get posts count
    posts_count = await db.posts.count_documents({"user_id": user_id})
    
    credentials = user.get("credentials", {})
    
    # Build credentials string for display
    creds_parts = []
    if credentials.get("license_state") and credentials.get("license_number"):
        creds_parts.append(f"{credentials.get('license_state')} License #{credentials.get('license_number')}")
    if credentials.get("certifications"):
        creds_parts.extend(credentials.get("certifications", []))
    credentials_display = " | ".join(creds_parts) if creds_parts else None
    
    # Ensure specialties is a list
    specialties_raw = user.get("specialties", [])
    if isinstance(specialties_raw, str):
        specialties_list = [s.strip() for s in specialties_raw.split(",") if s.strip()]
    else:
        specialties_list = specialties_raw or []
    
    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "profile_icon_url": user.get("profile_photo") or user.get("profile_icon_url"),
        "profile_photo": user.get("profile_photo"),  # Legacy support
        
        # Stylist Hub features
        "bio": user.get("bio", "Professional Hairstylist"),
        "specialties": specialties_list,
        "credentials": credentials_display,
        "is_verified": credentials.get("is_verified", False),
        
        # Location & Business
        "business_name": user.get("business_name"),
        "salon_name": user.get("salon_name"),
        "city": user.get("city"),
        
        # Social links
        "instagram_handle": user.get("instagram_handle"),
        "tiktok_handle": user.get("tiktok_handle"),
        "website_url": user.get("website_url"),
        "portfolio_images": user.get("portfolio_images", []),
        
        # Stats
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "portfolio_count": len(portfolio_items),
        
        # Relationship
        "is_following": is_following,
        "is_own_profile": current_user_id == user_id,
        
        # System Controls
        "is_tester": user.get("is_tester", False),
        "subscription_active": user.get("subscription_status") == "active" or user.get("is_tester", False),
        
        # Credentials detail (for backward compatibility)
        "license_state": credentials.get("license_state"),
        "certifications": credentials.get("certifications", []),
        
        # Portfolio grid
        "portfolio": portfolio_items
    }

# ==================== MY PROFILE QUICK ACCESS ====================

@router.get("/me/hub")
async def get_my_hub_profile(current_user: dict = Depends(get_current_user)):
    """Quick access to own profile for Stylist Hub view"""
    user_id = str(current_user["_id"])
    
    # Populate tester portfolio if needed
    if current_user.get("is_tester"):
        await populate_tester_portfolio(user_id)
    
    # Get stats
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})
    posts_count = await db.posts.count_documents({"user_id": user_id})
    
    # Get portfolio
    portfolio = await db.portfolio.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    portfolio_items = [{
        "id": str(item["_id"]),
        "image": item.get("image"),
        "caption": item.get("caption"),
        "created_at": item.get("created_at")
    } for item in portfolio]
    
    credentials = current_user.get("credentials", {})
    
    # Build credentials string for display
    creds_parts = []
    if credentials.get("license_state") and credentials.get("license_number"):
        creds_parts.append(f"{credentials.get('license_state')} License #{credentials.get('license_number')}")
    if credentials.get("certifications"):
        creds_parts.extend(credentials.get("certifications", []))
    credentials_display = " | ".join(creds_parts) if creds_parts else None
    
    # Ensure specialties is a list
    specialties_raw = current_user.get("specialties", [])
    if isinstance(specialties_raw, str):
        specialties_list = [s.strip() for s in specialties_raw.split(",") if s.strip()]
    else:
        specialties_list = specialties_raw or []
    
    return {
        "id": user_id,
        "full_name": current_user.get("full_name"),
        "email": current_user.get("email"),
        "profile_icon_url": current_user.get("profile_photo") or current_user.get("profile_icon_url"),
        "profile_photo": current_user.get("profile_photo"),  # Legacy support
        
        # Stylist Hub features
        "bio": current_user.get("bio", "Professional Hairstylist"),
        "specialties": specialties_list,
        "credentials": credentials_display,
        "is_verified": credentials.get("is_verified", False),
        
        # Location & Business
        "business_name": current_user.get("business_name"),
        "salon_name": current_user.get("salon_name"),
        "city": current_user.get("city"),
        
        # Social links
        "instagram_handle": current_user.get("instagram_handle"),
        "tiktok_handle": current_user.get("tiktok_handle"),
        "website_url": current_user.get("website_url"),
        "portfolio_images": current_user.get("portfolio_images", []),
        
        # Stats
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "portfolio_count": len(portfolio_items),
        
        # System Controls
        "is_tester": current_user.get("is_tester", False),
        "subscription_active": current_user.get("subscription_status") == "active" or current_user.get("is_tester", False),
        
        # Credentials detail (for backward compatibility)
        "license_state": credentials.get("license_state"),
        "certifications": credentials.get("certifications", []),
        
        # Portfolio grid
        "portfolio": portfolio_items,
        
        "is_own_profile": True
    }
