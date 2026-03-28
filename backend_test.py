#!/usr/bin/env python3
"""
Backend Test Suite for StyleFlow - Cloudinary Avatar Upload Integration
Testing Cloudinary CDN configuration and avatar upload functionality
"""

import requests
import json
import base64
from io import BytesIO
from PIL import Image
import sys

# Configuration
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
TEST_CREDENTIALS = {
    "email": "admin@styleflow.com",
    "password": "Admin1234!"
}

def create_test_image_base64():
    """Create a small test JPG image as base64"""
    # Create a small 100x100 red square image
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_data = buffer.getvalue()
    
    # Convert to base64
    img_base64 = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"

def login():
    """Login and get JWT token"""
    print("🔐 Logging in with admin credentials...")
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=TEST_CREDENTIALS)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    token = data.get("token") or data.get("access_token")
    
    if not token:
        print(f"❌ No access token in response: {data}")
        return None
    
    print(f"✅ Login successful")
    return token

def test_cloudinary_avatar_upload(token):
    """Test avatar upload with Cloudinary integration"""
    print("\n🖼️  Testing Cloudinary Avatar Upload Integration...")
    
    # Create test image
    test_image = create_test_image_base64()
    
    # Prepare request
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"image_base64": test_image}
    
    # Make request
    response = requests.post(f"{BACKEND_URL}/profiles/avatar", 
                           headers=headers, 
                           json=payload)
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Avatar upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response Data: {json.dumps(data, indent=2)}")
    
    # Verify response structure
    required_fields = ["success", "avatar_url", "storage_type"]
    for field in required_fields:
        if field not in data:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check if success is True
    if not data.get("success"):
        print(f"❌ Upload not successful: {data}")
        return False
    
    # CRITICAL CHECK: Verify storage_type is "cloudinary" (NOT "base64")
    storage_type = data.get("storage_type")
    if storage_type != "cloudinary":
        print(f"❌ CRITICAL: Expected storage_type 'cloudinary', got '{storage_type}'")
        print("❌ This indicates Cloudinary config is not loading correctly")
        return False
    
    # CRITICAL CHECK: Verify avatar_url starts with Cloudinary CDN URL
    avatar_url = data.get("avatar_url")
    expected_cloudinary_prefix = "https://res.cloudinary.com/dqq3nmkgd/"
    
    if not avatar_url.startswith(expected_cloudinary_prefix):
        print(f"❌ CRITICAL: Avatar URL doesn't start with expected Cloudinary CDN URL")
        print(f"Expected prefix: {expected_cloudinary_prefix}")
        print(f"Actual URL: {avatar_url}")
        return False
    
    print(f"✅ SUCCESS: Cloudinary integration working correctly!")
    print(f"✅ Storage Type: {storage_type}")
    print(f"✅ Avatar URL: {avatar_url}")
    print(f"✅ Cloudinary CDN confirmed with Cloud Name: dqq3nmkgd")
    
    return True

def main():
    """Main test execution"""
    print("=" * 80)
    print("STYLEFLOW CLOUDINARY AVATAR UPLOAD INTEGRATION TEST")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: {TEST_CREDENTIALS['email']}")
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n❌ FAILED: Could not authenticate")
        sys.exit(1)
    
    # Step 2: Test Cloudinary Avatar Upload
    success = test_cloudinary_avatar_upload(token)
    
    # Final Results
    print("\n" + "=" * 80)
    print("CLOUDINARY INTEGRATION TEST RESULTS")
    print("=" * 80)
    
    if success:
        print("✅ PASS: Cloudinary avatar upload integration working correctly")
        print("✅ CONFIRMED: storage_type = 'cloudinary' (NOT 'base64')")
        print("✅ CONFIRMED: avatar_url starts with 'https://res.cloudinary.com/dqq3nmkgd/'")
        print("✅ CONFIRMED: Cloudinary CDN properly configured")
        print("\nCloudinary Configuration Verified:")
        print("- Cloud Name: dqq3nmkgd")
        print("- API Key: 514656752899134")
        print("- CDN URL format working correctly")
    else:
        print("❌ FAIL: Cloudinary integration not working as expected")
        print("❌ Check Cloudinary configuration in backend/.env")
        sys.exit(1)

if __name__ == "__main__":
    main()