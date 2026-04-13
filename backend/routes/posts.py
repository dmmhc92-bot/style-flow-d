from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import cloudinary
import cloudinary.uploader
import base64
import logging

from core.database import db
from core.dependencies import get_current_user
from core.config import settings
from models.post import PostCreate, PostUpdate, CommentCreate, ShareCreate, TREND_TAGS

router = APIRouter(tags=["Posts"])

# Comment Report model for Apple Guideline 1.2 compliance
class CommentReportCreate(BaseModel):
    reason: str  # spam, harassment, inappropriate

# Configure Cloudinary
CLOUDINARY_FOLDER = getattr(settings, 'CLOUDINARY_ASSET_FOLDER', 'styleflow_uploads')
cloudinary.config(
    cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
    api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
    api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', '')
)

# ==================== IMAGE UPLOAD ====================

@router.post("/posts/upload-image")
async def upload_post_image(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Upload a single image for a post and return the URL"""
    try:
        image_data = data.get("image")
        if not image_data:
            raise HTTPException(status_code=400, detail="Image data is required")
        
        user_id = str(current_user["_id"])
        
        # Check if Cloudinary is configured
        cloudinary_configured = bool(getattr(settings, 'CLOUDINARY_API_KEY', ''))
        
        if cloudinary_configured:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_data,
                folder=f"{CLOUDINARY_FOLDER}/posts/{user_id}",
                resource_type="image",
                transformation=[
                    {"width": 1080, "height": 1080, "crop": "limit"},
                    {"quality": "auto:good"},
                    {"fetch_format": "auto"}
                ]
            )
            image_url = upload_result.get("secure_url")
        else:
            # If no Cloudinary, accept the base64 directly (dev mode)
            image_url = image_data
        
        return {"url": image_url}
    except Exception as e:
        logging.error(f"Post image upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

# ==================== POSTS & ENGAGEMENT SYSTEM ====================

@router.post("/posts")
async def create_post(post_data: PostCreate, current_user: dict = Depends(get_current_user)):
    """Create a new post with up to 5 images"""
    user_id = str(current_user["_id"])
    
    # Validate images
    if not post_data.images or len(post_data.images) == 0:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(post_data.images) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed per post")
    
    # Validate tags
    valid_tags = [tag for tag in (post_data.tags or []) if tag.lower().replace("#", "") in TREND_TAGS]
    
    post_doc = {
        "user_id": user_id,
        "images": post_data.images,
        "caption": post_data.caption,
        "tags": valid_tags,
        "likes_count": 0,
        "comments_count": 0,
        "saves_count": 0,
        "shares_count": 0,
        "is_shared": False,
        "original_post_id": None,
        "shared_by_id": None,
        "share_caption": None,
        "created_at": datetime.utcnow()
    }
    
    result = await db.posts.insert_one(post_doc)
    
    return {
        "id": str(result.inserted_id),
        "message": "Post created successfully"
    }

@router.get("/posts")
async def get_posts(
    feed: str = "trending",
    tag: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get posts feed with different filters"""
    current_user_id = str(current_user["_id"])
    
    # Get blocked users to filter out
    blocked_by_me = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    blocked_me = await db.blocks.find({"blocked_id": current_user_id}).to_list(1000)
    blocked_ids = [b["blocked_id"] for b in blocked_by_me] + [b["blocker_id"] for b in blocked_me]
    
    # Base query excluding blocked users
    query = {"user_id": {"$nin": blocked_ids}}
    
    if tag:
        query["tags"] = tag.lower().replace("#", "")
    
    if feed == "following":
        follows = await db.follows.find({"follower_id": current_user_id}).to_list(1000)
        following_ids = [f["following_id"] for f in follows]
        following_ids.append(current_user_id)
        query["user_id"] = {"$in": following_ids, "$nin": blocked_ids}
    
    # Get posts based on feed type
    if feed == "trending":
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "hours_since_posted": {
                    "$divide": [
                        {"$subtract": [datetime.utcnow(), "$created_at"]},
                        3600000
                    ]
                },
                "engagement_score": {
                    "$add": [
                        {"$multiply": ["$likes_count", 2]},
                        {"$multiply": ["$comments_count", 3]},
                        {"$multiply": ["$saves_count", 1.5]},
                        {"$multiply": ["$shares_count", 2.5]}
                    ]
                }
            }},
            {"$addFields": {
                "trending_score": {
                    "$cond": [
                        {"$eq": ["$hours_since_posted", 0]},
                        "$engagement_score",
                        {"$divide": ["$engagement_score", {"$add": ["$hours_since_posted", 1]}]}
                    ]
                }
            }},
            {"$match": {"hours_since_posted": {"$lt": 168}}},
            {"$sort": {"trending_score": -1, "created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        posts = await db.posts.aggregate(pipeline).to_list(limit)
    elif feed == "new":
        posts = await db.posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    else:
        posts = await db.posts.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Enrich posts with user info and interaction status
    result = []
    for post in posts:
        author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
        
        user_liked = await db.post_likes.find_one({
            "post_id": str(post["_id"]),
            "user_id": current_user_id
        }) is not None
        
        user_saved = await db.post_saves.find_one({
            "post_id": str(post["_id"]),
            "user_id": current_user_id
        }) is not None
        
        # Handle shared posts
        original_author = None
        if post.get("is_shared") and post.get("original_post_id"):
            original_post = await db.posts.find_one({"_id": ObjectId(post["original_post_id"])})
            if original_post:
                orig_user = await db.users.find_one({"_id": ObjectId(original_post["user_id"])})
                if orig_user:
                    original_author = {
                        "id": str(orig_user["_id"]),
                        "full_name": orig_user.get("full_name"),
                        "profile_photo": orig_user.get("profile_photo")
                    }
        
        shared_by = None
        if post.get("shared_by_id"):
            sharer = await db.users.find_one({"_id": ObjectId(post["shared_by_id"])})
            if sharer:
                shared_by = {
                    "id": str(sharer["_id"]),
                    "full_name": sharer.get("full_name"),
                    "profile_photo": sharer.get("profile_photo")
                }
        
        result.append({
            "id": str(post["_id"]),
            "author": {
                "id": str(author["_id"]) if author else None,
                "full_name": author.get("full_name") if author else "Unknown",
                "profile_photo": author.get("profile_photo") if author else None,
                "business_name": author.get("business_name") if author else None
            },
            "images": post.get("images", []),
            "caption": post.get("caption"),
            "tags": post.get("tags", []),
            "likes_count": post.get("likes_count", 0),
            "comments_count": post.get("comments_count", 0),
            "saves_count": post.get("saves_count", 0),
            "shares_count": post.get("shares_count", 0),
            "user_liked": user_liked,
            "user_saved": user_saved,
            "is_shared": post.get("is_shared", False),
            "original_author": original_author,
            "shared_by": shared_by,
            "share_caption": post.get("share_caption"),
            "created_at": post.get("created_at").isoformat() if post.get("created_at") else None
        })
    
    return result

@router.get("/posts/trending-tags")
async def get_trending_tags(current_user: dict = Depends(get_current_user)):
    """Get currently trending tags based on recent post engagement"""
    pipeline = [
        {"$match": {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}},
        {"$unwind": "$tags"},
        {"$group": {
            "_id": "$tags",
            "post_count": {"$sum": 1},
            "total_engagement": {
                "$sum": {
                    "$add": [
                        {"$multiply": ["$likes_count", 2]},
                        {"$multiply": ["$comments_count", 3]},
                        "$saves_count"
                    ]
                }
            }
        }},
        {"$addFields": {
            "score": {"$multiply": ["$post_count", {"$add": ["$total_engagement", 1]}]}
        }},
        {"$sort": {"score": -1}},
        {"$limit": 15}
    ]
    
    trending = await db.posts.aggregate(pipeline).to_list(15)
    result = [{"tag": t["_id"], "post_count": t["post_count"], "score": t["score"]} for t in trending]
    
    if len(result) < 10:
        for tag in TREND_TAGS[:10 - len(result)]:
            if not any(r["tag"] == tag for r in result):
                result.append({"tag": tag, "post_count": 0, "score": 0})
    
    return result

@router.get("/posts/saved")
async def get_saved_posts(skip: int = 0, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get user's saved/bookmarked posts"""
    user_id = str(current_user["_id"])
    
    saved = await db.post_saves.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    post_ids = [s["post_id"] for s in saved]
    
    result = []
    for pid in post_ids:
        post = await db.posts.find_one({"_id": ObjectId(pid)})
        if post:
            author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
            result.append({
                "id": str(post["_id"]),
                "author": {
                    "id": str(author["_id"]) if author else None,
                    "full_name": author.get("full_name") if author else "Unknown",
                    "profile_photo": author.get("profile_photo") if author else None
                },
                "images": post.get("images", []),
                "caption": post.get("caption"),
                "likes_count": post.get("likes_count", 0),
                "comments_count": post.get("comments_count", 0),
                "created_at": post.get("created_at").isoformat() if post.get("created_at") else None
            })
    
    return result

@router.get("/posts/{post_id}")
async def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Get single post with full details"""
    current_user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
    
    user_liked = await db.post_likes.find_one({
        "post_id": post_id,
        "user_id": current_user_id
    }) is not None
    
    user_saved = await db.post_saves.find_one({
        "post_id": post_id,
        "user_id": current_user_id
    }) is not None
    
    original_author = None
    original_post_data = None
    if post.get("is_shared") and post.get("original_post_id"):
        original_post = await db.posts.find_one({"_id": ObjectId(post["original_post_id"])})
        if original_post:
            orig_user = await db.users.find_one({"_id": ObjectId(original_post["user_id"])})
            if orig_user:
                original_author = {
                    "id": str(orig_user["_id"]),
                    "full_name": orig_user.get("full_name"),
                    "profile_photo": orig_user.get("profile_photo")
                }
            original_post_data = {
                "id": str(original_post["_id"]),
                "images": original_post.get("images", []),
                "caption": original_post.get("caption"),
                "tags": original_post.get("tags", [])
            }
    
    return {
        "id": str(post["_id"]),
        "author": {
            "id": str(author["_id"]) if author else None,
            "full_name": author.get("full_name") if author else "Unknown",
            "profile_photo": author.get("profile_photo") if author else None,
            "business_name": author.get("business_name") if author else None
        },
        "images": post.get("images", []),
        "caption": post.get("caption"),
        "tags": post.get("tags", []),
        "likes_count": post.get("likes_count", 0),
        "comments_count": post.get("comments_count", 0),
        "saves_count": post.get("saves_count", 0),
        "shares_count": post.get("shares_count", 0),
        "user_liked": user_liked,
        "user_saved": user_saved,
        "is_shared": post.get("is_shared", False),
        "original_author": original_author,
        "original_post": original_post_data,
        "share_caption": post.get("share_caption"),
        "created_at": post.get("created_at").isoformat() if post.get("created_at") else None
    }

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """Delete own post"""
    user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["user_id"] != user_id and not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    await db.post_likes.delete_many({"post_id": post_id})
    await db.post_saves.delete_many({"post_id": post_id})
    await db.post_comments.delete_many({"post_id": post_id})
    await db.posts.delete_one({"_id": ObjectId(post_id)})
    
    return {"message": "Post deleted successfully"}

@router.get("/posts/user/{user_id}")
async def get_user_posts(user_id: str, skip: int = 0, limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get posts by a specific user"""
    current_user_id = str(current_user["_id"])
    
    blocked = await db.blocks.find_one({
        "$or": [
            {"blocker_id": current_user_id, "blocked_id": user_id},
            {"blocker_id": user_id, "blocked_id": current_user_id}
        ]
    })
    if blocked:
        raise HTTPException(status_code=403, detail="Cannot view this user's posts")
    
    posts = await db.posts.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for post in posts:
        author = await db.users.find_one({"_id": ObjectId(post["user_id"])})
        
        user_liked = await db.post_likes.find_one({
            "post_id": str(post["_id"]),
            "user_id": current_user_id
        }) is not None
        
        user_saved = await db.post_saves.find_one({
            "post_id": str(post["_id"]),
            "user_id": current_user_id
        }) is not None
        
        result.append({
            "id": str(post["_id"]),
            "author": {
                "id": str(author["_id"]) if author else None,
                "full_name": author.get("full_name") if author else "Unknown",
                "profile_photo": author.get("profile_photo") if author else None
            },
            "images": post.get("images", []),
            "caption": post.get("caption"),
            "tags": post.get("tags", []),
            "likes_count": post.get("likes_count", 0),
            "comments_count": post.get("comments_count", 0),
            "saves_count": post.get("saves_count", 0),
            "user_liked": user_liked,
            "user_saved": user_saved,
            "is_shared": post.get("is_shared", False),
            "created_at": post.get("created_at").isoformat() if post.get("created_at") else None
        })
    
    return result

# ==================== POST INTERACTIONS ====================

@router.post("/posts/{post_id}/like")
async def toggle_like(post_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle like on a post"""
    user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    existing_like = await db.post_likes.find_one({
        "post_id": post_id,
        "user_id": user_id
    })
    
    if existing_like:
        await db.post_likes.delete_one({"_id": existing_like["_id"]})
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"likes_count": -1}}
        )
        return {"liked": False, "likes_count": max(0, post.get("likes_count", 1) - 1)}
    else:
        await db.post_likes.insert_one({
            "post_id": post_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"likes_count": 1}}
        )
        return {"liked": True, "likes_count": post.get("likes_count", 0) + 1}

@router.post("/posts/{post_id}/save")
async def toggle_save(post_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle save/bookmark on a post"""
    user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    existing_save = await db.post_saves.find_one({
        "post_id": post_id,
        "user_id": user_id
    })
    
    if existing_save:
        await db.post_saves.delete_one({"_id": existing_save["_id"]})
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"saves_count": -1}}
        )
        return {"saved": False, "saves_count": max(0, post.get("saves_count", 1) - 1)}
    else:
        await db.post_saves.insert_one({
            "post_id": post_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        await db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"saves_count": 1}}
        )
        return {"saved": True, "saves_count": post.get("saves_count", 0) + 1}

# ==================== COMMENTS ====================

@router.post("/posts/{post_id}/comments")
async def add_comment(post_id: str, comment_data: CommentCreate, current_user: dict = Depends(get_current_user)):
    """Add a comment to a post"""
    user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if not comment_data.text.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    comment_doc = {
        "post_id": post_id,
        "user_id": user_id,
        "text": comment_data.text.strip(),
        "likes_count": 0,
        "is_pinned": False,
        "created_at": datetime.utcnow()
    }
    
    result = await db.post_comments.insert_one(comment_doc)
    
    await db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$inc": {"comments_count": 1}}
    )
    
    return {
        "id": str(result.inserted_id),
        "text": comment_data.text.strip(),
        "user": {
            "id": user_id,
            "full_name": current_user.get("full_name"),
            "profile_photo": current_user.get("profile_photo")
        },
        "likes_count": 0,
        "is_pinned": False,
        "created_at": datetime.utcnow().isoformat()
    }

@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str, skip: int = 0, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get comments for a post, pinned comment first"""
    user_id = str(current_user["_id"])
    
    pinned = await db.post_comments.find_one({"post_id": post_id, "is_pinned": True})
    
    comments = await db.post_comments.find({
        "post_id": post_id,
        "is_pinned": {"$ne": True}
    }).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    if pinned:
        comments.insert(0, pinned)
    
    result = []
    for comment in comments:
        commenter = await db.users.find_one({"_id": ObjectId(comment["user_id"])})
        
        user_liked = await db.comment_likes.find_one({
            "comment_id": str(comment["_id"]),
            "user_id": user_id
        }) is not None
        
        result.append({
            "id": str(comment["_id"]),
            "text": comment.get("text"),
            "user": {
                "id": str(commenter["_id"]) if commenter else None,
                "full_name": commenter.get("full_name") if commenter else "Unknown",
                "profile_photo": commenter.get("profile_photo") if commenter else None
            },
            "likes_count": comment.get("likes_count", 0),
            "user_liked": user_liked,
            "is_pinned": comment.get("is_pinned", False),
            "created_at": comment.get("created_at").isoformat() if comment.get("created_at") else None
        })
    
    return result

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(comment_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle like on a comment"""
    user_id = str(current_user["_id"])
    
    comment = await db.post_comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    existing_like = await db.comment_likes.find_one({
        "comment_id": comment_id,
        "user_id": user_id
    })
    
    if existing_like:
        await db.comment_likes.delete_one({"_id": existing_like["_id"]})
        await db.post_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {"likes_count": -1}}
        )
        return {"liked": False, "likes_count": max(0, comment.get("likes_count", 1) - 1)}
    else:
        await db.comment_likes.insert_one({
            "comment_id": comment_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        await db.post_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$inc": {"likes_count": 1}}
        )
        return {"liked": True, "likes_count": comment.get("likes_count", 0) + 1}

@router.post("/posts/{post_id}/comments/{comment_id}/pin")
async def pin_comment(post_id: str, comment_id: str, current_user: dict = Depends(get_current_user)):
    """Pin/unpin a comment (only post creator can do this)"""
    user_id = str(current_user["_id"])
    
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only post creator can pin comments")
    
    comment = await db.post_comments.find_one({"_id": ObjectId(comment_id), "post_id": post_id})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    await db.post_comments.update_many(
        {"post_id": post_id},
        {"$set": {"is_pinned": False}}
    )
    
    new_pin_status = not comment.get("is_pinned", False)
    if new_pin_status:
        await db.post_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"is_pinned": True}}
        )
    
    return {"is_pinned": new_pin_status}

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a comment (by comment author or post author)"""
    user_id = str(current_user["_id"])
    
    comment = await db.post_comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    post = await db.posts.find_one({"_id": ObjectId(comment["post_id"])})
    
    if comment["user_id"] != user_id and (not post or post["user_id"] != user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    await db.comment_likes.delete_many({"comment_id": comment_id})
    await db.post_comments.delete_one({"_id": ObjectId(comment_id)})
    
    if post:
        await db.posts.update_one(
            {"_id": post["_id"]},
            {"$inc": {"comments_count": -1}}
        )
    
    return {"message": "Comment deleted"}

# ==================== COMMENT REPORTING (Apple Guideline 1.2) ====================

@router.post("/comments/{comment_id}/report")
async def report_comment(
    comment_id: str,
    report_data: CommentReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """Report a comment for moderation (Apple Guideline 1.2 UGC compliance)"""
    user_id = str(current_user["_id"])
    
    # Validate reason
    valid_reasons = ["spam", "harassment", "inappropriate"]
    if report_data.reason not in valid_reasons:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid reason. Must be one of: {', '.join(valid_reasons)}"
        )
    
    # Validate ObjectId format
    try:
        comment_oid = ObjectId(comment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comment ID format")
    
    # Get the comment
    comment = await db.post_comments.find_one({"_id": comment_oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Cannot report own comment
    if comment["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot report your own comment")
    
    # Check if already reported by this user
    existing_report = await db.comment_reports.find_one({
        "comment_id": comment_id,
        "reporter_id": user_id
    })
    if existing_report:
        raise HTTPException(status_code=400, detail="You have already reported this comment")
    
    # Create the report
    report = {
        "comment_id": comment_id,
        "post_id": comment.get("post_id"),
        "reported_user_id": comment["user_id"],
        "reporter_id": user_id,
        "reason": report_data.reason,
        "comment_text": comment.get("text", "")[:500],  # Store snippet for moderation
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.comment_reports.insert_one(report)
    
    # Update comment report count
    await db.post_comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$inc": {"report_count": 1}}
    )
    
    # Auto-hide comment if 3+ reports
    comment_report_count = await db.comment_reports.count_documents({"comment_id": comment_id})
    if comment_report_count >= 3:
        await db.post_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"is_hidden": True, "hidden_reason": "multiple_reports"}}
        )
    
    return {
        "message": "Report submitted successfully",
        "report_count": comment_report_count
    }

# ==================== SHARING ====================

@router.post("/posts/{post_id}/share")
async def share_post(post_id: str, share_data: ShareCreate, current_user: dict = Depends(get_current_user)):
    """Share a post (creates a new post in feed showing original + sharer)"""
    user_id = str(current_user["_id"])
    
    original_post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not original_post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if original_post["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot share your own post")
    
    actual_original_id = original_post.get("original_post_id") or post_id
    
    existing_share = await db.posts.find_one({
        "shared_by_id": user_id,
        "original_post_id": actual_original_id
    })
    if existing_share:
        raise HTTPException(status_code=400, detail="You have already shared this post")
    
    if original_post.get("original_post_id"):
        actual_original = await db.posts.find_one({"_id": ObjectId(original_post["original_post_id"])})
        if actual_original:
            original_post = actual_original
            actual_original_id = str(actual_original["_id"])
    
    shared_post_doc = {
        "user_id": original_post["user_id"],
        "images": original_post.get("images", []),
        "caption": original_post.get("caption"),
        "tags": original_post.get("tags", []),
        "likes_count": 0,
        "comments_count": 0,
        "saves_count": 0,
        "shares_count": 0,
        "is_shared": True,
        "original_post_id": actual_original_id,
        "shared_by_id": user_id,
        "share_caption": share_data.caption,
        "created_at": datetime.utcnow()
    }
    
    result = await db.posts.insert_one(shared_post_doc)
    
    await db.posts.update_one(
        {"_id": ObjectId(actual_original_id)},
        {"$inc": {"shares_count": 1}}
    )
    
    return {
        "id": str(result.inserted_id),
        "message": "Post shared successfully"
    }

# ==================== CREATOR PROFILES ====================

@router.get("/creators/{user_id}/profile")
async def get_creator_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get enhanced creator profile with portfolio sections and stats"""
    current_user_id = str(current_user["_id"])
    
    blocked = await db.blocks.find_one({
        "$or": [
            {"blocker_id": current_user_id, "blocked_id": user_id},
            {"blocker_id": user_id, "blocked_id": current_user_id}
        ]
    })
    if blocked:
        raise HTTPException(status_code=403, detail="Cannot view this profile")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    is_following = await db.follows.find_one({
        "follower_id": current_user_id,
        "following_id": user_id
    }) is not None
    
    followers_count = await db.follows.count_documents({"following_id": user_id})
    following_count = await db.follows.count_documents({"follower_id": user_id})
    posts_count = await db.posts.count_documents({"user_id": user_id, "is_shared": {"$ne": True}})
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_likes": {"$sum": "$likes_count"},
            "total_comments": {"$sum": "$comments_count"},
            "total_saves": {"$sum": "$saves_count"}
        }}
    ]
    engagement_stats = await db.posts.aggregate(pipeline).to_list(1)
    engagement = engagement_stats[0] if engagement_stats else {"total_likes": 0, "total_comments": 0, "total_saves": 0}
    
    tag_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    signature_styles = await db.posts.aggregate(tag_pipeline).to_list(5)
    
    portfolio_sections = {}
    posts = await db.posts.find({"user_id": user_id, "is_shared": {"$ne": True}}).sort("created_at", -1).limit(50).to_list(50)
    
    for post in posts:
        for tag in post.get("tags", []):
            if tag not in portfolio_sections:
                portfolio_sections[tag] = []
            if len(portfolio_sections[tag]) < 6:
                portfolio_sections[tag].append({
                    "id": str(post["_id"]),
                    "cover_image": post.get("images", [None])[0],
                    "likes_count": post.get("likes_count", 0)
                })
    
    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "business_name": user.get("business_name"),
        "bio": user.get("bio"),
        "profile_photo": user.get("profile_photo"),
        "city": user.get("city"),
        "specialties": user.get("specialties"),
        "instagram_handle": user.get("instagram_handle"),
        "tiktok_handle": user.get("tiktok_handle"),
        "website_url": user.get("website_url"),
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "engagement": {
            "total_likes": engagement.get("total_likes", 0),
            "total_comments": engagement.get("total_comments", 0),
            "total_saves": engagement.get("total_saves", 0)
        },
        "signature_styles": [{"tag": s["_id"], "count": s["count"]} for s in signature_styles],
        "portfolio_sections": portfolio_sections
    }

@router.put("/profile/signature-styles")
async def update_signature_styles(styles: List[str], current_user: dict = Depends(get_current_user)):
    """Update user's signature styles"""
    valid_styles = [s for s in styles if s.lower().replace("#", "") in TREND_TAGS][:5]
    
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"signature_styles": valid_styles}}
    )
    
    return {"signature_styles": valid_styles}

# ==================== POST REPORTING WITH STRIKE INTEGRATION ====================

REPORT_REASONS = [
    "harassment", "inappropriate", "spam", "hate_speech", 
    "sexual_content", "illegal", "impersonation", "other"
]

@router.post("/posts/{post_id}/report")
async def report_post(
    post_id: str, 
    report_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Report a post for rule violation.
    Triggers the automated Strike Engine for threshold-based enforcement.
    """
    from core.strike_engine import StrikeEngine
    
    reason = report_data.get("reason")
    details = report_data.get("details")
    
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required")
    
    reporter_id = str(current_user["_id"])
    
    # Validate post exists
    post = await db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    reported_user_id = post["user_id"]
    
    # Can't report your own post
    if reported_user_id == reporter_id:
        raise HTTPException(status_code=400, detail="Cannot report your own post")
    
    # Validate reason
    if reason.lower() not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail=f"Invalid reason. Must be one of: {REPORT_REASONS}")
    
    # Check if already reported by this user
    existing_report = await db.reports.find_one({
        "reporter_id": reporter_id,
        "post_id": post_id
    })
    if existing_report:
        raise HTTPException(status_code=400, detail="You have already reported this post")
    
    # Create the report
    report_doc = {
        "reporter_id": reporter_id,
        "reported_user_id": reported_user_id,
        "post_id": post_id,
        "content_type": "post",
        "reason": reason.lower(),
        "details": details,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.reports.insert_one(report_doc)
    
    # Increment report count on the user
    await db.users.update_one(
        {"_id": ObjectId(reported_user_id)},
        {"$inc": {"report_count": 1}}
    )
    
    # Check report threshold and trigger Strike Engine if needed
    user = await db.users.find_one({"_id": ObjectId(reported_user_id)})
    report_count = user.get("report_count", 0)
    
    # Auto-action thresholds: 3 reports = warning, 6 = strike escalation
    if report_count >= 3:
        # Get all pending reports for this user
        pending_reports = await db.reports.find({
            "reported_user_id": reported_user_id,
            "status": "pending"
        }).to_list(100)
        
        report_ids = [str(r["_id"]) for r in pending_reports]
        
        # Trigger Strike Engine
        strike_engine = StrikeEngine(db)
        result = await strike_engine.process_violation(
            user_id=reported_user_id,
            violation_type=reason.lower(),
            report_ids=report_ids,
            details=f"Auto-triggered: {report_count} reports received. Latest: {details or 'No details provided'}"
        )
        
        return {
            "message": "Report submitted. Automated enforcement triggered.",
            "action_taken": result.get("action_label"),
            "strike_number": result.get("strike_number")
        }
    
    return {
        "message": "Report submitted successfully",
        "report_count": report_count,
        "action_taken": None
    }

@router.get("/posts/{post_id}/report-status")
async def get_post_report_status(post_id: str, current_user: dict = Depends(get_current_user)):
    """Check if a post has been reported by the current user"""
    reporter_id = str(current_user["_id"])
    
    existing_report = await db.reports.find_one({
        "reporter_id": reporter_id,
        "post_id": post_id
    })
    
    return {
        "reported": existing_report is not None,
        "report_id": str(existing_report["_id"]) if existing_report else None
    }

