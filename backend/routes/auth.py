from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
import secrets
import logging
import resend

from core.database import db
from core.config import settings
from core.dependencies import get_current_user
from models.auth import UserSignup, UserLogin, PasswordReset, PasswordResetConfirm
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize resend
resend.api_key = settings.RESEND_API_KEY

@router.post("/signup")
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

@router.post("/login")
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
        "created_at": datetime.utcnow()
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
    reset_record = await db.password_resets.find_one({"token": request.token})
    
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
    
    # Update password
    hashed_password = hash_password(request.new_password)
    await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password": hashed_password}}
    )
    
    # Delete the used token
    await db.password_resets.delete_one({"token": request.token})
    
    return {"message": "Password reset successful"}

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid before showing reset form"""
    reset_record = await db.password_resets.find_one({"token": token})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    if reset_record["expires_at"] < datetime.utcnow():
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    return {
        "valid": True,
        "email": reset_record["email"][:3] + "***" + reset_record["email"][reset_record["email"].index("@"):]  # Masked email
    }

@router.delete("/delete-account")
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

@router.get("/me")
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

@router.put("/profile")
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
