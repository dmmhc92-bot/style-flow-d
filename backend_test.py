#!/usr/bin/env python3
"""
StyleFlow Backend Testing - Avatar and Portfolio Upload Endpoints
Testing the UPDATED avatar and portfolio upload endpoints with validation
"""

import requests
import json
import base64
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

# Test credentials
admin_token = None
portfolio_id = None

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status else "❌"
    print(f"[{timestamp}] {status_symbol} {test_name}")
    if details:
        print(f"    {details}")
    return status

def create_small_test_image():
    """Create a small valid base64 JPG image for testing"""
    # Create a simple 10x10 red JPEG image
    try:
        from PIL import Image
        import io
        import base64
        
        # Create a small 10x10 red image
        img = Image.new('RGB', (10, 10), color='red')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    except ImportError:
        # Fallback to a known working small JPEG
        return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"

def create_large_test_image():
    """Create a large base64 image that exceeds 5MB limit"""
    # Create a valid base64 string that will decode to more than 5MB
    # We'll create a string that when base64 decoded will be > 5MB
    # Base64 encoding increases size by ~33%, so we need raw data > 5MB
    import base64
    large_binary_data = b'A' * (6 * 1024 * 1024)  # 6MB of binary data
    large_base64 = base64.b64encode(large_binary_data).decode('utf-8')
    return f"data:image/jpeg;base64,{large_base64}"

def login_admin():
    """Login as admin and get JWT token"""
    global admin_token
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get("token")  # The endpoint returns "token" not "access_token"
            if admin_token:
                return log_test("Admin Login", True, f"Token obtained: {admin_token[:20]}...")
            else:
                return log_test("Admin Login", False, f"No token in response: {data}")
        else:
            return log_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Admin Login", False, f"Exception: {str(e)}")

def get_auth_headers():
    """Get authorization headers with JWT token"""
    if not admin_token:
        return {}
    return {"Authorization": f"Bearer {admin_token}"}

def test_avatar_upload_valid():
    """Test POST /api/profiles/avatar with valid JPG base64 image"""
    try:
        small_image = create_small_test_image()
        
        response = requests.post(
            f"{BASE_URL}/profiles/avatar",
            json={"image_base64": small_image},
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["avatar_url", "storage_type", "success"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return log_test("Avatar Upload (Valid)", False, f"Missing fields: {missing_fields}")
            
            if data.get("success") != True:
                return log_test("Avatar Upload (Valid)", False, f"Success field is not True: {data.get('success')}")
            
            return log_test("Avatar Upload (Valid)", True, 
                          f"Avatar URL: {data.get('avatar_url')[:50]}..., Storage: {data.get('storage_type')}")
        else:
            return log_test("Avatar Upload (Valid)", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Avatar Upload (Valid)", False, f"Exception: {str(e)}")

def test_avatar_upload_empty():
    """Test POST /api/profiles/avatar with empty image (should fail 422)"""
    try:
        response = requests.post(
            f"{BASE_URL}/profiles/avatar",
            json={"image_base64": ""},
            headers=get_auth_headers()
        )
        
        if response.status_code == 422:
            return log_test("Avatar Upload (Empty Image)", True, "Correctly rejected empty image with 422")
        else:
            return log_test("Avatar Upload (Empty Image)", False, 
                          f"Expected 422, got {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Avatar Upload (Empty Image)", False, f"Exception: {str(e)}")

def test_avatar_upload_size_validation():
    """Test POST /api/profiles/avatar size validation (5MB max)"""
    try:
        large_image = create_large_test_image()
        
        response = requests.post(
            f"{BASE_URL}/profiles/avatar",
            json={"image_base64": large_image},
            headers=get_auth_headers()
        )
        
        if response.status_code == 422:
            error_detail = response.json().get("detail", [])
            if isinstance(error_detail, list) and len(error_detail) > 0:
                error_msg = error_detail[0].get("msg", "")
                if "too large" in error_msg.lower() or "5mb" in error_msg.lower():
                    return log_test("Avatar Upload (Size Validation)", True, 
                                  f"Correctly rejected large image: {error_msg}")
                else:
                    return log_test("Avatar Upload (Size Validation)", False, 
                                  f"Got 422 but wrong error message: {error_msg}")
            else:
                return log_test("Avatar Upload (Size Validation)", False, 
                              f"Got 422 but unexpected error format: {error_detail}")
        else:
            return log_test("Avatar Upload (Size Validation)", False, 
                          f"Expected 422, got {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Avatar Upload (Size Validation)", False, f"Exception: {str(e)}")

def test_portfolio_upload():
    """Test POST /api/profiles/portfolio - Portfolio image upload"""
    global portfolio_id
    
    try:
        small_image = create_small_test_image()
        
        response = requests.post(
            f"{BASE_URL}/profiles/portfolio",
            json={
                "image_base64": small_image,
                "caption": "Test portfolio image upload"
            },
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["portfolio_id", "image_url", "success"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return log_test("Portfolio Upload", False, f"Missing fields: {missing_fields}")
            
            if data.get("success") != True:
                return log_test("Portfolio Upload", False, f"Success field is not True: {data.get('success')}")
            
            portfolio_id = data.get("portfolio_id")
            return log_test("Portfolio Upload", True, 
                          f"Portfolio ID: {portfolio_id}, Image URL: {data.get('image_url')[:50]}...")
        else:
            return log_test("Portfolio Upload", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Portfolio Upload", False, f"Exception: {str(e)}")

def test_portfolio_delete():
    """Test DELETE /api/profiles/portfolio/{id} - Delete portfolio"""
    global portfolio_id
    
    if not portfolio_id:
        return log_test("Portfolio Delete", False, "No portfolio_id available from previous test")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/profiles/portfolio/{portfolio_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") == True:
                return log_test("Portfolio Delete", True, f"Successfully deleted portfolio item {portfolio_id}")
            else:
                return log_test("Portfolio Delete", False, f"Success field is not True: {data}")
        else:
            return log_test("Portfolio Delete", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Portfolio Delete", False, f"Exception: {str(e)}")

def test_profile_me_hub():
    """Test GET /api/profiles/me/hub after avatar upload - Verify user schema updates"""
    try:
        response = requests.get(
            f"{BASE_URL}/profiles/me/hub",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for profile_image_url field (this should be set after avatar upload)
            profile_image_url = data.get("profile_photo")  # The endpoint returns profile_photo
            if not profile_image_url:
                return log_test("Profile Me Hub (Schema Check)", False, 
                              "profile_photo field is missing or empty")
            
            # Check for portfolio_images array existence
            portfolio = data.get("portfolio", [])
            if not isinstance(portfolio, list):
                return log_test("Profile Me Hub (Schema Check)", False, 
                              "portfolio field is not an array")
            
            # Check other required fields
            required_fields = ["id", "full_name", "followers_count", "following_count", "posts_count", "portfolio_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return log_test("Profile Me Hub (Schema Check)", False, f"Missing fields: {missing_fields}")
            
            return log_test("Profile Me Hub (Schema Check)", True, 
                          f"Profile image URL set: {profile_image_url[:50]}..., Portfolio count: {data.get('portfolio_count')}")
        else:
            return log_test("Profile Me Hub (Schema Check)", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("Profile Me Hub (Schema Check)", False, f"Exception: {str(e)}")

def run_all_tests():
    """Run all avatar and portfolio upload tests"""
    print("=" * 80)
    print("STYLEFLOW AVATAR & PORTFOLIO UPLOAD ENDPOINTS TESTING")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Admin Credentials: {ADMIN_EMAIL}")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 0
    
    # Test sequence
    test_functions = [
        login_admin,
        test_avatar_upload_valid,
        test_avatar_upload_empty,
        test_avatar_upload_size_validation,
        test_portfolio_upload,
        test_portfolio_delete,
        test_profile_me_hub
    ]
    
    for test_func in test_functions:
        total_tests += 1
        if test_func():
            tests_passed += 1
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 80)
    print(f"TESTING SUMMARY: {tests_passed}/{total_tests} tests passed")
    success_rate = (tests_passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - Avatar and Portfolio Upload endpoints are working correctly!")
    else:
        print(f"⚠️  {total_tests - tests_passed} test(s) failed - See details above")
    
    print("=" * 80)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)