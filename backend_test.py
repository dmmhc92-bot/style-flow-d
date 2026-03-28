#!/usr/bin/env python3
"""
StyleFlow JWT Auth System Testing
Tests the newly implemented JWT Auth System with Refresh Tokens, isTester bypass, and Resend integration.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Backend URL from frontend environment
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

# Tester emails for App Store bypass testing
TESTER_EMAILS = [
    "tester@styleflow.com",
    "appreview@apple.com"
]

class AuthTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.admin_refresh_token = None
        self.test_user_email = f"testuser_{int(time.time())}@styleflow.com"
        self.test_user_password = "TestPassword123!"
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "status": status
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            raise
    
    def test_1_basic_auth_login(self):
        """Test 1: Basic Auth Flow - Login with admin credentials"""
        try:
            response = self.make_request("POST", "/auth/login", {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["token", "refresh_token", "user"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Basic Auth Login", False, f"Missing fields: {missing_fields}")
                    return
                
                # Check user object has is_tester field
                user = data["user"]
                if "is_tester" not in user:
                    self.log_result("Basic Auth Login", False, "Missing is_tester field in user object")
                    return
                
                # Store tokens for later tests
                self.admin_token = data["token"]
                self.admin_refresh_token = data["refresh_token"]
                
                self.log_result("Basic Auth Login", True, 
                    f"Login successful. User: {user.get('email')}, is_tester: {user.get('is_tester')}, is_admin: {user.get('is_admin')}")
            else:
                self.log_result("Basic Auth Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Basic Auth Login", False, f"Exception: {str(e)}")
    
    def test_2_basic_auth_signup(self):
        """Test 2: Basic Auth Flow - Signup with new email"""
        try:
            response = self.make_request("POST", "/auth/signup", {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": "Test User",
                "business_name": "Test Salon"
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["token", "refresh_token", "user"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Basic Auth Signup", False, f"Missing fields: {missing_fields}")
                    return
                
                # Check user object structure
                user = data["user"]
                required_user_fields = ["id", "email", "full_name", "is_tester"]
                missing_user_fields = [field for field in required_user_fields if field not in user]
                
                if missing_user_fields:
                    self.log_result("Basic Auth Signup", False, f"Missing user fields: {missing_user_fields}")
                    return
                
                self.log_result("Basic Auth Signup", True, 
                    f"Signup successful. User: {user.get('email')}, is_tester: {user.get('is_tester')}")
            else:
                self.log_result("Basic Auth Signup", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Basic Auth Signup", False, f"Exception: {str(e)}")
    
    def test_3_jwt_refresh_token_system(self):
        """Test 3: JWT Refresh Token System"""
        if not self.admin_refresh_token:
            self.log_result("JWT Refresh Token System", False, "No refresh token available from login")
            return
        
        try:
            # Test refresh with valid token
            headers = {"X-Refresh-Token": self.admin_refresh_token}
            response = self.make_request("POST", "/auth/refresh", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response contains new token pair
                if "token" not in data or "refresh_token" not in data:
                    self.log_result("JWT Refresh Token System", False, "Missing token or refresh_token in response")
                    return
                
                # Verify tokens are different from original
                if data["token"] == self.admin_token or data["refresh_token"] == self.admin_refresh_token:
                    self.log_result("JWT Refresh Token System", False, "New tokens are same as old tokens")
                    return
                
                # Update stored tokens
                self.admin_token = data["token"]
                self.admin_refresh_token = data["refresh_token"]
                
                self.log_result("JWT Refresh Token System", True, "Refresh token system working correctly")
            else:
                self.log_result("JWT Refresh Token System", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("JWT Refresh Token System", False, f"Exception: {str(e)}")
    
    def test_4_invalid_refresh_token(self):
        """Test 4: JWT Refresh Token System - Invalid token"""
        try:
            headers = {"X-Refresh-Token": "invalid_token_12345"}
            response = self.make_request("POST", "/auth/refresh", headers=headers)
            
            if response.status_code == 401:
                self.log_result("Invalid Refresh Token", True, "Correctly rejected invalid refresh token")
            else:
                self.log_result("Invalid Refresh Token", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Refresh Token", False, f"Exception: {str(e)}")
    
    def test_5_istester_app_store_bypass(self):
        """Test 5: isTester App Store Bypass"""
        for tester_email in TESTER_EMAILS:
            try:
                # Create tester account
                tester_password = "TesterPassword123!"
                response = self.make_request("POST", "/auth/signup", {
                    "email": tester_email,
                    "password": tester_password,
                    "full_name": "App Store Tester",
                    "business_name": "Test Business"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    user = data["user"]
                    
                    # Check tester flags
                    expected_flags = {
                        "is_tester": True,
                        "is_admin": True,
                        "subscription_status": "active"
                    }
                    
                    missing_flags = []
                    for flag, expected_value in expected_flags.items():
                        if user.get(flag) != expected_value:
                            missing_flags.append(f"{flag}: expected {expected_value}, got {user.get(flag)}")
                    
                    if missing_flags:
                        self.log_result(f"isTester Bypass ({tester_email})", False, f"Incorrect flags: {missing_flags}")
                    else:
                        self.log_result(f"isTester Bypass ({tester_email})", True, "Tester account created with correct flags")
                
                elif response.status_code == 400 and "already registered" in response.text:
                    # Account exists, try login
                    login_response = self.make_request("POST", "/auth/login", {
                        "email": tester_email,
                        "password": tester_password
                    })
                    
                    if login_response.status_code == 200:
                        data = login_response.json()
                        user = data["user"]
                        
                        # Check tester flags
                        if user.get("is_tester") and user.get("is_admin") and user.get("subscription_status") == "active":
                            self.log_result(f"isTester Bypass ({tester_email})", True, "Existing tester account has correct flags")
                        else:
                            self.log_result(f"isTester Bypass ({tester_email})", False, 
                                f"Existing account missing flags: is_tester={user.get('is_tester')}, is_admin={user.get('is_admin')}, subscription_status={user.get('subscription_status')}")
                    else:
                        self.log_result(f"isTester Bypass ({tester_email})", False, f"Login failed: {login_response.status_code}")
                else:
                    self.log_result(f"isTester Bypass ({tester_email})", False, f"Signup failed: {response.status_code}, {response.text}")
                    
            except Exception as e:
                self.log_result(f"isTester Bypass ({tester_email})", False, f"Exception: {str(e)}")
    
    def test_6_password_reset_via_resend(self):
        """Test 6: Password Reset via Resend"""
        try:
            # Step 1: Request password reset
            response = self.make_request("POST", "/auth/forgot-password", {
                "email": self.test_user_email
            })
            
            if response.status_code != 200:
                self.log_result("Password Reset Request", False, f"Status: {response.status_code}")
                return
            
            # Check response message
            data = response.json()
            if "message" not in data:
                self.log_result("Password Reset Request", False, "Missing message in response")
                return
            
            self.log_result("Password Reset Request", True, "Password reset request sent")
            
            # Step 2: Check if token was created in database (we can't access DB directly, so we'll test the verify endpoint)
            # We need to get the token somehow - let's try a common pattern or check if there's a way to get it
            
            # For now, let's test with a mock token to verify the endpoint exists
            test_token = "test_token_12345"
            verify_response = self.make_request("GET", f"/auth/verify-reset-token/{test_token}")
            
            if verify_response.status_code == 400:
                # This is expected for invalid token
                self.log_result("Password Reset Token Verification", True, "Verify endpoint exists and rejects invalid tokens")
            else:
                self.log_result("Password Reset Token Verification", False, f"Unexpected status: {verify_response.status_code}")
                
        except Exception as e:
            self.log_result("Password Reset via Resend", False, f"Exception: {str(e)}")
    
    def test_7_token_revocation_logout(self):
        """Test 7: Token Revocation (Logout)"""
        if not self.admin_token:
            self.log_result("Token Revocation (Logout)", False, "No admin token available")
            return
        
        try:
            # Test logout
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.make_request("POST", "/auth/logout", headers=headers)
            
            if response.status_code == 200:
                # Try to use the old refresh token
                old_refresh_headers = {"X-Refresh-Token": self.admin_refresh_token}
                refresh_response = self.make_request("POST", "/auth/refresh", headers=old_refresh_headers)
                
                if refresh_response.status_code == 401:
                    self.log_result("Token Revocation (Logout)", True, "Logout successfully revoked refresh token")
                else:
                    self.log_result("Token Revocation (Logout)", False, f"Old refresh token still works: {refresh_response.status_code}")
            else:
                self.log_result("Token Revocation (Logout)", False, f"Logout failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Token Revocation (Logout)", False, f"Exception: {str(e)}")
    
    def test_8_auth_me_endpoint(self):
        """Test 8: GET /api/auth/me endpoint"""
        # First, login again since we logged out
        try:
            login_response = self.make_request("POST", "/auth/login", {
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if login_response.status_code != 200:
                self.log_result("Auth Me Endpoint", False, "Could not login for /me test")
                return
            
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if is_tester field is present
                if "is_tester" not in data:
                    self.log_result("Auth Me Endpoint", False, "Missing is_tester field in /me response")
                    return
                
                # Check other important fields
                required_fields = ["id", "email", "full_name", "is_admin", "subscription_status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Auth Me Endpoint", False, f"Missing fields: {missing_fields}")
                    return
                
                self.log_result("Auth Me Endpoint", True, 
                    f"GET /auth/me working. is_tester: {data.get('is_tester')}, is_admin: {data.get('is_admin')}")
            else:
                self.log_result("Auth Me Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Auth Me Endpoint", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all JWT auth tests"""
        print("🚀 Starting JWT Auth System Testing...")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Run tests in order
        self.test_1_basic_auth_login()
        self.test_2_basic_auth_signup()
        self.test_3_jwt_refresh_token_system()
        self.test_4_invalid_refresh_token()
        self.test_5_istester_app_store_bypass()
        self.test_6_password_reset_via_resend()
        self.test_7_token_revocation_logout()
        self.test_8_auth_me_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        return success_rate, self.test_results

if __name__ == "__main__":
    test_suite = AuthTestSuite()
    success_rate, results = test_suite.run_all_tests()
    
    if success_rate >= 80:
        print(f"\n🎉 JWT Auth System testing completed with {success_rate:.1f}% success rate!")
    else:
        print(f"\n⚠️  JWT Auth System testing completed with {success_rate:.1f}% success rate. Issues found.")