from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime, timedelta
from typing import Optional
import secrets
import logging
import resend
from bson import ObjectId

from core.database import db
from core.config import settings
from core.dependencies import get_current_user
from models.auth import UserSignup, UserLogin, PasswordReset, PasswordResetConfirm
from utils.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    create_token_pair,
    verify_refresh_token,
    decode_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize resend
resend.api_key = settings.RESEND_API_KEY

# App Store Review Tester emails (bypass paywall)
TESTER_EMAILS = [
    "appreview@apple.com",
    "tester@styleflow.com",
    "review@styleflow.com"
]

def is_tester_account(email: str) -> bool:
    """Check if email is a designated tester account"""
    return email.lower() in [e.lower() for e in TESTER_EMAILS]

@router.post("/signup")
async def signup(user_data: UserSignup):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Check if tester account
    is_tester = is_tester_account(user_data.email)
    
    # Create user document with all fields
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
        "updated_at": datetime.utcnow(),
        # Subscription fields
        "subscription_status": "active" if is_tester else "free",
        "subscription_tier": "premium" if is_tester else "free",
        # Tester flag for App Store Review
        "is_tester": is_tester,
        "is_admin": is_tester,  # Testers get admin access too
        # AI usage tracking
        "ai_uses_today": 0,
        "ai_uses_reset_date": datetime.utcnow().date().isoformat(),
        # JWT tracking
        "last_login": datetime.utcnow(),
        "refresh_token_jti": None,  # For token revocation
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create token pair with additional claims
    additional_claims = {
        "user_id": user_id,
        "is_tester": is_tester,
        "is_admin": is_tester,
        "subscription_status": "active" if is_tester else "free"
    }
    
    access_token, refresh_token = create_token_pair(user_data.email, additional_claims)
    
    # Store refresh token JTI for revocation support
    refresh_payload = decode_token(refresh_token)
    if refresh_payload:
        await db.users.update_one(
            {"_id": result.inserted_id},
            {"$set": {"refresh_token_jti": refresh_payload.get("jti")}}
        )
    
    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "business_name": user_data.business_name,
            "is_tester": is_tester,
            "is_admin": is_tester,
            "subscription_status": "active" if is_tester else "free"
        }
    }

@router.post("/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(user["_id"])
    is_tester = user.get("is_tester", is_tester_account(credentials.email))
    is_admin = user.get("is_admin", is_tester)
    subscription_status = user.get("subscription_status", "active" if is_tester else "free")
    
    # Update tester status if not already set
    if is_tester_account(credentials.email) and not user.get("is_tester"):
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "is_tester": True,
                "is_admin": True,
                "subscription_status": "active",
                "subscription_tier": "premium"
            }}
        )
        is_tester = True
        is_admin = True
        subscription_status = "active"
    
    # Create token pair with additional claims
    additional_claims = {
        "user_id": user_id,
        "is_tester": is_tester,
        "is_admin": is_admin,
        "subscription_status": subscription_status
    }
    
    access_token, refresh_token = create_token_pair(credentials.email, additional_claims)
    
    # Update last login and refresh token JTI
    refresh_payload = decode_token(refresh_token)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "last_login": datetime.utcnow(),
            "refresh_token_jti": refresh_payload.get("jti") if refresh_payload else None
        }}
    )
    
    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "email": user["email"],
            "full_name": user["full_name"],
            "business_name": user.get("business_name"),
            "profile_photo": user.get("profile_photo"),
            "is_tester": is_tester,
            "is_admin": is_admin,
            "subscription_status": subscription_status
        }
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str = Header(..., alias="X-Refresh-Token")):
    """
    Refresh an expired access token using a valid refresh token
    """
    # Verify refresh token
    email = verify_refresh_token(refresh_token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Get user and verify refresh token JTI hasn't been revoked
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    refresh_payload = decode_token(refresh_token)
    if not refresh_payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # Check if this refresh token's JTI matches the stored one (revocation check)
    stored_jti = user.get("refresh_token_jti")
    token_jti = refresh_payload.get("jti")
    # If no stored JTI (user logged out) OR token doesn't match, reject
    if not stored_jti or token_jti != stored_jti:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    
    user_id = str(user["_id"])
    is_tester = user.get("is_tester", False)
    is_admin = user.get("is_admin", False)
    subscription_status = user.get("subscription_status", "free")
    
    # Create new token pair
    additional_claims = {
        "user_id": user_id,
        "is_tester": is_tester,
        "is_admin": is_admin,
        "subscription_status": subscription_status
    }
    
    new_access_token, new_refresh_token = create_token_pair(email, additional_claims)
    
    # Update stored refresh token JTI
    new_refresh_payload = decode_token(new_refresh_token)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"refresh_token_jti": new_refresh_payload.get("jti") if new_refresh_payload else None}}
    )
    
    return {
        "token": new_access_token,
        "refresh_token": new_refresh_token
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user by revoking their refresh token
    """
    # Invalidate refresh token by clearing the JTI
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"refresh_token_jti": None}}
    )
    
    return {"message": "Logged out successfully"}

@router.post("/forgot-password")
async def forgot_password(request: PasswordReset):
    user = await db.users.find_one({"email": request.email})
    if not user:
        # Don't reveal if email exists - security best practice
        return {"message": "If email exists, reset instructions sent"}
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    
    # Store reset token in database
    await db.password_resets.delete_many({"email": request.email})  # Remove old tokens
    await db.password_resets.insert_one({
        "email": request.email,
        "token": reset_token,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
        "used": False
    })
    
    # Create deep link for app (iOS universal link)
    reset_link = f"https://{settings.APP_DOMAIN}/reset-password?token={reset_token}"
    
    # Send email via Resend
    try:
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #1a1a1a; color: #ffffff; padding: 40px 20px; margin: 0;">
            <div style="max-width: 480px; margin: 0 auto; background-color: #2a2a2a; border-radius: 16px; padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <div style="text-align: center; margin-bottom: 24px;">
                    <h1 style="color: #8BA889; margin: 0; font-size: 28px;">StyleFlow</h1>
                    <p style="color: #888888; margin: 8px 0 0 0; font-size: 14px;">Password Reset Request</p>
                </div>
                
                <p style="color: #ffffff; font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
                    Hi {user.get('full_name', 'there')},
                </p>
                
                <p style="color: #cccccc; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
                    We received a request to reset your password. Tap the button below to create a new password:
                </p>
                
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{reset_link}" style="display: inline-block; background-color: #8BA889; color: #1a1a1a; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 600; font-size: 16px;">
                        Reset Password
                    </a>
                </div>
                
                <p style="color: #888888; font-size: 13px; line-height: 1.6; margin-bottom: 16px;">
                    This link will expire in 1 hour for security reasons.
                </p>
                
                <p style="color: #888888; font-size: 13px; line-height: 1.6;">
                    If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.
                </p>
                
                <hr style="border: none; border-top: 1px solid #444444; margin: 32px 0;">
                
                <p style="color: #666666; font-size: 12px; text-align: center; margin: 0;">
                    © {datetime.utcnow().year} StyleFlow. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        params = {
            "from": f"StyleFlow <no-reply@{settings.APP_DOMAIN}>",
            "to": [request.email],
            "subject": "Reset Your StyleFlow Password",
            "html": email_html,
        }
        
        resend.Emails.send(params)
        
    except Exception as e:
        logging.error(f"Failed to send reset email: {e}")
        # Still return success to not reveal if email exists
    
    return {"message": "If email exists, reset instructions sent"}

@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    # Find the reset token
    reset_record = await db.password_resets.find_one({
        "token": request.token,
        "used": {"$ne": True}
    })
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token has expired
    if reset_record["expires_at"] < datetime.utcnow():
        # Delete expired token
        await db.password_resets.delete_one({"token": request.token})
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Find the user
    user = await db.users.find_one({"email": reset_record["email"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password and invalidate all existing tokens
    hashed_password = hash_password(request.new_password)
    await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {
            "password": hashed_password,
            "refresh_token_jti": None,  # Invalidate all refresh tokens
            "password_changed_at": datetime.utcnow()
        }}
    )
    
    # Mark token as used (instead of deleting, for audit trail)
    await db.password_resets.update_one(
        {"token": request.token},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )
    
    return {"message": "Password reset successful. Please login with your new password."}

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """
    Verify if a password reset token is valid (used by frontend before showing form)
    """
    reset_record = await db.password_resets.find_one({
        "token": token,
        "used": {"$ne": True}
    })
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    if reset_record["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    return {"valid": True, "email": reset_record["email"]}

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
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
        "is_tester": current_user.get("is_tester", False),
        "is_admin": current_user.get("is_admin", False),
        "ai_uses_today": current_user.get("ai_uses_today", 0),
        "moderation_status": current_user.get("moderation_status"),
        "warnings_count": current_user.get("warnings_count", 0)
    }

@router.put("/profile")
async def update_profile(data: dict, current_user: dict = Depends(get_current_user)):
    # Filter allowed fields
    allowed_fields = [
        "full_name", "business_name", "bio", "specialties", 
        "salon_name", "city", "profile_photo", "instagram_handle",
        "tiktok_handle", "website_url", "profile_visibility"
    ]
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow()
    
    if update_data:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "full_name": updated_user["full_name"],
        "business_name": updated_user.get("business_name"),
        "bio": updated_user.get("bio"),
        "profile_photo": updated_user.get("profile_photo"),
        "is_tester": updated_user.get("is_tester", False),
        "is_admin": updated_user.get("is_admin", False),
        "subscription_status": updated_user.get("subscription_status", "free")
    }

@router.delete("/account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # Delete all user data
    await db.clients.delete_many({"user_id": user_id})
    await db.appointments.delete_many({"user_id": user_id})
    await db.formulas.delete_many({"user_id": user_id})
    await db.posts.delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": current_user["_id"]})
    
    return {"message": "Account deleted successfully"}
