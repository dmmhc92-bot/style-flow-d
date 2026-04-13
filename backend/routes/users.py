from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from bson import ObjectId

from core.database import db
from core.dependencies import get_current_user

router = APIRouter(tags=["Users"])

# ==================== USER DISCOVERY & COMMUNITY ====================

@router.get("/users/discover")
async def discover_users(search: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    # Get list of blocked users (both directions)
    blocked_by_me = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    blocked_me = await db.blocks.find({"blocked_id": current_user_id}).to_list(1000)
    
    blocked_ids = [b["blocked_id"] for b in blocked_by_me] + [b["blocker_id"] for b in blocked_me]
    
    # Safely convert to ObjectIds, skipping invalid ones
    blocked_object_ids = []
    for bid in blocked_ids:
        if bid:
            try:
                blocked_object_ids.append(ObjectId(bid))
            except Exception:
                pass  # Skip invalid ObjectIds
    
    query = {
        "profile_visibility": "public",
        "moderation_status": {"$nin": ["banned", "suspended"]},
        "_id": {"$nin": blocked_object_ids + [current_user["_id"]]}
    }
    
    if search:
        query["$or"] = [
            {"full_name": {"$regex": search, "$options": "i"}},
            {"business_name": {"$regex": search, "$options": "i"}},
            {"city": {"$regex": search, "$options": "i"}},
            {"specialties": {"$regex": search, "$options": "i"}}
        ]
    
    users = await db.users.find(query).limit(50).to_list(50)
    
    result = []
    for user in users:
        result.append({
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "business_name": user.get("business_name"),
            "city": user.get("city"),
            "specialties": user.get("specialties"),
            "profile_photo": user.get("profile_photo"),
            "bio": user.get("bio"),
        })
    
    return result

@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    # Check if blocked
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": current_user_id, "blocked_id": user_id},
            {"blocker_id": user_id, "blocked_id": current_user_id}
        ]
    })
    
    if block:
        raise HTTPException(status_code=403, detail="Cannot view this profile")
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if banned/suspended
    if user.get("moderation_status") == "banned":
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("profile_visibility") == "private" and str(user["_id"]) != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Profile is private")
    
    # Check if current user follows this user
    follow = await db.follows.find_one({
        "follower_id": str(current_user["_id"]),
        "following_id": user_id
    })
    
    # Get follower/following counts
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})
    
    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "business_name": user.get("business_name"),
        "bio": user.get("bio"),
        "salon_name": user.get("salon_name"),
        "city": user.get("city"),
        "specialties": user.get("specialties"),
        "profile_photo": user.get("profile_photo"),
        "instagram_handle": user.get("instagram_handle"),
        "tiktok_handle": user.get("tiktok_handle"),
        "website_url": user.get("website_url"),
        "is_following": follow is not None,
        "followers_count": followers_count,
        "following_count": following_count,
    }

# ==================== FOLLOW/UNFOLLOW ENDPOINTS ====================

@router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if target user exists
    try:
        target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = await db.follows.find_one({
        "follower_id": current_user_id,
        "following_id": user_id
    })
    
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")
    
    # Create follow relationship
    await db.follows.insert_one({
        "follower_id": current_user_id,
        "following_id": user_id,
        "created_at": datetime.utcnow()
    })
    
    return {"message": "User followed successfully"}

@router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    # Remove follow relationship
    result = await db.follows.delete_one({
        "follower_id": current_user_id,
        "following_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not following this user")
    
    return {"message": "User unfollowed successfully"}

@router.delete("/users/{user_id}/follower")
async def remove_follower(user_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a follower from your followers list"""
    current_user_id = str(current_user["_id"])
    
    # Remove the follow relationship where user_id is following current_user
    result = await db.follows.delete_one({
        "follower_id": user_id,
        "following_id": current_user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User is not following you")
    
    return {"message": "Follower removed successfully"}

@router.get("/users/following")
async def get_following_list(current_user: dict = Depends(get_current_user)):
    """Get list of users the current user is following"""
    current_user_id = str(current_user["_id"])
    
    # Get all follows where current user is the follower
    follows = await db.follows.find({"follower_id": current_user_id}).to_list(1000)
    
    result = []
    for follow in follows:
        try:
            user = await db.users.find_one({"_id": ObjectId(follow["following_id"])})
            if user:
                result.append({
                    "id": str(user["_id"]),
                    "full_name": user.get("full_name"),
                    "profile_photo": user.get("profile_photo"),
                    "business_name": user.get("business_name"),
                    "is_verified": user.get("is_verified", False),
                })
        except:
            continue
    
    return result

@router.get("/users/followers")
async def get_followers_list(current_user: dict = Depends(get_current_user)):
    """Get list of users following the current user"""
    current_user_id = str(current_user["_id"])
    
    # Get all follows where current user is being followed
    follows = await db.follows.find({"following_id": current_user_id}).to_list(1000)
    
    result = []
    for follow in follows:
        try:
            user = await db.users.find_one({"_id": ObjectId(follow["follower_id"])})
            if user:
                result.append({
                    "id": str(user["_id"]),
                    "full_name": user.get("full_name"),
                    "profile_photo": user.get("profile_photo"),
                    "business_name": user.get("business_name"),
                    "is_verified": user.get("is_verified", False),
                })
        except:
            continue
    
    return result

# ==================== CONNECTION MANAGEMENT ====================

@router.post("/connections/{user_id}")
async def add_connection(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself")
    
    # Check if already connected
    existing = await db.connections.find_one({
        "user_id": current_user_id,
        "connected_user_id": user_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already connected")
    
    # Check if user is blocked
    blocked = await db.blocks.find_one({
        "$or": [
            {"blocker_id": current_user_id, "blocked_id": user_id},
            {"blocker_id": user_id, "blocked_id": current_user_id}
        ]
    })
    
    if blocked:
        raise HTTPException(status_code=403, detail="Cannot connect with this user")
    
    # Create connection
    await db.connections.insert_one({
        "user_id": current_user_id,
        "connected_user_id": user_id,
        "created_at": datetime.utcnow()
    })
    
    return {"message": "Connection added successfully"}

@router.delete("/connections/{user_id}")
async def remove_connection(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    result = await db.connections.delete_one({
        "user_id": current_user_id,
        "connected_user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"message": "Connection removed successfully"}

@router.get("/connections")
async def get_connections(current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    connections = await db.connections.find({"user_id": current_user_id}).to_list(1000)
    
    result = []
    for conn in connections:
        try:
            user = await db.users.find_one({"_id": ObjectId(conn["connected_user_id"])})
            if user:
                result.append({
                    "id": str(user["_id"]),
                    "full_name": user.get("full_name"),
                    "business_name": user.get("business_name"),
                    "city": user.get("city"),
                    "profile_photo": user.get("profile_photo"),
                    "specialties": user.get("specialties"),
                })
        except:
            continue
    
    return result

# ==================== BLOCK SYSTEM ====================

@router.post("/block/{user_id}")
async def block_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    # Check if already blocked
    existing = await db.blocks.find_one({
        "blocker_id": current_user_id,
        "blocked_id": user_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="User already blocked")
    
    # Remove any existing connection
    await db.connections.delete_many({
        "$or": [
            {"user_id": current_user_id, "connected_user_id": user_id},
            {"user_id": user_id, "connected_user_id": current_user_id}
        ]
    })
    
    # Remove follow relationships
    await db.follows.delete_many({
        "$or": [
            {"follower_id": current_user_id, "following_id": user_id},
            {"follower_id": user_id, "following_id": current_user_id}
        ]
    })
    
    # Create block
    await db.blocks.insert_one({
        "blocker_id": current_user_id,
        "blocked_id": user_id,
        "created_at": datetime.utcnow()
    })
    
    return {"message": "User blocked successfully"}

@router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    result = await db.blocks.delete_one({
        "blocker_id": current_user_id,
        "blocked_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not blocked")
    
    return {"message": "User unblocked successfully"}

@router.get("/blocked")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    blocks = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    
    result = []
    for block in blocks:
        try:
            user = await db.users.find_one({"_id": ObjectId(block["blocked_id"])})
            if user:
                result.append({
                    "id": str(user["_id"]),
                    "full_name": user.get("full_name"),
                    "business_name": user.get("business_name"),
                    "profile_photo": user.get("profile_photo"),
                    "blocked_at": block.get("created_at"),
                })
        except:
            continue
    
    return result

# ==================== PRIVACY SETTINGS ====================

@router.get("/privacy/settings")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    return {
        "profile_visibility": current_user.get("profile_visibility", "public"),
        "nearby_discoverable": current_user.get("nearby_discoverable", False),
        "contacts_discoverable": current_user.get("contacts_discoverable", False),
    }

@router.put("/privacy/settings")
async def update_privacy_settings(settings: dict, current_user: dict = Depends(get_current_user)):
    update_fields = {}
    
    if "profile_visibility" in settings:
        update_fields["profile_visibility"] = settings["profile_visibility"]
    
    if "nearby_discoverable" in settings:
        update_fields["nearby_discoverable"] = settings["nearby_discoverable"]
    
    if "contacts_discoverable" in settings:
        update_fields["contacts_discoverable"] = settings["contacts_discoverable"]
    
    if update_fields:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_fields}
        )
    
    return {"message": "Privacy settings updated successfully"}

# ==================== PORTFOLIO GALLERY ====================

@router.post("/portfolio")
async def add_portfolio_image(image_data: dict, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    portfolio_doc = {
        "user_id": user_id,
        "image": image_data.get("image"),
        "caption": image_data.get("caption"),
        "created_at": datetime.utcnow()
    }
    
    result = await db.portfolio.insert_one(portfolio_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "Image added to portfolio"
    }

@router.get("/portfolio")
async def get_portfolio(user_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    target_user_id = user_id if user_id else str(current_user["_id"])
    
    portfolio = await db.portfolio.find({"user_id": target_user_id}).sort("created_at", -1).to_list(1000)
    
    result = []
    for item in portfolio:
        result.append({
            "id": str(item["_id"]),
            "image": item.get("image"),
            "caption": item.get("caption"),
            "created_at": item.get("created_at")
        })
    
    return result

@router.delete("/portfolio/{image_id}")
async def delete_portfolio_image(image_id: str, current_user: dict = Depends(get_current_user)):
    try:
        result = await db.portfolio.delete_one({
            "_id": ObjectId(image_id),
            "user_id": str(current_user["_id"])
        })
    except:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {"message": "Image deleted successfully"}
