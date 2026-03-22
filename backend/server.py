from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
import jwt
import bcrypt
import json
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ['JWT_SECRET_KEY']
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']
JWT_EXPIRATION = int(os.environ['JWT_EXPIRATION_MINUTES'])

# OpenAI Configuration
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# ==================== WEBSOCKET CONNECTION MANAGER ====================

class AdminConnectionManager:
    """Manages WebSocket connections for admin real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.admin_users: Set[str] = set()
    
    async def connect(self, websocket: WebSocket, admin_id: str):
        await websocket.accept()
        self.active_connections[admin_id] = websocket
        self.admin_users.add(admin_id)
        logging.info(f"Admin {admin_id} connected to moderation websocket")
    
    def disconnect(self, admin_id: str):
        if admin_id in self.active_connections:
            del self.active_connections[admin_id]
        if admin_id in self.admin_users:
            self.admin_users.discard(admin_id)
        logging.info(f"Admin {admin_id} disconnected from moderation websocket")
    
    async def broadcast_to_admins(self, message: dict):
        """Send message to all connected admins"""
        disconnected = []
        for admin_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.error(f"Failed to send to admin {admin_id}: {e}")
                disconnected.append(admin_id)
        
        # Clean up disconnected
        for admin_id in disconnected:
            self.disconnect(admin_id)
    
    async def send_to_admin(self, admin_id: str, message: dict):
        """Send message to specific admin"""
        if admin_id in self.active_connections:
            try:
                await self.active_connections[admin_id].send_json(message)
            except Exception as e:
                logging.error(f"Failed to send to admin {admin_id}: {e}")
                self.disconnect(admin_id)

# Global connection manager instance
admin_manager = AdminConnectionManager()

# ==================== MODELS ====================

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
    profile_visibility: str = "public"  # public, private
    created_at: datetime

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    new_password: str

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    hair_goals: Optional[str] = None
    is_vip: bool = False
    last_visit: Optional[datetime] = None

class ClientResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    notes: Optional[str] = None
    preferences: Optional[str] = None
    hair_goals: Optional[str] = None
    is_vip: bool = False
    visit_count: int = 0
    last_visit: Optional[datetime] = None
    created_at: datetime

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

class GalleryCreate(BaseModel):
    client_id: str
    before_photo: Optional[str] = None
    after_photo: Optional[str] = None
    notes: Optional[str] = None
    date_taken: Optional[datetime] = None

class GalleryResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    before_photo: Optional[str] = None
    after_photo: Optional[str] = None
    notes: Optional[str] = None
    date_taken: datetime

class AppointmentCreate(BaseModel):
    client_id: str
    appointment_date: datetime
    service: str
    duration_minutes: Optional[int] = 60
    notes: Optional[str] = None
    status: str = "scheduled"  # scheduled, completed, cancelled, no_show

class AppointmentResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    client_name: Optional[str] = None
    appointment_date: datetime
    service: str
    duration_minutes: int
    notes: Optional[str] = None
    status: str

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

class AIMessageRequest(BaseModel):
    message: str
    context: Optional[str] = None

class AIMessageResponse(BaseModel):
    response: str

# ==================== MODERATION MODELS ====================

class ReportCreate(BaseModel):
    reported_user_id: str
    content_type: str  # "profile", "portfolio", "gallery"
    content_id: Optional[str] = None
    reason: str  # "harassment", "inappropriate", "spam", "hate_speech", "sexual_content", "illegal", "other"
    details: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: str
    content_type: str
    content_id: Optional[str] = None
    reason: str
    details: Optional[str] = None
    status: str  # "pending", "reviewed", "dismissed", "actioned"
    created_at: datetime

class BlockCreate(BaseModel):
    blocked_user_id: str

class ModerationAction(BaseModel):
    action: str  # "dismiss", "warn", "remove_content", "restrict", "suspend", "ban"
    reason: Optional[str] = None
    duration_days: Optional[int] = None  # For suspensions

REPORT_REASONS = [
    "harassment",
    "inappropriate", 
    "spam",
    "hate_speech",
    "sexual_content",
    "illegal",
    "impersonation",
    "other"
]

MODERATION_ACTIONS = ["dismiss", "warn", "remove_content", "restrict", "suspend", "ban"]

# ==================== APPEAL MODELS ====================

class AppealCreate(BaseModel):
    reason: str  # Required appeal reason
    additional_details: Optional[str] = None

class AppealAction(BaseModel):
    action: str  # "approve", "deny"
    admin_notes: Optional[str] = None

APPEAL_STATUSES = ["pending", "under_review", "approved", "denied"]

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    email = decode_access_token(token)
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/signup")
async def signup(user_data: UserSignup):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_doc = {
        "email": user_data.email,
        "password": hashed_password,
        "full_name": user_data.full_name,
        "business_name": user_data.business_name,
        "bio": None,
        "specialties": None,
        "salon_info": None,
        "salon_name": None,
        "city": None,
        "profile_photo": None,
        "instagram_handle": None,
        "tiktok_handle": None,
        "website_url": None,
        "profile_visibility": "public",
        "created_at": datetime.utcnow(),
        "subscription_status": "free"
    }
    
    result = await db.users.insert_one(user_doc)
    
    # Create token
    token = create_access_token(user_data.email)
    
    return {
        "token": token,
        "user": {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "business_name": user_data.business_name
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(credentials.email)
    
    return {
        "token": token,
        "user": {
            "email": user["email"],
            "full_name": user["full_name"],
            "business_name": user.get("business_name")
        }
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(request: PasswordReset):
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists
        return {"message": "If email exists, reset instructions sent"}
    
    # In production, send email with reset link
    # For now, just return success
    return {"message": "If email exists, reset instructions sent"}

@api_router.post("/auth/reset-password")
async def reset_password(request: PasswordResetConfirm):
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = hash_password(request.new_password)
    await db.users.update_one(
        {"email": request.email},
        {"$set": {"password": hashed_password}}
    )
    
    return {"message": "Password reset successful"}

@api_router.delete("/auth/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Delete all user data
    await db.users.delete_one({"_id": current_user["_id"]})
    await db.clients.delete_many({"user_id": user_id})
    await db.formulas.delete_many({"user_id": user_id})
    await db.gallery.delete_many({"user_id": user_id})
    await db.appointments.delete_many({"user_id": user_id})
    await db.income.delete_many({"user_id": user_id})
    await db.retail.delete_many({"user_id": user_id})
    await db.no_shows.delete_many({"user_id": user_id})
    
    return {"message": "Account deleted successfully"}

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "business_name": current_user.get("business_name"),
        "bio": current_user.get("bio"),
        "specialties": current_user.get("specialties"),
        "salon_name": current_user.get("salon_name"),
        "city": current_user.get("city"),
        "profile_photo": current_user.get("profile_photo"),
        "instagram_handle": current_user.get("instagram_handle"),
        "tiktok_handle": current_user.get("tiktok_handle"),
        "website_url": current_user.get("website_url"),
        "profile_visibility": current_user.get("profile_visibility", "public"),
        "subscription_status": current_user.get("subscription_status", "free"),
        "is_admin": current_user.get("is_admin", False),
        # Moderation fields
        "moderation_status": current_user.get("moderation_status", "good_standing"),
        "warnings_count": current_user.get("warnings_count", 0),
        "last_warning_reason": current_user.get("last_warning_reason"),
        "suspended_until": current_user.get("suspended_until").isoformat() if current_user.get("suspended_until") else None,
        "suspension_reason": current_user.get("suspension_reason"),
        "ban_reason": current_user.get("ban_reason"),
    }

@api_router.put("/auth/profile")
async def update_profile(profile_data: dict, current_user: dict = Depends(get_current_user)):
    update_fields = {}
    allowed_fields = ["full_name", "business_name", "bio", "specialties", "salon_name", 
                     "city", "profile_photo", "instagram_handle", "tiktok_handle", 
                     "website_url", "profile_visibility"]
    
    for field in allowed_fields:
        if field in profile_data:
            update_fields[field] = profile_data[field]
    
    if update_fields:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_fields}
        )
    
    return {"message": "Profile updated successfully"}

# ==================== USER DISCOVERY & COMMUNITY ====================

@api_router.get("/users/discover")
async def discover_users(search: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    # Get list of blocked users (both directions)
    blocked_by_me = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    blocked_me = await db.blocks.find({"blocked_id": current_user_id}).to_list(1000)
    
    blocked_ids = [b["blocked_id"] for b in blocked_by_me] + [b["blocker_id"] for b in blocked_me]
    blocked_object_ids = [ObjectId(bid) for bid in blocked_ids if bid]
    
    query = {
        "profile_visibility": "public",
        "moderation_status": {"$nin": ["banned", "suspended"]},  # Exclude banned/suspended users
        "_id": {"$nin": blocked_object_ids + [current_user["_id"]]}  # Exclude blocked and self
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

@api_router.get("/users/{user_id}/profile")
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

@api_router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if target user exists
    from bson import ObjectId
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

@api_router.delete("/users/{user_id}/follow")
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

# ==================== CONNECTION MANAGEMENT ====================

@api_router.post("/connections/{user_id}")
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

@api_router.delete("/connections/{user_id}")
async def remove_connection(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    result = await db.connections.delete_one({
        "user_id": current_user_id,
        "connected_user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return {"message": "Connection removed successfully"}

@api_router.get("/connections")
async def get_connections(current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    connections = await db.connections.find({"user_id": current_user_id}).to_list(1000)
    
    result = []
    from bson import ObjectId
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

@api_router.post("/block/{user_id}")
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

@api_router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    result = await db.blocks.delete_one({
        "blocker_id": current_user_id,
        "blocked_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not blocked")
    
    return {"message": "User unblocked successfully"}

@api_router.get("/blocked")
async def get_blocked_users(current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    blocks = await db.blocks.find({"blocker_id": current_user_id}).to_list(1000)
    
    result = []
    from bson import ObjectId
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

# ==================== REPORT SYSTEM ====================

@api_router.post("/report")
async def create_report(report_data: ReportCreate, current_user: dict = Depends(get_current_user)):
    current_user_id = str(current_user["_id"])
    
    if current_user_id == report_data.reported_user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    if report_data.reason not in REPORT_REASONS:
        raise HTTPException(status_code=400, detail="Invalid report reason")
    
    # Check if user already reported this content
    existing = await db.reports.find_one({
        "reporter_id": current_user_id,
        "reported_user_id": report_data.reported_user_id,
        "content_type": report_data.content_type,
        "content_id": report_data.content_id,
        "status": "pending"
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reported this content")
    
    report_doc = {
        "reporter_id": current_user_id,
        "reported_user_id": report_data.reported_user_id,
        "content_type": report_data.content_type,
        "content_id": report_data.content_id,
        "reason": report_data.reason,
        "details": report_data.details,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.reports.insert_one(report_doc)
    report_id = str(result.inserted_id)
    
    # Update report count on the reported user
    await db.users.update_one(
        {"_id": ObjectId(report_data.reported_user_id)},
        {"$inc": {"report_count": 1}}
    )
    
    # Get total pending report count for this user/content
    report_count = await db.reports.count_documents({
        "reported_user_id": report_data.reported_user_id,
        "status": "pending"
    })
    
    # Auto-flag if user has 3+ pending reports
    is_flagged = report_count >= 3
    if is_flagged:
        await db.users.update_one(
            {"_id": ObjectId(report_data.reported_user_id)},
            {"$set": {"flagged": True, "flagged_at": datetime.utcnow()}}
        )
    
    # Get reporter and reported user info for notification
    reporter = await db.users.find_one({"_id": current_user["_id"]})
    reported_user = await db.users.find_one({"_id": ObjectId(report_data.reported_user_id)})
    
    # Calculate priority (higher = more reports)
    priority = "high" if report_count >= 5 else "medium" if report_count >= 3 else "normal"
    
    # Broadcast real-time notification to all connected admins
    notification = {
        "type": "new_report",
        "report_id": report_id,
        "reporter": {
            "id": current_user_id,
            "name": reporter.get("full_name") if reporter else "Unknown"
        },
        "reported_user": {
            "id": report_data.reported_user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown",
            "email": reported_user.get("email") if reported_user else None
        },
        "content_type": report_data.content_type,
        "reason": report_data.reason,
        "details": report_data.details,
        "report_count": report_count,
        "priority": priority,
        "is_flagged": is_flagged,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Send to admins asynchronously
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {"message": "Report submitted successfully", "report_id": report_id}

@api_router.post("/report/{user_id}")
async def report_user(user_id: str, report_data: dict, current_user: dict = Depends(get_current_user)):
    """Legacy endpoint for backwards compatibility"""
    current_user_id = str(current_user["_id"])
    
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    report_doc = {
        "reporter_id": current_user_id,
        "reported_user_id": user_id,
        "content_type": "profile",
        "content_id": None,
        "reason": report_data.get("reason", "other"),
        "details": report_data.get("notes"),
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.reports.insert_one(report_doc)
    
    return {"message": "Report submitted successfully"}

# ==================== ADMIN MODERATION ENDPOINTS ====================

async def check_admin(current_user: dict):
    """Check if user is an admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")

# WebSocket endpoint for admin real-time notifications
@app.websocket("/ws/admin/moderation")
async def admin_moderation_websocket(websocket: WebSocket):
    """WebSocket connection for real-time admin moderation updates"""
    # Authenticate via query param token
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_email = payload.get("sub")
        user = await db.users.find_one({"email": user_email})
        
        if not user or not user.get("is_admin", False):
            await websocket.close(code=4003, reason="Admin access required")
            return
        
        admin_id = str(user["_id"])
        await admin_manager.connect(websocket, admin_id)
        
        # Send initial stats on connect
        pending_count = await db.reports.count_documents({"status": "pending"})
        flagged_count = await db.users.count_documents({"flagged": True})
        
        await websocket.send_json({
            "type": "connected",
            "admin_id": admin_id,
            "stats": {
                "pending_reports": pending_count,
                "flagged_users": flagged_count
            }
        })
        
        # Keep connection alive and listen for commands
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle ping/pong for keep-alive
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle request for queue refresh
                elif data.get("type") == "refresh_queue":
                    queue = await get_grouped_moderation_queue_data()
                    await websocket.send_json({
                        "type": "queue_update",
                        "data": queue
                    })
                    
            except WebSocketDisconnect:
                admin_manager.disconnect(admin_id)
                break
            except Exception as e:
                logging.error(f"WebSocket error: {e}")
                break
                
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4002, reason="Token expired")
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")

async def get_grouped_moderation_queue_data():
    """Get moderation queue grouped by user with priority sorting"""
    # Get all pending reports
    reports = await db.reports.find({"status": "pending"}).to_list(500)
    
    # Group by reported user
    user_reports: Dict[str, list] = {}
    for report in reports:
        user_id = report["reported_user_id"]
        if user_id not in user_reports:
            user_reports[user_id] = []
        user_reports[user_id].append(report)
    
    result = []
    for user_id, user_report_list in user_reports.items():
        # Get user info
        reported_user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        # Calculate priority based on report count
        report_count = len(user_report_list)
        priority = "critical" if report_count >= 10 else "high" if report_count >= 5 else "medium" if report_count >= 3 else "normal"
        
        # Get unique reasons
        reasons = list(set(r.get("reason") for r in user_report_list))
        
        # Get latest report date
        latest_report = max(user_report_list, key=lambda x: x.get("created_at", datetime.min))
        
        # Get all report details
        report_details = []
        for r in sorted(user_report_list, key=lambda x: x.get("created_at", datetime.min), reverse=True)[:10]:
            reporter = await db.users.find_one({"_id": ObjectId(r["reporter_id"])})
            report_details.append({
                "id": str(r["_id"]),
                "reporter_name": reporter.get("full_name") if reporter else "Unknown",
                "reason": r.get("reason"),
                "details": r.get("details"),
                "content_type": r.get("content_type"),
                "content_id": r.get("content_id"),
                "created_at": r.get("created_at").isoformat() if r.get("created_at") else None
            })
        
        result.append({
            "user_id": user_id,
            "user": {
                "id": user_id,
                "full_name": reported_user.get("full_name") if reported_user else "Unknown",
                "email": reported_user.get("email") if reported_user else None,
                "profile_photo": reported_user.get("profile_photo") if reported_user else None,
                "moderation_status": reported_user.get("moderation_status", "good_standing") if reported_user else None,
                "warnings_count": reported_user.get("warnings_count", 0) if reported_user else 0,
                "flagged": reported_user.get("flagged", False) if reported_user else False
            },
            "report_count": report_count,
            "priority": priority,
            "reasons": reasons,
            "reports": report_details,
            "latest_report_at": latest_report.get("created_at").isoformat() if latest_report.get("created_at") else None
        })
    
    # Sort by priority (critical > high > medium > normal) then by report count
    priority_order = {"critical": 0, "high": 1, "medium": 2, "normal": 3}
    result.sort(key=lambda x: (priority_order.get(x["priority"], 4), -x["report_count"]))
    
    return result

@api_router.get("/admin/moderation/queue")
async def get_moderation_queue(
    status: Optional[str] = "pending",
    grouped: bool = True,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    if grouped:
        return await get_grouped_moderation_queue_data()
    
    # Legacy non-grouped view
    query = {}
    if status:
        query["status"] = status
    
    reports = await db.reports.find(query).sort("created_at", -1).to_list(100)
    
    result = []
    for report in reports:
        reporter = await db.users.find_one({"_id": ObjectId(report["reporter_id"])})
        reported_user = await db.users.find_one({"_id": ObjectId(report["reported_user_id"])})
        
        report_count = await db.reports.count_documents({
            "reported_user_id": report["reported_user_id"],
            "status": "pending"
        })
        
        result.append({
            "id": str(report["_id"]),
            "reporter": {
                "id": str(reporter["_id"]) if reporter else None,
                "name": reporter.get("full_name") if reporter else "Unknown"
            },
            "reported_user": {
                "id": str(reported_user["_id"]) if reported_user else None,
                "name": reported_user.get("full_name") if reported_user else "Unknown",
                "email": reported_user.get("email") if reported_user else None,
                "moderation_status": reported_user.get("moderation_status", "good_standing") if reported_user else None,
                "warnings_count": reported_user.get("warnings_count", 0) if reported_user else 0
            },
            "content_type": report.get("content_type"),
            "content_id": report.get("content_id"),
            "reason": report.get("reason"),
            "details": report.get("details"),
            "report_count": report_count,
            "status": report.get("status"),
            "created_at": report.get("created_at")
        })
    
    return result

@api_router.get("/admin/moderation/stats")
async def get_moderation_stats(current_user: dict = Depends(get_current_user)):
    """Get real-time moderation statistics"""
    await check_admin(current_user)
    
    pending_reports = await db.reports.count_documents({"status": "pending"})
    flagged_users = await db.users.count_documents({"flagged": True})
    warned_users = await db.users.count_documents({"moderation_status": "warned"})
    restricted_users = await db.users.count_documents({"moderation_status": "restricted"})
    suspended_users = await db.users.count_documents({"moderation_status": "suspended"})
    banned_users = await db.users.count_documents({"moderation_status": "banned"})
    
    # Reports by reason
    pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    reason_breakdown = await db.reports.aggregate(pipeline).to_list(20)
    
    # High priority cases (5+ reports)
    high_priority_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$reported_user_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gte": 5}}}
    ]
    high_priority_count = len(await db.reports.aggregate(high_priority_pipeline).to_list(100))
    
    return {
        "pending_reports": pending_reports,
        "flagged_users": flagged_users,
        "warned_users": warned_users,
        "restricted_users": restricted_users,
        "suspended_users": suspended_users,
        "banned_users": banned_users,
        "high_priority_cases": high_priority_count,
        "reason_breakdown": {r["_id"]: r["count"] for r in reason_breakdown}
    }

@api_router.get("/admin/moderation/flagged")
async def get_flagged_users(current_user: dict = Depends(get_current_user)):
    await check_admin(current_user)
    
    # Get users who are flagged or have moderation issues
    flagged_users = await db.users.find({
        "$or": [
            {"flagged": True},
            {"moderation_status": {"$in": ["warned", "restricted", "suspended"]}}
        ]
    }).to_list(100)
    
    result = []
    for user in flagged_users:
        pending_reports = await db.reports.count_documents({
            "reported_user_id": str(user["_id"]),
            "status": "pending"
        })
        
        result.append({
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "moderation_status": user.get("moderation_status", "good_standing"),
            "warnings_count": user.get("warnings_count", 0),
            "flagged": user.get("flagged", False),
            "suspended_until": user.get("suspended_until"),
            "pending_reports": pending_reports
        })
    
    return result

@api_router.post("/admin/moderation/action/{report_id}")
async def take_moderation_action(
    report_id: str,
    action_data: ModerationAction,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    if action_data.action not in MODERATION_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    # Get the report
    report = await db.reports.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    reported_user_id = report["reported_user_id"]
    
    # Update report status
    new_status = "actioned" if action_data.action != "dismiss" else "dismissed"
    await db.reports.update_one(
        {"_id": ObjectId(report_id)},
        {
            "$set": {
                "status": new_status,
                "actioned_by": str(current_user["_id"]),
                "actioned_at": datetime.utcnow(),
                "action_taken": action_data.action,
                "action_reason": action_data.reason
            }
        }
    )
    
    # Apply action to user
    user_update = {}
    
    if action_data.action == "dismiss":
        # Just dismiss the report, no action on user
        # Clear flagged status if no more pending reports
        pending_count = await db.reports.count_documents({
            "reported_user_id": reported_user_id,
            "status": "pending"
        })
        if pending_count == 0:
            await db.users.update_one(
                {"_id": ObjectId(reported_user_id)},
                {"$set": {"flagged": False}}
            )
    
    elif action_data.action == "warn":
        user_update = {
            "$inc": {"warnings_count": 1},
            "$set": {
                "last_warning_at": datetime.utcnow(),
                "last_warning_reason": action_data.reason
            }
        }
        # Check if warnings should escalate to restriction
        user = await db.users.find_one({"_id": ObjectId(reported_user_id)})
        if user and user.get("warnings_count", 0) >= 2:
            user_update["$set"]["moderation_status"] = "restricted"
    
    elif action_data.action == "remove_content":
        # Remove the specific content
        if report.get("content_type") == "portfolio":
            await db.portfolio.delete_one({"_id": ObjectId(report.get("content_id"))})
        elif report.get("content_type") == "gallery":
            await db.gallery.delete_one({"_id": ObjectId(report.get("content_id"))})
        user_update = {"$inc": {"content_removed_count": 1}}
    
    elif action_data.action == "restrict":
        user_update = {
            "$set": {
                "moderation_status": "restricted",
                "restricted_at": datetime.utcnow(),
                "restriction_reason": action_data.reason
            }
        }
    
    elif action_data.action == "suspend":
        duration_days = action_data.duration_days or 7
        suspended_until = datetime.utcnow() + timedelta(days=duration_days)
        user_update = {
            "$set": {
                "moderation_status": "suspended",
                "suspended_at": datetime.utcnow(),
                "suspended_until": suspended_until,
                "suspension_reason": action_data.reason
            }
        }
    
    elif action_data.action == "ban":
        user_update = {
            "$set": {
                "moderation_status": "banned",
                "banned_at": datetime.utcnow(),
                "ban_reason": action_data.reason,
                "flagged": False
            }
        }
    
    if user_update:
        await db.users.update_one(
            {"_id": ObjectId(reported_user_id)},
            user_update
        )
    
    # Log the moderation action
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "report_id": report_id,
        "target_user_id": reported_user_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "created_at": datetime.utcnow()
    })
    
    # Broadcast action update to all connected admins
    reported_user = await db.users.find_one({"_id": ObjectId(reported_user_id)})
    action_notification = {
        "type": "action_taken",
        "report_id": report_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "admin_id": str(current_user["_id"]),
        "admin_name": current_user.get("full_name", "Admin"),
        "target_user": {
            "id": reported_user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown"
        },
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(action_notification))
    
    return {"message": f"Action '{action_data.action}' applied successfully"}

@api_router.post("/admin/moderation/action/user/{user_id}")
async def take_bulk_moderation_action(
    user_id: str,
    action_data: ModerationAction,
    current_user: dict = Depends(get_current_user)
):
    """Take action on all pending reports for a specific user"""
    await check_admin(current_user)
    
    if action_data.action not in MODERATION_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid moderation action")
    
    # Get all pending reports for this user
    pending_reports = await db.reports.find({
        "reported_user_id": user_id,
        "status": "pending"
    }).to_list(500)
    
    if not pending_reports:
        raise HTTPException(status_code=404, detail="No pending reports found for this user")
    
    # Update all reports status
    new_status = "actioned" if action_data.action != "dismiss" else "dismissed"
    await db.reports.update_many(
        {"reported_user_id": user_id, "status": "pending"},
        {
            "$set": {
                "status": new_status,
                "actioned_by": str(current_user["_id"]),
                "actioned_at": datetime.utcnow(),
                "action_taken": action_data.action,
                "action_reason": action_data.reason
            }
        }
    )
    
    # Apply action to user (same logic as single report)
    user_update = {}
    
    if action_data.action == "dismiss":
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"flagged": False}}
        )
    elif action_data.action == "warn":
        user_update = {
            "$inc": {"warnings_count": 1},
            "$set": {
                "last_warning_at": datetime.utcnow(),
                "last_warning_reason": action_data.reason
            }
        }
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user and user.get("warnings_count", 0) >= 2:
            user_update["$set"]["moderation_status"] = "restricted"
    elif action_data.action == "restrict":
        user_update = {
            "$set": {
                "moderation_status": "restricted",
                "restricted_at": datetime.utcnow(),
                "restriction_reason": action_data.reason,
                "flagged": False
            }
        }
    elif action_data.action == "suspend":
        duration_days = action_data.duration_days or 7
        suspended_until = datetime.utcnow() + timedelta(days=duration_days)
        user_update = {
            "$set": {
                "moderation_status": "suspended",
                "suspended_at": datetime.utcnow(),
                "suspended_until": suspended_until,
                "suspension_reason": action_data.reason,
                "flagged": False
            }
        }
    elif action_data.action == "ban":
        user_update = {
            "$set": {
                "moderation_status": "banned",
                "banned_at": datetime.utcnow(),
                "ban_reason": action_data.reason,
                "flagged": False
            }
        }
    
    if user_update:
        await db.users.update_one({"_id": ObjectId(user_id)}, user_update)
    
    # Log the bulk action
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "target_user_id": user_id,
        "action": action_data.action,
        "reason": action_data.reason,
        "reports_actioned": len(pending_reports),
        "is_bulk": True,
        "created_at": datetime.utcnow()
    })
    
    # Broadcast to admins
    reported_user = await db.users.find_one({"_id": ObjectId(user_id)})
    bulk_notification = {
        "type": "bulk_action_taken",
        "action": action_data.action,
        "reason": action_data.reason,
        "admin_name": current_user.get("full_name", "Admin"),
        "target_user": {
            "id": user_id,
            "name": reported_user.get("full_name") if reported_user else "Unknown"
        },
        "reports_actioned": len(pending_reports),
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(bulk_notification))
    
    return {
        "message": f"Action '{action_data.action}' applied to {len(pending_reports)} reports",
        "reports_actioned": len(pending_reports)
    }

@api_router.get("/admin/moderation/user/{user_id}")
async def get_user_moderation_history(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    await check_admin(current_user)
    
    # Get user info
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all reports against this user
    reports = await db.reports.find({"reported_user_id": user_id}).sort("created_at", -1).to_list(50)
    
    # Get moderation log
    mod_log = await db.moderation_log.find({"target_user_id": user_id}).sort("created_at", -1).to_list(50)
    
    return {
        "user": {
            "id": str(user["_id"]),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "moderation_status": user.get("moderation_status", "good_standing"),
            "warnings_count": user.get("warnings_count", 0),
            "flagged": user.get("flagged", False),
            "suspended_until": user.get("suspended_until"),
            "created_at": user.get("created_at")
        },
        "reports": [{
            "id": str(r["_id"]),
            "reason": r.get("reason"),
            "details": r.get("details"),
            "status": r.get("status"),
            "created_at": r.get("created_at")
        } for r in reports],
        "moderation_actions": [{
            "action": m.get("action"),
            "reason": m.get("reason"),
            "created_at": m.get("created_at")
        } for m in mod_log]
    }

@api_router.post("/admin/moderation/lift/{user_id}")
async def lift_moderation_status(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Lift restrictions/suspensions from a user"""
    await check_admin(current_user)
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("moderation_status") == "banned":
        raise HTTPException(status_code=400, detail="Cannot lift ban through this endpoint. Use appeal process.")
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {"moderation_status": "good_standing", "flagged": False},
            "$unset": {"suspended_until": "", "restricted_at": ""}
        }
    )
    
    # Log the action
    await db.moderation_log.insert_one({
        "admin_id": str(current_user["_id"]),
        "target_user_id": user_id,
        "action": "lift_restrictions",
        "created_at": datetime.utcnow()
    })
    
    return {"message": "Moderation status lifted successfully"}

# ==================== APPEAL SYSTEM ENDPOINTS ====================

@api_router.post("/appeals")
async def submit_appeal(appeal_data: AppealCreate, current_user: dict = Depends(get_current_user)):
    """Submit an appeal for a moderation action"""
    user_id = str(current_user["_id"])
    
    # Check if user has a moderation action to appeal
    status = current_user.get("moderation_status", "good_standing")
    if status not in ["suspended", "banned", "restricted", "warned"]:
        raise HTTPException(status_code=400, detail="No moderation action to appeal")
    
    # Check if user already has a pending appeal
    existing_appeal = await db.appeals.find_one({
        "user_id": user_id,
        "status": {"$in": ["pending", "under_review"]}
    })
    
    if existing_appeal:
        raise HTTPException(status_code=400, detail="You already have a pending appeal. Please wait for a decision.")
    
    # Create the appeal
    appeal_doc = {
        "user_id": user_id,
        "user_email": current_user["email"],
        "user_name": current_user.get("full_name"),
        "moderation_status": status,
        "original_reason": current_user.get("ban_reason") or current_user.get("suspension_reason") or current_user.get("last_warning_reason") or "Policy violation",
        "suspended_until": current_user.get("suspended_until"),
        "appeal_reason": appeal_data.reason,
        "additional_details": appeal_data.additional_details,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = await db.appeals.insert_one(appeal_doc)
    
    # Notify admins via WebSocket
    notification = {
        "type": "new_appeal",
        "appeal_id": str(result.inserted_id),
        "user": {
            "id": user_id,
            "name": current_user.get("full_name"),
            "email": current_user["email"]
        },
        "moderation_status": status,
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {
        "message": "Appeal submitted successfully",
        "appeal_id": str(result.inserted_id),
        "status": "pending"
    }

@api_router.get("/appeals/me")
async def get_my_appeal(current_user: dict = Depends(get_current_user)):
    """Get the current user's appeal status"""
    user_id = str(current_user["_id"])
    
    # Get the most recent appeal
    appeal = await db.appeals.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )
    
    if not appeal:
        return {"has_appeal": False}
    
    return {
        "has_appeal": True,
        "appeal": {
            "id": str(appeal["_id"]),
            "status": appeal.get("status"),
            "appeal_reason": appeal.get("appeal_reason"),
            "admin_notes": appeal.get("admin_notes"),
            "decision_at": appeal.get("decision_at").isoformat() if appeal.get("decision_at") else None,
            "created_at": appeal.get("created_at").isoformat() if appeal.get("created_at") else None
        }
    }

@api_router.get("/admin/appeals")
async def get_appeals_queue(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all appeals for admin review"""
    await check_admin(current_user)
    
    query = {}
    if status:
        query["status"] = status
    
    appeals = await db.appeals.find(query).sort("created_at", -1).to_list(100)
    
    result = []
    for appeal in appeals:
        # Get user info
        user = await db.users.find_one({"_id": ObjectId(appeal["user_id"])})
        
        result.append({
            "id": str(appeal["_id"]),
            "user": {
                "id": appeal["user_id"],
                "name": appeal.get("user_name") or (user.get("full_name") if user else "Unknown"),
                "email": appeal.get("user_email") or (user.get("email") if user else "Unknown"),
            },
            "moderation_status": appeal.get("moderation_status"),
            "original_reason": appeal.get("original_reason"),
            "suspended_until": appeal.get("suspended_until").isoformat() if appeal.get("suspended_until") else None,
            "appeal_reason": appeal.get("appeal_reason"),
            "additional_details": appeal.get("additional_details"),
            "status": appeal.get("status"),
            "admin_notes": appeal.get("admin_notes"),
            "decided_by": appeal.get("decided_by"),
            "decision_at": appeal.get("decision_at").isoformat() if appeal.get("decision_at") else None,
            "created_at": appeal.get("created_at").isoformat() if appeal.get("created_at") else None
        })
    
    return result

@api_router.get("/admin/appeals/stats")
async def get_appeals_stats(current_user: dict = Depends(get_current_user)):
    """Get appeal statistics"""
    await check_admin(current_user)
    
    pending = await db.appeals.count_documents({"status": "pending"})
    under_review = await db.appeals.count_documents({"status": "under_review"})
    approved = await db.appeals.count_documents({"status": "approved"})
    denied = await db.appeals.count_documents({"status": "denied"})
    
    return {
        "pending": pending,
        "under_review": under_review,
        "approved": approved,
        "denied": denied,
        "total": pending + under_review + approved + denied
    }

@api_router.post("/admin/appeals/{appeal_id}/action")
async def process_appeal(
    appeal_id: str,
    action_data: AppealAction,
    current_user: dict = Depends(get_current_user)
):
    """Process an appeal (approve or deny)"""
    await check_admin(current_user)
    
    if action_data.action not in ["approve", "deny"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'deny'.")
    
    # Get the appeal
    appeal = await db.appeals.find_one({"_id": ObjectId(appeal_id)})
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    if appeal.get("status") in ["approved", "denied"]:
        raise HTTPException(status_code=400, detail="This appeal has already been processed")
    
    user_id = appeal["user_id"]
    original_status = appeal.get("moderation_status")
    
    # Update appeal status
    new_status = "approved" if action_data.action == "approve" else "denied"
    await db.appeals.update_one(
        {"_id": ObjectId(appeal_id)},
        {
            "$set": {
                "status": new_status,
                "admin_notes": action_data.admin_notes,
                "decided_by": str(current_user["_id"]),
                "decided_by_name": current_user.get("full_name"),
                "decision_at": datetime.utcnow()
            }
        }
    )
    
    # If approved, restore user's account based on original status
    if action_data.action == "approve":
        # Determine restored status based on original moderation status
        # For bans: restore with "warned" status (not fully clean)
        # For suspensions: restore immediately with "good_standing"
        # For all approved appeals: set final_warning flag for faster escalation
        
        if original_status == "banned":
            # Ban appeal approved → restore with "warned" status
            restored_status = "warned"
        else:
            # Suspension/restriction appeal → restore to good standing
            restored_status = "good_standing"
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "moderation_status": restored_status,
                    "flagged": False,
                    "appeal_approved_at": datetime.utcnow(),
                    # CRITICAL: Set final_warning flag for faster escalation on repeat behavior
                    "final_warning": True,
                    "final_warning_at": datetime.utcnow(),
                    "final_warning_reason": f"Restored via appeal from {original_status}. Next violation will escalate faster."
                },
                "$unset": {
                    "suspended_until": "",
                    "suspension_reason": "",
                    "ban_reason": "",
                    "banned_at": "",
                    "suspended_at": "",
                    "restricted_at": "",
                    "restriction_reason": ""
                }
            }
        )
        
        # Log the action with detailed info
        await db.moderation_log.insert_one({
            "admin_id": str(current_user["_id"]),
            "target_user_id": user_id,
            "action": "appeal_approved",
            "appeal_id": appeal_id,
            "original_status": original_status,
            "restored_status": restored_status,
            "final_warning_applied": True,
            "notes": action_data.admin_notes,
            "created_at": datetime.utcnow()
        })
    else:
        # Log denial
        await db.moderation_log.insert_one({
            "admin_id": str(current_user["_id"]),
            "target_user_id": user_id,
            "action": "appeal_denied",
            "appeal_id": appeal_id,
            "original_status": original_status,
            "notes": action_data.admin_notes,
            "created_at": datetime.utcnow()
        })
    
    # Broadcast update to admins
    notification = {
        "type": "appeal_processed",
        "appeal_id": appeal_id,
        "action": action_data.action,
        "original_status": original_status,
        "admin_name": current_user.get("full_name"),
        "created_at": datetime.utcnow().isoformat()
    }
    asyncio.create_task(admin_manager.broadcast_to_admins(notification))
    
    return {
        "message": f"Appeal {action_data.action}d successfully",
        "appeal_status": new_status,
        "restored_status": restored_status if action_data.action == "approve" else None,
        "final_warning_applied": action_data.action == "approve"
    }

@api_router.patch("/admin/appeals/{appeal_id}/review")
async def mark_appeal_under_review(
    appeal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark an appeal as under review"""
    await check_admin(current_user)
    
    appeal = await db.appeals.find_one({"_id": ObjectId(appeal_id)})
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    
    if appeal.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Only pending appeals can be marked as under review")
    
    await db.appeals.update_one(
        {"_id": ObjectId(appeal_id)},
        {
            "$set": {
                "status": "under_review",
                "reviewed_by": str(current_user["_id"]),
                "review_started_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Appeal marked as under review"}

# ==================== USER MODERATION STATUS CHECK ====================

async def check_user_moderation_status(user: dict):
    """Check if user can access the app"""
    status = user.get("moderation_status", "good_standing")
    
    if status == "banned":
        raise HTTPException(
            status_code=403, 
            detail="Your account has been permanently suspended for violating community guidelines."
        )
    
    if status == "suspended":
        suspended_until = user.get("suspended_until")
        if suspended_until and suspended_until > datetime.utcnow():
            raise HTTPException(
                status_code=403,
                detail=f"Your account is suspended until {suspended_until.strftime('%Y-%m-%d %H:%M UTC')}."
            )
        else:
            # Suspension expired, restore status
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"moderation_status": "good_standing"}}
            )

# ==================== PRIVACY SETTINGS ====================

@api_router.get("/privacy/settings")
async def get_privacy_settings(current_user: dict = Depends(get_current_user)):
    return {
        "profile_visibility": current_user.get("profile_visibility", "public"),
        "nearby_discoverable": current_user.get("nearby_discoverable", False),
        "contacts_discoverable": current_user.get("contacts_discoverable", False),
    }

@api_router.put("/privacy/settings")
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

@api_router.post("/portfolio")
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

@api_router.get("/portfolio")
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

@api_router.delete("/portfolio/{image_id}")
async def delete_portfolio_image(image_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
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

# ==================== CLIENT ENDPOINTS ====================

@api_router.post("/clients", response_model=ClientResponse)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    client_doc = {
        "user_id": user_id,
        "name": client_data.name,
        "email": client_data.email,
        "phone": client_data.phone,
        "photo": client_data.photo,
        "notes": client_data.notes,
        "preferences": client_data.preferences,
        "hair_goals": client_data.hair_goals,
        "is_vip": client_data.is_vip,
        "visit_count": 0,
        "last_visit": client_data.last_visit,
        "created_at": datetime.utcnow()
    }
    
    result = await db.clients.insert_one(client_doc)
    client_doc["id"] = str(result.inserted_id)
    
    return ClientResponse(**client_doc)

@api_router.get("/clients", response_model=List[ClientResponse])
async def get_clients(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    clients = await db.clients.find({"user_id": user_id}).to_list(1000)
    
    return [ClientResponse(id=str(c["_id"]), **{k: v for k, v in c.items() if k != "_id"}) for c in clients]

@api_router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        client = await db.clients.find_one({"_id": ObjectId(client_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientResponse(id=str(client["_id"]), **{k: v for k, v in client.items() if k != "_id"})

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, client_data: dict, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.clients.update_one(
            {"_id": ObjectId(client_id), "user_id": str(current_user["_id"])},
            {"$set": client_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"message": "Client updated successfully"}

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.clients.delete_one({"_id": ObjectId(client_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Delete related data
    await db.formulas.delete_many({"client_id": client_id})
    await db.gallery.delete_many({"client_id": client_id})
    await db.appointments.delete_many({"client_id": client_id})
    await db.retail.delete_many({"client_id": client_id})
    await db.no_shows.delete_many({"client_id": client_id})
    
    return {"message": "Client deleted successfully"}

# ==================== FORMULA ENDPOINTS ====================

@api_router.post("/formulas", response_model=FormulaResponse)
async def create_formula(formula_data: FormulaCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    formula_doc = {
        "user_id": user_id,
        "client_id": formula_data.client_id,
        "formula_name": formula_data.formula_name,
        "formula_details": formula_data.formula_details,
        "date_created": formula_data.date_created or datetime.utcnow()
    }
    
    result = await db.formulas.insert_one(formula_doc)
    formula_doc["id"] = str(result.inserted_id)
    
    return FormulaResponse(**formula_doc)

@api_router.get("/formulas", response_model=List[FormulaResponse])
async def get_formulas(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}
    if client_id:
        query["client_id"] = client_id
    
    formulas = await db.formulas.find(query).to_list(1000)
    return [FormulaResponse(id=str(f["_id"]), **{k: v for k, v in f.items() if k != "_id"}) for f in formulas]

@api_router.put("/formulas/{formula_id}")
async def update_formula(formula_id: str, formula_data: dict, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.formulas.update_one(
            {"_id": ObjectId(formula_id), "user_id": str(current_user["_id"])},
            {"$set": formula_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return {"message": "Formula updated successfully"}

@api_router.delete("/formulas/{formula_id}")
async def delete_formula(formula_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.formulas.delete_one({"_id": ObjectId(formula_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    return {"message": "Formula deleted successfully"}

# ==================== GALLERY ENDPOINTS ====================

@api_router.post("/gallery", response_model=GalleryResponse)
async def create_gallery(gallery_data: GalleryCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    gallery_doc = {
        "user_id": user_id,
        "client_id": gallery_data.client_id,
        "before_photo": gallery_data.before_photo,
        "after_photo": gallery_data.after_photo,
        "notes": gallery_data.notes,
        "date_taken": gallery_data.date_taken or datetime.utcnow()
    }
    
    result = await db.gallery.insert_one(gallery_doc)
    gallery_doc["id"] = str(result.inserted_id)
    
    return GalleryResponse(**gallery_doc)

@api_router.get("/gallery", response_model=List[GalleryResponse])
async def get_gallery(client_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    query = {"user_id": user_id}
    if client_id:
        query["client_id"] = client_id
    
    gallery = await db.gallery.find(query).sort("date_taken", -1).to_list(1000)
    return [GalleryResponse(id=str(g["_id"]), **{k: v for k, v in g.items() if k != "_id"}) for g in gallery]

@api_router.delete("/gallery/{gallery_id}")
async def delete_gallery(gallery_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.gallery.delete_one({"_id": ObjectId(gallery_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    return {"message": "Gallery item deleted successfully"}

# ==================== APPOINTMENT ENDPOINTS ====================

@api_router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(appointment_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    appointment_doc = {
        "user_id": user_id,
        "client_id": appointment_data.client_id,
        "appointment_date": appointment_data.appointment_date,
        "service": appointment_data.service,
        "duration_minutes": appointment_data.duration_minutes,
        "notes": appointment_data.notes,
        "status": appointment_data.status
    }
    
    result = await db.appointments.insert_one(appointment_doc)
    appointment_doc["id"] = str(result.inserted_id)
    
    # Get client name
    from bson import ObjectId
    try:
        client = await db.clients.find_one({"_id": ObjectId(appointment_data.client_id)})
        appointment_doc["client_name"] = client["name"] if client else None
    except:
        appointment_doc["client_name"] = None
    
    return AppointmentResponse(**appointment_doc)

@api_router.get("/appointments", response_model=List[AppointmentResponse])
async def get_appointments(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    appointments = await db.appointments.find({"user_id": user_id}).sort("appointment_date", 1).to_list(1000)
    
    # Enrich with client names
    from bson import ObjectId
    result = []
    for apt in appointments:
        try:
            client = await db.clients.find_one({"_id": ObjectId(apt["client_id"])})
            apt["client_name"] = client["name"] if client else None
        except:
            apt["client_name"] = None
        
        result.append(AppointmentResponse(id=str(apt["_id"]), **{k: v for k, v in apt.items() if k != "_id"}))
    
    return result

@api_router.put("/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, appointment_data: dict, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.appointments.update_one(
            {"_id": ObjectId(appointment_id), "user_id": str(current_user["_id"])},
            {"$set": appointment_data}
        )
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # If status changed to completed, update client visit count
    if appointment_data.get("status") == "completed":
        appointment = await db.appointments.find_one({"_id": ObjectId(appointment_id)})
        if appointment:
            await db.clients.update_one(
                {"_id": ObjectId(appointment["client_id"])},
                {
                    "$inc": {"visit_count": 1},
                    "$set": {"last_visit": datetime.utcnow()}
                }
            )
    
    return {"message": "Appointment updated successfully"}

@api_router.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.appointments.delete_one({"_id": ObjectId(appointment_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Appointment deleted successfully"}

# ==================== INCOME ENDPOINTS ====================

@api_router.post("/income", response_model=IncomeResponse)
async def create_income(income_data: IncomeCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    income_doc = {
        "user_id": user_id,
        "client_id": income_data.client_id,
        "amount": income_data.amount,
        "service": income_data.service,
        "date": income_data.date or datetime.utcnow(),
        "payment_method": income_data.payment_method
    }
    
    result = await db.income.insert_one(income_doc)
    income_doc["id"] = str(result.inserted_id)
    
    # Get client name
    from bson import ObjectId
    if income_data.client_id:
        try:
            client = await db.clients.find_one({"_id": ObjectId(income_data.client_id)})
            income_doc["client_name"] = client["name"] if client else None
        except:
            income_doc["client_name"] = None
    else:
        income_doc["client_name"] = None
    
    return IncomeResponse(**income_doc)

@api_router.get("/income", response_model=List[IncomeResponse])
async def get_income(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    income = await db.income.find({"user_id": user_id}).sort("date", -1).to_list(1000)
    
    # Enrich with client names
    from bson import ObjectId
    result = []
    for inc in income:
        if inc.get("client_id"):
            try:
                client = await db.clients.find_one({"_id": ObjectId(inc["client_id"])})
                inc["client_name"] = client["name"] if client else None
            except:
                inc["client_name"] = None
        else:
            inc["client_name"] = None
        
        result.append(IncomeResponse(id=str(inc["_id"]), **{k: v for k, v in inc.items() if k != "_id"}))
    
    return result

@api_router.get("/income/stats")
async def get_income_stats(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Get all income records
    income = await db.income.find({"user_id": user_id}).to_list(1000)
    
    # Calculate stats
    total = sum(i["amount"] for i in income)
    
    # Today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_income = sum(i["amount"] for i in income if i["date"] >= today_start)
    
    # This week
    week_start = today_start - timedelta(days=today_start.weekday())
    week_income = sum(i["amount"] for i in income if i["date"] >= week_start)
    
    # This month
    month_start = today_start.replace(day=1)
    month_income = sum(i["amount"] for i in income if i["date"] >= month_start)
    
    return {
        "total": total,
        "today": today_income,
        "week": week_income,
        "month": month_income
    }

# ==================== RETAIL ENDPOINTS ====================

@api_router.post("/retail", response_model=RetailResponse)
async def create_retail(retail_data: RetailCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    retail_doc = {
        "user_id": user_id,
        "client_id": retail_data.client_id,
        "product_name": retail_data.product_name,
        "recommended": retail_data.recommended,
        "purchased": retail_data.purchased,
        "date": retail_data.date or datetime.utcnow()
    }
    
    result = await db.retail.insert_one(retail_doc)
    retail_doc["id"] = str(result.inserted_id)
    
    # Get client name
    from bson import ObjectId
    try:
        client = await db.clients.find_one({"_id": ObjectId(retail_data.client_id)})
        retail_doc["client_name"] = client["name"] if client else None
    except:
        retail_doc["client_name"] = None
    
    return RetailResponse(**retail_doc)

@api_router.get("/retail", response_model=List[RetailResponse])
async def get_retail(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    retail = await db.retail.find({"user_id": user_id}).sort("date", -1).to_list(1000)
    
    # Enrich with client names
    from bson import ObjectId
    result = []
    for ret in retail:
        try:
            client = await db.clients.find_one({"_id": ObjectId(ret["client_id"])})
            ret["client_name"] = client["name"] if client else None
        except:
            ret["client_name"] = None
        
        result.append(RetailResponse(id=str(ret["_id"]), **{k: v for k, v in ret.items() if k != "_id"}))
    
    return result

@api_router.delete("/retail/{retail_id}")
async def delete_retail(retail_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.retail.delete_one({"_id": ObjectId(retail_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Retail record not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Retail record not found")
    
    return {"message": "Retail record deleted successfully"}

# ==================== NO-SHOW ENDPOINTS ====================

@api_router.post("/no-shows", response_model=NoShowResponse)
async def create_no_show(no_show_data: NoShowCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    no_show_doc = {
        "user_id": user_id,
        "client_id": no_show_data.client_id,
        "appointment_date": no_show_data.appointment_date,
        "notes": no_show_data.notes,
        "created_at": datetime.utcnow()
    }
    
    result = await db.no_shows.insert_one(no_show_doc)
    no_show_doc["id"] = str(result.inserted_id)
    
    # Get client name
    from bson import ObjectId
    try:
        client = await db.clients.find_one({"_id": ObjectId(no_show_data.client_id)})
        no_show_doc["client_name"] = client["name"] if client else None
    except:
        no_show_doc["client_name"] = None
    
    return NoShowResponse(**no_show_doc)

@api_router.get("/no-shows", response_model=List[NoShowResponse])
async def get_no_shows(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    no_shows = await db.no_shows.find({"user_id": user_id}).sort("appointment_date", -1).to_list(1000)
    
    # Enrich with client names
    from bson import ObjectId
    result = []
    for ns in no_shows:
        try:
            client = await db.clients.find_one({"_id": ObjectId(ns["client_id"])})
            ns["client_name"] = client["name"] if client else None
        except:
            ns["client_name"] = None
        
        result.append(NoShowResponse(id=str(ns["_id"]), **{k: v for k, v in ns.items() if k != "_id"}))
    
    return result

@api_router.delete("/no-shows/{no_show_id}")
async def delete_no_show(no_show_id: str, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    
    try:
        result = await db.no_shows.delete_one({"_id": ObjectId(no_show_id), "user_id": str(current_user["_id"])})
    except:
        raise HTTPException(status_code=404, detail="No-show record not found")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No-show record not found")
    
    return {"message": "No-show record deleted successfully"}

# ==================== AI ASSISTANT ENDPOINTS ====================

@api_router.post("/ai/chat", response_model=AIMessageResponse)
async def ai_chat(request: AIMessageRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Get user context
        user_id = str(current_user["_id"])
        clients_count = await db.clients.count_documents({"user_id": user_id})
        appointments_count = await db.appointments.count_documents({"user_id": user_id})
        
        # Create system message with context
        system_message = f"""You are StyleFlow AI, an intelligent assistant for hairstylists. You help with:
- Client follow-up suggestions and rebooking reminders
- Formula recall and hair color recommendations
- Business insights and revenue tracking
- Content ideas for social media
- Product upsell suggestions based on client history
- Retention strategies

Current user context:
- Total clients: {clients_count}
- Total appointments: {appointments_count}

Be helpful, professional, and focused on helping the stylist grow their business."""

        # Additional context if provided
        if request.context:
            system_message += f"\n\nAdditional context: {request.context}"
        
        # Initialize LLM Chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"styleflow_{user_id}_{datetime.utcnow().timestamp()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Send message
        user_message = UserMessage(text=request.message)
        response = await chat.send_message(user_message)
        
        return AIMessageResponse(response=response)
    
    except Exception as e:
        logging.error(f"AI chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI assistant unavailable")

# ==================== DASHBOARD ENDPOINTS ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Get counts
    total_clients = await db.clients.count_documents({"user_id": user_id})
    vip_clients = await db.clients.count_documents({"user_id": user_id, "is_vip": True})
    
    # Today's appointments
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_appointments = await db.appointments.count_documents({
        "user_id": user_id,
        "appointment_date": {"$gte": today_start, "$lt": today_end}
    })
    
    # This week's appointments
    week_start = today_start - timedelta(days=today_start.weekday())
    week_appointments = await db.appointments.count_documents({
        "user_id": user_id,
        "appointment_date": {"$gte": week_start}
    })
    
    # Followers count
    from bson import ObjectId
    followers_count = await db.connections.count_documents({
        "following_id": ObjectId(current_user["_id"]),
        "status": "active"
    })
    
    # New clients this week
    new_clients_this_week = await db.clients.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": week_start}
    })
    
    # Clients due for rebooking (no visit in last 60 days)
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    clients_due = await db.clients.count_documents({
        "user_id": user_id,
        "last_visit": {"$lt": sixty_days_ago}
    })
    
    return {
        "total_clients": total_clients,
        "vip_clients": vip_clients,
        "today_appointments": today_appointments,
        "week_appointments": week_appointments,
        "followers_count": followers_count,
        "new_clients_this_week": new_clients_this_week,
        "clients_due_rebooking": clients_due
    }

# ==================== APP STORE COMPLIANCE ====================

@api_router.get("/support")
async def get_support():
    return {
        "email": "support@styleflow.app",
        "website": "https://styleflow.app/support"
    }

@api_router.get("/privacy-policy")
async def get_privacy_policy():
    return {
        "url": "https://styleflow.app/privacy"
    }

@api_router.get("/terms-of-service")
async def get_terms():
    return {
        "url": "https://styleflow.app/terms"
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
