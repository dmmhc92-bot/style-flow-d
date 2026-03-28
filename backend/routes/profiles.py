# ═══════════════════════════════════════════════════════════════════════════════
# PROFILES.PY - Stylist Hub Profile & Avatar Management
# ═══════════════════════════════════════════════════════════════════════════════
# LOCK_STYLIST_HUB_V1: 2025-03-28
#
# Features:
#   - Cloudinary avatar upload (JPG/PNG, optimized delivery)
#   - Credential/License badge management
#   - Enhanced discovery search (City, Name, Specialty)
#   - Tester account pre-population for App Store review
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import cloudinary
import cloudinary.uploader
import base64
import logging

from core.database import db
from core.config import settings
from core.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["Stylist Hub"])

# Initialize Cloudinary
cloudinary.config(
    cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'demo'),
    api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
    api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
    secure=True
)

# ==================== MODELS ====================

class AvatarUpload(BaseModel):
    image_base64: str  # Base64 encoded JPG/PNG

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
    Accepts: Base64 encoded JPG/PNG
    Returns: Optimized Cloudinary URL
    """
    try:
        # Validate base64 image
        image_data = data.image_base64
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Remove data URL prefix if present
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        
        # Check Cloudinary configuration
        if not getattr(settings, 'CLOUDINARY_API_KEY', ''):
            # Fallback: Store as base64 if Cloudinary not configured
            avatar_url = f"data:image/jpeg;base64,{image_data}"
        else:
            # Upload to Cloudinary with optimization
            upload_result = cloudinary.uploader.upload(
                f"data:image/jpeg;base64,{image_data}",
                folder="styleflow/avatars",
                public_id=f"user_{str(current_user['_id'])}",
                overwrite=True,
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            avatar_url = upload_result.get("secure_url")
        
        # Update user profile with avatar URL
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {
                "profile_photo": avatar_url,
                "avatar_updated_at": datetime.utcnow()
            }}
        )
        
        return {
            "success": True,
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully"
        }
        
    except Exception as e:
        logging.error(f"Avatar upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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
        
        results.append({
            "id": user_id,
            "full_name": user.get("full_name"),
            "business_name": user.get("business_name"),
            "bio": user.get("bio"),
            "city": user.get("city"),
            "specialties": user.get("specialties"),
            "profile_photo": user.get("profile_photo"),
            "followers_count": followers_count,
            "portfolio_count": portfolio_count,
            "is_verified": credentials.get("is_verified", False),
            "is_featured": user.get("is_tester", False) or credentials.get("is_verified", False)
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
    
    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "business_name": user.get("business_name"),
        "bio": user.get("bio"),
        "salon_name": user.get("salon_name"),
        "city": user.get("city"),
        "specialties": user.get("specialties"),
        "profile_photo": user.get("profile_photo"),
        
        # Social links
        "instagram_handle": user.get("instagram_handle"),
        "tiktok_handle": user.get("tiktok_handle"),
        "website_url": user.get("website_url"),
        
        # Stats
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "portfolio_count": len(portfolio_items),
        
        # Relationship
        "is_following": is_following,
        "is_own_profile": current_user_id == user_id,
        
        # Credentials
        "is_verified": credentials.get("is_verified", False),
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
    
    return {
        "id": user_id,
        "full_name": current_user.get("full_name"),
        "business_name": current_user.get("business_name"),
        "bio": current_user.get("bio"),
        "salon_name": current_user.get("salon_name"),
        "city": current_user.get("city"),
        "specialties": current_user.get("specialties"),
        "profile_photo": current_user.get("profile_photo"),
        
        # Social links
        "instagram_handle": current_user.get("instagram_handle"),
        "tiktok_handle": current_user.get("tiktok_handle"),
        "website_url": current_user.get("website_url"),
        
        # Stats
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "portfolio_count": len(portfolio_items),
        
        # Credentials
        "is_verified": credentials.get("is_verified", False),
        "license_state": credentials.get("license_state"),
        "certifications": credentials.get("certifications", []),
        
        # Portfolio grid
        "portfolio": portfolio_items,
        
        "is_own_profile": True
    }
