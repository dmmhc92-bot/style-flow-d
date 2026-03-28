#!/usr/bin/env python3
"""
SPECIFIC Token Revocation Bug Fix Test
Tests the exact scenario from the review request:
1. POST /api/auth/login with admin@styleflow.com / Admin1234! - Get tokens
2. POST /api/auth/logout with the access token (Authorization header)
3. POST /api/auth/refresh with the OLD refresh token (X-Refresh-Token header)
4. Verify step 3 returns 401 "Refresh token has been revoked"
"""

import requests
import json

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

def main():
    print("🔐 SPECIFIC TOKEN REVOCATION BUG FIX TEST")
    print("=" * 60)
    print("Testing the exact fix in /app/backend/routes/auth.py line 205:")
    print("Changed from: if stored_jti and token_jti != stored_jti:")
    print("Changed to:   if not stored_jti or token_jti != stored_jti:")
    print("=" * 60)
    
    # Step 1: Login to get tokens
    print("\n1️⃣ POST /api/auth/login with admin@styleflow.com / Admin1234!")
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"   Status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"   ❌ FAILED: {login_response.text}")
        return False
    
    login_result = login_response.json()
    access_token = login_result.get("token")
    refresh_token = login_result.get("refresh_token")
    
    print(f"   ✅ SUCCESS: Got tokens")
    print(f"   Access Token: {access_token[:30]}...")
    print(f"   Refresh Token: {refresh_token[:30]}...")
    
    # Step 2: Logout with access token
    print("\n2️⃣ POST /api/auth/logout with access token (Authorization header)")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    logout_response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    print(f"   Status: {logout_response.status_code}")
    
    if logout_response.status_code not in [200, 204]:
        print(f"   ❌ FAILED: {logout_response.text}")
        return False
    
    print(f"   ✅ SUCCESS: Logout completed")
    
    # Step 3: Try to refresh with OLD refresh token
    print("\n3️⃣ POST /api/auth/refresh with OLD refresh token (X-Refresh-Token header)")
    refresh_headers = {"X-Refresh-Token": refresh_token}
    
    refresh_response = requests.post(f"{BASE_URL}/auth/refresh", headers=refresh_headers)
    print(f"   Status: {refresh_response.status_code}")
    
    # Step 4: Verify returns 401 "Refresh token has been revoked"
    print("\n4️⃣ Verify step 3 returns 401 'Refresh token has been revoked'")
    
    if refresh_response.status_code == 401:
        try:
            response_data = refresh_response.json()
            detail = response_data.get("detail", "")
            print(f"   Response: {response_data}")
            
            if "revoked" in detail.lower():
                print(f"   ✅ SUCCESS: Correct error message - '{detail}'")
                print(f"   ✅ BUG FIX CONFIRMED WORKING!")
                return True
            else:
                print(f"   ❌ FAILED: Wrong error message - '{detail}'")
                return False
        except:
            print(f"   ❌ FAILED: Invalid JSON response - {refresh_response.text}")
            return False
    else:
        print(f"   ❌ CRITICAL FAILURE: Expected 401, got {refresh_response.status_code}")
        print(f"   Response: {refresh_response.text}")
        print(f"   ❌ BUG FIX NOT WORKING - REFRESH TOKEN STILL VALID AFTER LOGOUT!")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULT")
    print("=" * 60)
    
    if success:
        print("✅ TOKEN REVOCATION BUG FIX TEST PASSED")
        print("✅ The condition change in auth.py line 205-206 is working correctly")
        print("✅ 'if not stored_jti or token_jti != stored_jti:' properly rejects tokens after logout")
        print("✅ Refresh tokens are correctly revoked when user logs out")
    else:
        print("❌ TOKEN REVOCATION BUG FIX TEST FAILED")
        print("❌ The bug fix may not be working properly")
        print("❌ Refresh tokens may still be valid after logout")
    
    exit(0 if success else 1)