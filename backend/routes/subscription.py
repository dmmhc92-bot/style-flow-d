from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import httpx
from dotenv import load_dotenv

from core.dependencies import get_current_user
from core.database import db

load_dotenv()

router = APIRouter(prefix="/subscription", tags=["subscription"])

# RevenueCat configuration
REVENUECAT_SECRET_KEY = os.getenv("REVENUECAT_SECRET_KEY", "")
REVENUECAT_API_URL = "https://api.revenuecat.com/v1"

# Pydantic models
class SubscriptionVerify(BaseModel):
    action: str
    product_id: Optional[str] = None
    is_premium: bool = False

class SubscriptionSync(BaseModel):
    is_premium: bool
    entitlements: List[str] = []

class SubscriptionStatus(BaseModel):
    is_premium: bool
    subscription_status: str
    expires_at: Optional[str] = None
    product_id: Optional[str] = None

# Helper to get RevenueCat headers
def get_revenuecat_headers():
    return {
        "Authorization": f"Bearer {REVENUECAT_SECRET_KEY}",
        "Content-Type": "application/json"
    }

@router.post("/verify")
async def verify_subscription(
    data: SubscriptionVerify,
    current_user: dict = Depends(get_current_user)
):
    """Verify a subscription purchase from mobile app"""
    try:
        user_id = str(current_user["_id"])
        
        # Update user's subscription status in database
        subscription_data = {
            "subscription_status": "active" if data.is_premium else "free",
            "subscription_updated_at": datetime.utcnow(),
        }
        
        if data.product_id:
            subscription_data["subscription_product_id"] = data.product_id
        
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": subscription_data}
        )
        
        return {
            "status": "success",
            "message": "Subscription verified",
            "is_premium": data.is_premium
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@router.post("/sync")
async def sync_subscription(
    data: SubscriptionSync,
    current_user: dict = Depends(get_current_user)
):
    """Sync subscription status from mobile app"""
    try:
        user_id = str(current_user["_id"])
        
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {
                "subscription_status": "active" if data.is_premium else "free",
                "subscription_entitlements": data.entitlements,
                "subscription_synced_at": datetime.utcnow()
            }}
        )
        
        return {
            "status": "success",
            "message": "Subscription synced"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/restore")
async def restore_purchases(
    data: SubscriptionVerify,
    current_user: dict = Depends(get_current_user)
):
    """Handle purchase restoration"""
    try:
        user_id = str(current_user["_id"])
        
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": {
                "subscription_status": "active" if data.is_premium else "free",
                "subscription_restored_at": datetime.utcnow()
            }}
        )
        
        return {
            "status": "success",
            "message": "Purchases restored",
            "is_premium": data.is_premium
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    try:
        user = await db.users.find_one({"_id": current_user["_id"]})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return SubscriptionStatus(
            is_premium=user.get("subscription_status") == "active",
            subscription_status=user.get("subscription_status", "free"),
            expires_at=user.get("subscription_expires_at"),
            product_id=user.get("subscription_product_id")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/webhook/revenuecat")
async def revenuecat_webhook(request: dict):
    """
    Handle RevenueCat webhook events.
    Configure this URL in RevenueCat dashboard.
    """
    try:
        event_type = request.get("event", {}).get("type")
        subscriber = request.get("subscriber", {})
        app_user_id = subscriber.get("original_app_user_id")
        
        if not app_user_id:
            return {"status": "ignored", "reason": "No user ID"}
        
        # Find user by RevenueCat ID or email
        user = await db.users.find_one({
            "$or": [
                {"revenuecat_id": app_user_id},
                {"email": app_user_id}
            ]
        })
        
        if not user:
            return {"status": "ignored", "reason": "User not found"}
        
        # Update based on event type
        update_data = {"subscription_webhook_at": datetime.utcnow()}
        
        if event_type == "INITIAL_PURCHASE":
            update_data["subscription_status"] = "active"
            update_data["subscription_started_at"] = datetime.utcnow()
        elif event_type == "RENEWAL":
            update_data["subscription_status"] = "active"
            update_data["subscription_renewed_at"] = datetime.utcnow()
        elif event_type == "CANCELLATION":
            update_data["subscription_cancelled_at"] = datetime.utcnow()
            # Don't immediately set to inactive - let it expire naturally
        elif event_type == "EXPIRATION":
            update_data["subscription_status"] = "expired"
            update_data["subscription_expired_at"] = datetime.utcnow()
        elif event_type == "BILLING_ISSUE":
            update_data["subscription_billing_issue"] = True
        
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        return {"status": "processed", "event": event_type}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/check-premium")
async def check_premium_access(current_user: dict = Depends(get_current_user)):
    """Quick check if user has premium access"""
    try:
        user = await db.users.find_one({"_id": current_user["_id"]})
        
        if not user:
            return {"has_premium": False}
        
        # Check subscription status
        status = user.get("subscription_status", "free")
        is_premium = status == "active"
        
        # Check if expired
        expires_at = user.get("subscription_expires_at")
        if expires_at and isinstance(expires_at, datetime):
            if expires_at < datetime.utcnow():
                is_premium = False
        
        return {
            "has_premium": is_premium,
            "status": status
        }
    except Exception as e:
        return {"has_premium": False, "error": str(e)}
