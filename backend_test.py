#!/usr/bin/env python3
"""
CLOUDINARY PRODUCTION SETUP VERIFICATION TEST
==============================================

This test verifies the Cloudinary production configuration and upload functionality
as requested in the review request.

Test Requirements:
1. Login with admin@styleflow.com / Admin1234!
2. POST /api/profiles/avatar with base64 image - verify Cloudinary storage
3. POST /api/profiles/portfolio with test image and caption
4. Verify production Cloudinary config (Cloud Name: dqq3nmkgd, API Key: 51465675, Asset Folder: styleflow_uploads)
"""

import requests
import json
import base64
from datetime import datetime
import os

# Backend URL from frontend/.env
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials from review request
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

# Expected Cloudinary production config
EXPECTED_CLOUD_NAME = "dqq3nmkgd"
EXPECTED_API_KEY = "514656752899134"
EXPECTED_ASSET_FOLDER = "styleflow_uploads"

def create_test_base64_image():
    """Create a small test base64 image (100x100 JPG)"""
    # This is a minimal 100x100 red square JPG in base64
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="

def test_login():
    """Test 1: Login with admin credentials"""
    print("🔐 TEST 1: Admin Login")
    print(f"   Attempting login with {ADMIN_EMAIL}")
    
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token") or data.get("access_token")
            if token:
                print("   ✅ Login successful - JWT token received")
                return token
            else:
                print("   ❌ Login failed - No token in response")
                print(f"   Response: {data}")
                return None
        else:
            print(f"   ❌ Login failed - {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None

def test_avatar_upload(token):
    """Test 2: Avatar upload with Cloudinary verification"""
    print("\n📸 TEST 2: Avatar Upload (Cloudinary Production)")
    
    if not token:
        print("   ❌ Skipped - No valid token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    test_image = create_test_base64_image()
    
    upload_data = {
        "image_base64": test_image
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/profiles/avatar", json=upload_data, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Verify Cloudinary storage
            storage_type = data.get("storage_type")
            avatar_url = data.get("avatar_url", "")
            
            print(f"   Storage Type: {storage_type}")
            print(f"   Avatar URL: {avatar_url}")
            
            # Check if using Cloudinary (not base64 fallback)
            if storage_type == "cloudinary":
                print("   ✅ Using Cloudinary storage (not base64 fallback)")
                
                # Verify cloud name in URL
                if EXPECTED_CLOUD_NAME in avatar_url:
                    print(f"   ✅ Cloud Name verified: {EXPECTED_CLOUD_NAME} found in URL")
                else:
                    print(f"   ❌ Cloud Name mismatch: {EXPECTED_CLOUD_NAME} not found in URL")
                    return False
                
                # Verify asset folder in URL
                if f"{EXPECTED_ASSET_FOLDER}/avatars" in avatar_url:
                    print(f"   ✅ Asset Folder verified: {EXPECTED_ASSET_FOLDER}/avatars found in URL")
                else:
                    print(f"   ❌ Asset Folder mismatch: {EXPECTED_ASSET_FOLDER}/avatars not found in URL")
                    return False
                
                print("   ✅ Avatar upload with Cloudinary production config VERIFIED")
                return True
            else:
                print(f"   ❌ Expected Cloudinary storage, got: {storage_type}")
                return False
        else:
            print(f"   ❌ Avatar upload failed - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Avatar upload error: {e}")
        return False

def test_portfolio_upload(token):
    """Test 3: Portfolio upload with Cloudinary verification"""
    print("\n🎨 TEST 3: Portfolio Upload (Cloudinary Production)")
    
    if not token:
        print("   ❌ Skipped - No valid token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    test_image = create_test_base64_image()
    
    upload_data = {
        "image_base64": test_image,
        "caption": "Test portfolio image for Cloudinary production verification"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/profiles/portfolio", json=upload_data, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            image_url = data.get("image_url", "")
            portfolio_id = data.get("portfolio_id")
            
            print(f"   Portfolio ID: {portfolio_id}")
            print(f"   Image URL: {image_url}")
            
            # Verify Cloudinary URL structure
            if "res.cloudinary.com" in image_url and EXPECTED_CLOUD_NAME in image_url:
                print("   ✅ Using Cloudinary CDN")
                
                # Verify cloud name in URL
                if EXPECTED_CLOUD_NAME in image_url:
                    print(f"   ✅ Cloud Name verified: {EXPECTED_CLOUD_NAME} found in URL")
                else:
                    print(f"   ❌ Cloud Name mismatch: {EXPECTED_CLOUD_NAME} not found in URL")
                    return False
                
                # Verify portfolio folder in URL
                if f"{EXPECTED_ASSET_FOLDER}/portfolio" in image_url:
                    print(f"   ✅ Portfolio Folder verified: {EXPECTED_ASSET_FOLDER}/portfolio found in URL")
                else:
                    print(f"   ❌ Portfolio Folder mismatch: {EXPECTED_ASSET_FOLDER}/portfolio not found in URL")
                    return False
                
                print("   ✅ Portfolio upload with Cloudinary production config VERIFIED")
                return True
            else:
                print(f"   ❌ Expected Cloudinary URL, got: {image_url}")
                return False
        else:
            print(f"   ❌ Portfolio upload failed - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Portfolio upload error: {e}")
        return False

def verify_cloudinary_config():
    """Test 4: Verify Cloudinary configuration in backend/.env"""
    print("\n⚙️  TEST 4: Cloudinary Configuration Verification")
    
    env_file = "/app/backend/.env"
    
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        # Check Cloud Name
        if f"CLOUDINARY_CLOUD_NAME={EXPECTED_CLOUD_NAME}" in env_content:
            print(f"   ✅ Cloud Name: {EXPECTED_CLOUD_NAME}")
        else:
            print(f"   ❌ Cloud Name mismatch in .env file")
            return False
        
        # Check API Key (partial for security)
        if f"CLOUDINARY_API_KEY={EXPECTED_API_KEY}" in env_content:
            print(f"   ✅ API Key: {EXPECTED_API_KEY}")
        else:
            print(f"   ❌ API Key mismatch in .env file")
            return False
        
        # Check Asset Folder
        if f"CLOUDINARY_ASSET_FOLDER={EXPECTED_ASSET_FOLDER}" in env_content:
            print(f"   ✅ Asset Folder: {EXPECTED_ASSET_FOLDER}")
        else:
            print(f"   ❌ Asset Folder mismatch in .env file")
            return False
        
        print("   ✅ All Cloudinary production config values VERIFIED")
        return True
        
    except Exception as e:
        print(f"   ❌ Config verification error: {e}")
        return False

def main():
    """Run all Cloudinary production setup tests"""
    print("=" * 60)
    print("CLOUDINARY PRODUCTION SETUP VERIFICATION")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test results tracking
    results = []
    
    # Test 1: Login
    token = test_login()
    results.append(("Admin Login", token is not None))
    
    # Test 2: Avatar Upload
    avatar_success = test_avatar_upload(token)
    results.append(("Avatar Upload (Cloudinary)", avatar_success))
    
    # Test 3: Portfolio Upload
    portfolio_success = test_portfolio_upload(token)
    results.append(("Portfolio Upload (Cloudinary)", portfolio_success))
    
    # Test 4: Config Verification
    config_success = verify_cloudinary_config()
    results.append(("Cloudinary Config", config_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Cloudinary production setup is FULLY FUNCTIONAL")
        print("\nVerified:")
        print(f"   • Cloud Name: {EXPECTED_CLOUD_NAME}")
        print(f"   • API Key: {EXPECTED_API_KEY}")
        print(f"   • Asset Folder: {EXPECTED_ASSET_FOLDER}")
        print("   • Avatar uploads using Cloudinary CDN")
        print("   • Portfolio uploads using Cloudinary CDN")
        print("   • Production folder structure (styleflow_uploads/avatars, styleflow_uploads/portfolio)")
    else:
        print(f"\n⚠️  {total-passed} TEST(S) FAILED - Cloudinary production setup needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)