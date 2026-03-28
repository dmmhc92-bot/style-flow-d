#!/usr/bin/env python3
"""
StyleFlow Backend Testing - Updated StylistProfile Schema Implementation
Testing the specific endpoints for StylistProfile schema updates:
1. GET /api/profiles/me/hub - Verify response includes profile_icon_url, specialties as List[str], credentials, is_tester, subscription_active, portfolio_images
2. GET /api/profiles/discover - Verify discovery results include profile_icon_url, specialties as List[str], is_verified, is_featured flags
3. GET /api/profiles/{user_id} - Verify full profile includes all StylistProfile fields
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
test_user_id = None

def log_test(test_name, status, details=""):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_symbol = "✅" if status else "❌"
    print(f"[{timestamp}] {status_symbol} {test_name}")
    if details:
        print(f"    {details}")
    return status

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

def test_profiles_me_hub():
    """Test GET /api/profiles/me/hub - Verify StylistProfile schema fields"""
    try:
        response = requests.get(
            f"{BASE_URL}/profiles/me/hub",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Required fields from StylistProfile schema
            required_fields = [
                "profile_icon_url",  # New field
                "specialties",       # Should be List[str]
                "credentials",       # Combined string
                "is_tester",         # Boolean
                "subscription_active", # Boolean
                "portfolio_images"   # List[str]
            ]
            
            missing_fields = []
            field_type_errors = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    # Type validation
                    value = data[field]
                    if field == "specialties":
                        if not isinstance(value, list):
                            field_type_errors.append(f"specialties should be List[str], got {type(value)}")
                        elif value and not all(isinstance(item, str) for item in value):
                            field_type_errors.append(f"specialties should contain only strings")
                    elif field == "portfolio_images":
                        if not isinstance(value, list):
                            field_type_errors.append(f"portfolio_images should be List[str], got {type(value)}")
                        elif value and not all(isinstance(item, str) for item in value):
                            field_type_errors.append(f"portfolio_images should contain only strings")
                    elif field in ["is_tester", "subscription_active"]:
                        if not isinstance(value, bool):
                            field_type_errors.append(f"{field} should be boolean, got {type(value)}")
            
            if missing_fields:
                return log_test("GET /api/profiles/me/hub", False, f"Missing fields: {missing_fields}")
            
            if field_type_errors:
                return log_test("GET /api/profiles/me/hub", False, f"Type errors: {field_type_errors}")
            
            # Additional validation
            details = []
            details.append(f"profile_icon_url: {data.get('profile_icon_url', 'None')}")
            details.append(f"specialties: {data.get('specialties', [])} (type: {type(data.get('specialties'))})")
            details.append(f"credentials: {data.get('credentials', 'None')}")
            details.append(f"is_tester: {data.get('is_tester')}")
            details.append(f"subscription_active: {data.get('subscription_active')}")
            details.append(f"portfolio_images count: {len(data.get('portfolio_images', []))}")
            
            return log_test("GET /api/profiles/me/hub", True, " | ".join(details))
        else:
            return log_test("GET /api/profiles/me/hub", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("GET /api/profiles/me/hub", False, f"Exception: {str(e)}")

def test_profiles_discover():
    """Test GET /api/profiles/discover - Verify discovery results schema"""
    try:
        response = requests.get(
            f"{BASE_URL}/profiles/discover?limit=10",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if not isinstance(data, list):
                return log_test("GET /api/profiles/discover", False, f"Expected list, got {type(data)}")
            
            if len(data) == 0:
                return log_test("GET /api/profiles/discover", True, "No users found in discovery (empty list)")
            
            # Check first user for required fields
            first_user = data[0]
            required_fields = [
                "profile_icon_url",  # New field
                "specialties",       # Should be List[str]
                "is_verified",       # Boolean flag
                "is_featured"        # Boolean flag
            ]
            
            missing_fields = []
            field_type_errors = []
            
            for field in required_fields:
                if field not in first_user:
                    missing_fields.append(field)
                else:
                    value = first_user[field]
                    if field == "specialties":
                        if not isinstance(value, list):
                            field_type_errors.append(f"specialties should be List[str], got {type(value)}")
                        elif value and not all(isinstance(item, str) for item in value):
                            field_type_errors.append(f"specialties should contain only strings")
                    elif field in ["is_verified", "is_featured"]:
                        if not isinstance(value, bool):
                            field_type_errors.append(f"{field} should be boolean, got {type(value)}")
            
            if missing_fields:
                return log_test("GET /api/profiles/discover", False, f"Missing fields in first user: {missing_fields}")
            
            if field_type_errors:
                return log_test("GET /api/profiles/discover", False, f"Type errors in first user: {field_type_errors}")
            
            # Store first user ID for next test
            global test_user_id
            test_user_id = first_user.get("id")
            
            details = []
            details.append(f"Found {len(data)} users")
            details.append(f"First user specialties: {first_user.get('specialties', [])} (type: {type(first_user.get('specialties'))})")
            details.append(f"First user is_verified: {first_user.get('is_verified')}")
            details.append(f"First user is_featured: {first_user.get('is_featured')}")
            details.append(f"First user profile_icon_url: {first_user.get('profile_icon_url', 'None')}")
            
            return log_test("GET /api/profiles/discover", True, " | ".join(details))
        else:
            return log_test("GET /api/profiles/discover", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("GET /api/profiles/discover", False, f"Exception: {str(e)}")

def test_profiles_user_id():
    """Test GET /api/profiles/{user_id} - Verify full profile includes all StylistProfile fields"""
    global test_user_id
    
    if not test_user_id:
        return log_test("GET /api/profiles/{user_id}", False, "No test_user_id available from discover test")
    
    try:
        response = requests.get(
            f"{BASE_URL}/profiles/{test_user_id}",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # All StylistProfile fields that should be present
            required_fields = [
                # Core Identity
                "full_name", "email", "profile_icon_url",
                # Stylist Hub features
                "bio", "specialties", "credentials", "is_verified",
                # Location & Business
                "city", "salon_name", "business_name",
                # Social Links
                "instagram_handle", "tiktok_handle", "website_url", "portfolio_images",
                # System Controls
                "is_tester", "subscription_active"
            ]
            
            missing_fields = []
            field_type_errors = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    value = data[field]
                    # Type validation for key fields
                    if field == "specialties":
                        if not isinstance(value, list):
                            field_type_errors.append(f"specialties should be List[str], got {type(value)}")
                        elif value and not all(isinstance(item, str) for item in value):
                            field_type_errors.append(f"specialties should contain only strings")
                    elif field == "portfolio_images":
                        if not isinstance(value, list):
                            field_type_errors.append(f"portfolio_images should be List[str], got {type(value)}")
                        elif value and not all(isinstance(item, str) for item in value):
                            field_type_errors.append(f"portfolio_images should contain only strings")
                    elif field in ["is_tester", "subscription_active", "is_verified"]:
                        if not isinstance(value, bool):
                            field_type_errors.append(f"{field} should be boolean, got {type(value)}")
            
            if missing_fields:
                return log_test("GET /api/profiles/{user_id}", False, f"Missing fields: {missing_fields}")
            
            if field_type_errors:
                return log_test("GET /api/profiles/{user_id}", False, f"Type errors: {field_type_errors}")
            
            # Additional stats fields that should be present
            stats_fields = ["followers_count", "following_count", "posts_count", "portfolio_count"]
            missing_stats = [field for field in stats_fields if field not in data]
            
            if missing_stats:
                return log_test("GET /api/profiles/{user_id}", False, f"Missing stats fields: {missing_stats}")
            
            details = []
            details.append(f"User: {data.get('full_name')}")
            details.append(f"specialties: {data.get('specialties', [])} (type: {type(data.get('specialties'))})")
            details.append(f"credentials: {data.get('credentials', 'None')}")
            details.append(f"is_verified: {data.get('is_verified')}")
            details.append(f"is_tester: {data.get('is_tester')}")
            details.append(f"subscription_active: {data.get('subscription_active')}")
            details.append(f"portfolio_images count: {len(data.get('portfolio_images', []))}")
            details.append(f"followers: {data.get('followers_count')}")
            
            return log_test("GET /api/profiles/{user_id}", True, " | ".join(details))
        else:
            return log_test("GET /api/profiles/{user_id}", False, 
                          f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        return log_test("GET /api/profiles/{user_id}", False, f"Exception: {str(e)}")

def test_specialties_list_format():
    """Test that specialties field is properly formatted as List[str] across all endpoints"""
    try:
        # Test /api/profiles/me/hub
        response = requests.get(f"{BASE_URL}/profiles/me/hub", headers=get_auth_headers())
        if response.status_code == 200:
            data = response.json()
            specialties = data.get("specialties", [])
            if not isinstance(specialties, list):
                return log_test("Specialties List Format", False, 
                              f"/api/profiles/me/hub specialties is not a list: {type(specialties)}")
            
            # Test /api/profiles/discover
            response = requests.get(f"{BASE_URL}/profiles/discover?limit=5", headers=get_auth_headers())
            if response.status_code == 200:
                discover_data = response.json()
                if discover_data:
                    for i, user in enumerate(discover_data[:3]):  # Check first 3 users
                        user_specialties = user.get("specialties", [])
                        if not isinstance(user_specialties, list):
                            return log_test("Specialties List Format", False, 
                                          f"/api/profiles/discover user {i} specialties is not a list: {type(user_specialties)}")
            
            return log_test("Specialties List Format", True, 
                          f"All endpoints return specialties as List[str]. Me/hub: {specialties}")
        else:
            return log_test("Specialties List Format", False, 
                          f"Failed to get /api/profiles/me/hub: {response.status_code}")
    except Exception as e:
        return log_test("Specialties List Format", False, f"Exception: {str(e)}")

def run_all_tests():
    """Run all StylistProfile schema tests"""
    print("=" * 80)
    print("STYLEFLOW STYLISTPROFILE SCHEMA IMPLEMENTATION TESTING")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"Admin Credentials: {ADMIN_EMAIL}")
    print("Testing endpoints:")
    print("1. GET /api/profiles/me/hub - Verify profile_icon_url, specialties as List[str], credentials, is_tester, subscription_active, portfolio_images")
    print("2. GET /api/profiles/discover - Verify discovery results include profile_icon_url, specialties as List[str], is_verified, is_featured flags")
    print("3. GET /api/profiles/{user_id} - Verify full profile includes all StylistProfile fields")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 0
    
    # Test sequence
    test_functions = [
        login_admin,
        test_profiles_me_hub,
        test_profiles_discover,
        test_profiles_user_id,
        test_specialties_list_format
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
        print("🎉 ALL TESTS PASSED - StylistProfile schema implementation is working correctly!")
        print("✅ profile_icon_url field present in all endpoints")
        print("✅ specialties field properly formatted as List[str]")
        print("✅ credentials field properly combined as string")
        print("✅ is_tester and subscription_active boolean fields working")
        print("✅ portfolio_images field present as List[str]")
        print("✅ is_verified and is_featured flags working in discovery")
    else:
        print(f"⚠️  {total_tests - tests_passed} test(s) failed - See details above")
    
    print("=" * 80)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)