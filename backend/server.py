from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from bson import ObjectId
import logging
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
import jwt
import bcrypt
import json
import asyncio
import secrets
import resend
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import from new modular structure
from core.config import settings
from core.database import db, client

# JWT Configuration (use from settings)
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRATION = settings.JWT_EXPIRATION_MINUTES

# OpenAI Configuration
EMERGENT_LLM_KEY = settings.EMERGENT_LLM_KEY

# Resend Configuration
RESEND_API_KEY = settings.RESEND_API_KEY
resend.api_key = RESEND_API_KEY

# App deep link scheme
APP_SCHEME = settings.APP_SCHEME
APP_DOMAIN = settings.APP_DOMAIN
APP_BUNDLE_ID = settings.APP_BUNDLE_ID
APP_TEAM_ID = settings.APP_TEAM_ID

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import and include route modules
from routes.auth import router as auth_router
from routes.clients import router as clients_router, enrich_client_with_rebook
from routes.formulas import router as formulas_router
from routes.gallery import router as gallery_router
from routes.appointments import router as appointments_router
from routes.business import router as business_router
from routes.ai import router as ai_router
from routes.dashboard import router as dashboard_router
from routes.users import router as users_router
from routes.posts import router as posts_router
from routes.admin import router as admin_router, get_admin_manager, get_grouped_queue_func

api_router.include_router(auth_router)
api_router.include_router(clients_router)
api_router.include_router(formulas_router)
api_router.include_router(gallery_router)
api_router.include_router(appointments_router)
api_router.include_router(business_router)
api_router.include_router(ai_router)
api_router.include_router(dashboard_router)
api_router.include_router(users_router)
api_router.include_router(posts_router)
api_router.include_router(admin_router)

# Get admin manager for WebSocket
admin_manager = get_admin_manager()

# Security
security = HTTPBearer()

# ==================== APPLE APP SITE ASSOCIATION (iOS Universal Links) ====================

from fastapi.responses import JSONResponse

@app.get("/.well-known/apple-app-site-association")
async def apple_app_site_association():
    """
    Apple App Site Association file for iOS Universal Links.
    This enables the reset password link to open directly in the app.
    
    IMPORTANT: For production, replace APP_TEAM_ID with your actual Apple Developer Team ID.
    The Team ID can be found in your Apple Developer account under Membership.
    """
    aasa = {
        "applinks": {
            "apps": [],
            "details": [
                {
                    "appIDs": [f"{APP_TEAM_ID}.{APP_BUNDLE_ID}"],
                    "paths": [
                        "/reset-password",
                        "/reset-password/*",
                        "/reset-password?*"
                    ],
                    "components": [
                        {
                            "/": "/reset-password",
                            "?": {"token": "?*"}
                        }
                    ]
                }
            ]
        },
        "webcredentials": {
            "apps": [f"{APP_TEAM_ID}.{APP_BUNDLE_ID}"]
        }
    }
    
    return JSONResponse(
        content=aasa,
        media_type="application/json",
        headers={
            "Content-Type": "application/json"
        }
    )

@app.get("/.well-known/assetlinks.json")
async def android_asset_links():
    """
    Android Asset Links for App Links (Android equivalent of Universal Links).
    """
    asset_links = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "com.styleflow.app",
                "sha256_cert_fingerprints": [
                    "YOUR_SHA256_FINGERPRINT"  # Replace with actual SHA256 from your signing key
                ]
            }
        }
    ]
    
    return JSONResponse(
        content=asset_links,
        media_type="application/json"
    )

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Check MongoDB connection
        await db.command("ping")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "styleflow-api",
        "version": "1.0.0",
        "database": db_status
    }

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
    token: str
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
    rebook_interval_days: Optional[int] = 42  # Default 6 weeks

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
    rebook_interval_days: Optional[int] = 42
    next_visit_due: Optional[datetime] = None  # Calculated field
    rebook_status: Optional[str] = None  # "on_track", "due_soon", "overdue"

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

# ==================== POST & ENGAGEMENT MODELS ====================

# Predefined trend tags for hairstyling
TREND_TAGS = [
    "balayage", "colortrend", "transformation", "mensstyle", "curlyhair",
    "blondehair", "brunette", "redhead", "highlights", "lowlights",
    "ombre", "sombre", "haircut", "pixiecut", "bobcut", "layers",
    "extensions", "braids", "updo", "wedding", "editorial", "natural",
    "vivids", "pastels", "colorcorrection", "keratintreatment", "textured"
]

class PostCreate(BaseModel):
    images: List[str]  # Base64 encoded images (max 5)
    caption: Optional[str] = None
    tags: Optional[List[str]] = []  # Trend tags

class PostUpdate(BaseModel):
    caption: Optional[str] = None
    tags: Optional[List[str]] = None

class CommentCreate(BaseModel):
    text: str

class ShareCreate(BaseModel):
    caption: Optional[str] = None  # Optional message when sharing

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

# ==================== APP STORE COMPLIANCE ====================


@api_router.get("/support")
async def get_support():
    return {
        "email": f"support@{APP_DOMAIN}",
        "website": f"https://{APP_DOMAIN}/support"
    }

@api_router.get("/privacy-policy")
async def get_privacy_policy():
    return {
        "url": f"https://{APP_DOMAIN}/privacy"
    }

@api_router.get("/terms-of-service")
async def get_terms():
    return {
        "url": f"https://{APP_DOMAIN}/terms"
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
