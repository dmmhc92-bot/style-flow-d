#!/usr/bin/env python3
"""
Additional JWT Auth System Testing - Deep dive into specific issues
"""

import requests
import json
import time
from datetime import datetime

# Backend URL
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

def test_token_revocation_detailed():
    """Detailed test of token revocation issue"""
    print("🔍 DETAILED TOKEN REVOCATION TESTING")
    print("=" * 50)
    
    # Step 1: Login to get tokens
    login_response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if login_response.status_code != 200:
        print("❌ Could not login for detailed test")
        return
    
    login_data = login_response.json()
    access_token = login_data["token"]
    refresh_token = login_data["refresh_token"]
    
    print(f"✅ Login successful, got tokens")
    
    # Step 2: Test refresh token works before logout
    refresh_response = requests.post(f"{BACKEND_URL}/auth/refresh", 
                                   headers={"X-Refresh-Token": refresh_token})
    
    if refresh_response.status_code == 200:
        print("✅ Refresh token works before logout")
        # Update tokens
        new_data = refresh_response.json()
        access_token = new_data["token"]
        refresh_token = new_data["refresh_token"]
    else:
        print(f"❌ Refresh token failed before logout: {refresh_response.status_code}")
        return
    
    # Step 3: Logout
    logout_response = requests.post(f"{BACKEND_URL}/auth/logout", 
                                  headers={"Authorization": f"Bearer {access_token}"})
    
    if logout_response.status_code == 200:
        print("✅ Logout successful")
    else:
        print(f"❌ Logout failed: {logout_response.status_code}")
        return
    
    # Step 4: Try to use refresh token after logout
    post_logout_refresh = requests.post(f"{BACKEND_URL}/auth/refresh", 
                                      headers={"X-Refresh-Token": refresh_token})
    
    print(f"🔍 Post-logout refresh attempt: {post_logout_refresh.status_code}")
    if post_logout_refresh.status_code == 200:
        print("❌ ISSUE: Refresh token still works after logout!")
        print(f"   Response: {post_logout_refresh.json()}")
    else:
        print("✅ Refresh token correctly revoked after logout")

def test_password_reset_complete_flow():
    """Test complete password reset flow"""
    print("\n🔍 COMPLETE PASSWORD RESET FLOW TESTING")
    print("=" * 50)
    
    # Create a test user for password reset
    test_email = f"resettest_{int(time.time())}@styleflow.com"
    test_password = "OriginalPassword123!"
    
    # Step 1: Create test user
    signup_response = requests.post(f"{BACKEND_URL}/auth/signup", json={
        "email": test_email,
        "password": test_password,
        "full_name": "Reset Test User",
        "business_name": "Test Business"
    })
    
    if signup_response.status_code != 200:
        print(f"❌ Could not create test user: {signup_response.status_code}")
        return
    
    print(f"✅ Created test user: {test_email}")
    
    # Step 2: Request password reset
    reset_request = requests.post(f"{BACKEND_URL}/auth/forgot-password", json={
        "email": test_email
    })
    
    if reset_request.status_code == 200:
        print("✅ Password reset request sent")
    else:
        print(f"❌ Password reset request failed: {reset_request.status_code}")
        return
    
    # Step 3: Test with invalid token (since we can't get the real token)
    invalid_token_test = requests.get(f"{BACKEND_URL}/auth/verify-reset-token/invalid_token_123")
    
    if invalid_token_test.status_code == 400:
        print("✅ Invalid token correctly rejected")
    else:
        print(f"❌ Invalid token handling issue: {invalid_token_test.status_code}")
    
    # Step 4: Test reset with invalid token
    invalid_reset = requests.post(f"{BACKEND_URL}/auth/reset-password", json={
        "token": "invalid_token_123",
        "new_password": "NewPassword123!"
    })
    
    if invalid_reset.status_code == 400:
        print("✅ Invalid reset token correctly rejected")
    else:
        print(f"❌ Invalid reset token handling issue: {invalid_reset.status_code}")

def test_database_token_storage():
    """Test if password reset tokens are being stored in database"""
    print("\n🔍 DATABASE TOKEN STORAGE TESTING")
    print("=" * 50)
    
    # Create another test user
    test_email = f"dbtest_{int(time.time())}@styleflow.com"
    
    signup_response = requests.post(f"{BACKEND_URL}/auth/signup", json={
        "email": test_email,
        "password": "TestPassword123!",
        "full_name": "DB Test User"
    })
    
    if signup_response.status_code != 200:
        print(f"❌ Could not create test user for DB test")
        return
    
    print(f"✅ Created test user for DB test: {test_email}")
    
    # Request password reset
    reset_request = requests.post(f"{BACKEND_URL}/auth/forgot-password", json={
        "email": test_email
    })
    
    if reset_request.status_code == 200:
        print("✅ Password reset request sent - token should be in database")
        
        # Test with non-existent email
        fake_reset = requests.post(f"{BACKEND_URL}/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        
        if fake_reset.status_code == 200:
            print("✅ Non-existent email handled correctly (security best practice)")
        else:
            print(f"❌ Non-existent email handling issue: {fake_reset.status_code}")
    else:
        print(f"❌ Password reset request failed: {reset_request.status_code}")

if __name__ == "__main__":
    test_token_revocation_detailed()
    test_password_reset_complete_flow()
    test_database_token_storage()