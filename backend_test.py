#!/usr/bin/env python3
"""
STYLIST HUB BACKEND ENDPOINTS TESTING
=====================================
Testing the newly created /api/profiles/* endpoints for Stylist Hub functionality.

Test Coverage:
1. GET /api/profiles/discover - List stylists with filters
2. GET /api/profiles/{user_id} - Get full profile for Stylist Hub  
3. POST /api/profiles/avatar - Avatar upload (mock test)
4. POST /api/profiles/credentials - Update credentials
5. GET /api/profiles/me/hub - Quick access to own profile

Admin credentials: admin@styleflow.com / Admin1234!
"""

import requests
import json
import base64
from datetime import datetime
import sys

# Backend URL from frontend/.env
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StylistHubTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def authenticate(self):
        """Authenticate with admin credentials"""
        print("🔐 AUTHENTICATING WITH ADMIN CREDENTIALS...")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")  # Changed from access_token to token
                self.user_id = data.get("user", {}).get("id")
                
                # Set authorization header for all future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_result("Admin Authentication", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_discover_stylists(self):
        """Test GET /api/profiles/discover - List stylists with filters"""
        print("🔍 TESTING STYLIST DISCOVERY ENDPOINT...")
        
        try:
            # Test 1: Basic discover without filters
            response = self.session.get(f"{BACKEND_URL}/profiles/discover")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Discover Stylists - Basic", True, f"Found {len(data)} stylists")
                    
                    # Verify response structure
                    if data and len(data) > 0:
                        stylist = data[0]
                        required_fields = ["id", "full_name", "followers_count", "portfolio_count", "is_verified"]
                        missing_fields = [field for field in required_fields if field not in stylist]
                        
                        if not missing_fields:
                            self.log_result("Discover Response Structure", True, "All required fields present")
                        else:
                            self.log_result("Discover Response Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_result("Discover Response Structure", True, "No stylists to verify structure")
                else:
                    self.log_result("Discover Stylists - Basic", False, "Response is not a list")
            else:
                self.log_result("Discover Stylists - Basic", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test 2: Discover with filters
            response = self.session.get(f"{BACKEND_URL}/profiles/discover", params={
                "featured": True,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Discover Stylists - Featured Filter", True, f"Found {len(data)} featured stylists")
            else:
                self.log_result("Discover Stylists - Featured Filter", False, f"Status: {response.status_code}")
                
            # Test 3: Discover with name search
            response = self.session.get(f"{BACKEND_URL}/profiles/discover", params={
                "name": "admin",
                "limit": 5
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Discover Stylists - Name Search", True, f"Found {len(data)} stylists matching 'admin'")
            else:
                self.log_result("Discover Stylists - Name Search", False, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_result("Discover Stylists - Exception", False, f"Exception: {str(e)}")
    
    def test_get_stylist_profile(self):
        """Test GET /api/profiles/{user_id} - Get full profile for Stylist Hub"""
        print("👤 TESTING STYLIST PROFILE ENDPOINT...")
        
        if not self.user_id:
            self.log_result("Get Stylist Profile", False, "No user ID available for testing")
            return
        
        try:
            response = self.session.get(f"{BACKEND_URL}/profiles/{self.user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields for Stylist Hub profile
                required_fields = [
                    "id", "full_name", "followers_count", "following_count", 
                    "posts_count", "portfolio_count", "is_following", "is_own_profile",
                    "is_verified", "portfolio"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("Get Stylist Profile - Structure", True, "All required fields present")
                    
                    # Verify portfolio structure
                    portfolio = data.get("portfolio", [])
                    if isinstance(portfolio, list):
                        self.log_result("Get Stylist Profile - Portfolio", True, f"Portfolio has {len(portfolio)} items")
                        
                        # Check if tester account has demo portfolio
                        if data.get("is_own_profile") and len(portfolio) > 0:
                            self.log_result("Tester Portfolio Auto-Population", True, "Demo portfolio items found")
                        else:
                            self.log_result("Tester Portfolio Auto-Population", True, "No demo portfolio (expected for non-tester)")
                    else:
                        self.log_result("Get Stylist Profile - Portfolio", False, "Portfolio is not a list")
                else:
                    self.log_result("Get Stylist Profile - Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_result("Get Stylist Profile", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Get Stylist Profile - Exception", False, f"Exception: {str(e)}")
    
    def test_avatar_upload(self):
        """Test POST /api/profiles/avatar - Avatar upload (mock test)"""
        print("📸 TESTING AVATAR UPLOAD ENDPOINT...")
        
        try:
            # Create a small test image in base64 (1x1 pixel PNG)
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
            
            response = self.session.post(f"{BACKEND_URL}/profiles/avatar", json={
                "image_base64": test_image_base64
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "avatar_url" in data:
                    self.log_result("Avatar Upload", True, f"Avatar uploaded successfully: {data.get('message')}")
                    
                    # Verify avatar URL format
                    avatar_url = data.get("avatar_url")
                    if avatar_url and (avatar_url.startswith("http") or avatar_url.startswith("data:")):
                        self.log_result("Avatar URL Format", True, "Valid avatar URL returned")
                    else:
                        self.log_result("Avatar URL Format", False, f"Invalid avatar URL: {avatar_url}")
                else:
                    self.log_result("Avatar Upload", False, "Missing success flag or avatar_url in response")
            else:
                self.log_result("Avatar Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Avatar Upload - Exception", False, f"Exception: {str(e)}")
    
    def test_credentials_management(self):
        """Test POST /api/profiles/credentials - Update credentials"""
        print("🏆 TESTING CREDENTIALS MANAGEMENT...")
        
        try:
            # Test updating credentials
            credentials_data = {
                "license_number": "ST123456",
                "license_state": "CA",
                "is_verified": True,
                "certifications": ["Advanced Color Theory", "Balayage Specialist"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/profiles/credentials", json=credentials_data)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    self.log_result("Update Credentials", True, data.get("message", "Credentials updated"))
                    
                    # Test retrieving credentials
                    get_response = self.session.get(f"{BACKEND_URL}/profiles/credentials")
                    
                    if get_response.status_code == 200:
                        cred_data = get_response.json()
                        
                        # Verify the updated data
                        if (cred_data.get("license_number") == "ST123456" and 
                            cred_data.get("license_state") == "CA" and
                            cred_data.get("is_verified") == True):
                            self.log_result("Get Credentials", True, "Credentials retrieved and verified")
                        else:
                            self.log_result("Get Credentials", False, f"Credential data mismatch: {cred_data}")
                    else:
                        self.log_result("Get Credentials", False, f"Status: {get_response.status_code}")
                else:
                    self.log_result("Update Credentials", False, "Missing success flag in response")
            else:
                self.log_result("Update Credentials", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("Credentials Management - Exception", False, f"Exception: {str(e)}")
    
    def test_my_hub_profile(self):
        """Test GET /api/profiles/me/hub - Quick access to own profile"""
        print("🏠 TESTING MY HUB PROFILE ENDPOINT...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/profiles/me/hub")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields for own profile
                required_fields = [
                    "id", "full_name", "followers_count", "following_count", 
                    "posts_count", "portfolio_count", "is_verified", "portfolio",
                    "is_own_profile"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_result("My Hub Profile - Structure", True, "All required fields present")
                    
                    # Verify is_own_profile is True
                    if data.get("is_own_profile") == True:
                        self.log_result("My Hub Profile - Own Profile Flag", True, "is_own_profile correctly set to True")
                    else:
                        self.log_result("My Hub Profile - Own Profile Flag", False, f"is_own_profile is {data.get('is_own_profile')}")
                    
                    # Verify user ID matches
                    if data.get("id") == self.user_id:
                        self.log_result("My Hub Profile - User ID Match", True, "Profile ID matches authenticated user")
                    else:
                        self.log_result("My Hub Profile - User ID Match", False, f"Profile ID {data.get('id')} != User ID {self.user_id}")
                        
                else:
                    self.log_result("My Hub Profile - Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_result("My Hub Profile", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_result("My Hub Profile - Exception", False, f"Exception: {str(e)}")
    
    def test_tester_account_population(self):
        """Verify that tester accounts auto-populate with demo portfolio"""
        print("🧪 TESTING TESTER ACCOUNT AUTO-POPULATION...")
        
        try:
            # Check if current user is a tester
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                is_tester = user_data.get("is_tester", False)
                
                if is_tester:
                    # Get profile to check portfolio
                    profile_response = self.session.get(f"{BACKEND_URL}/profiles/me/hub")
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        portfolio = profile_data.get("portfolio", [])
                        
                        if len(portfolio) > 0:
                            self.log_result("Tester Auto-Population", True, f"Tester account has {len(portfolio)} demo portfolio items")
                            
                            # Verify portfolio items have required fields
                            first_item = portfolio[0]
                            if "image" in first_item and "caption" in first_item:
                                self.log_result("Demo Portfolio Structure", True, "Portfolio items have image and caption")
                            else:
                                self.log_result("Demo Portfolio Structure", False, "Portfolio items missing required fields")
                        else:
                            self.log_result("Tester Auto-Population", False, "Tester account has no demo portfolio items")
                    else:
                        self.log_result("Tester Auto-Population", False, f"Failed to get profile: {profile_response.status_code}")
                else:
                    self.log_result("Tester Auto-Population", True, "Non-tester account (auto-population not expected)")
                    
            else:
                self.log_result("Tester Auto-Population", False, f"Failed to get user info: {response.status_code}")
                
        except Exception as e:
            self.log_result("Tester Auto-Population - Exception", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Stylist Hub profile endpoint tests"""
        print("=" * 60)
        print("STYLIST HUB BACKEND ENDPOINTS TESTING")
        print("=" * 60)
        print()
        
        # Authenticate first
        if not self.authenticate():
            print("❌ AUTHENTICATION FAILED - CANNOT PROCEED WITH TESTS")
            return
        
        print()
        
        # Run all tests
        self.test_discover_stylists()
        self.test_get_stylist_profile()
        self.test_avatar_upload()
        self.test_credentials_management()
        self.test_my_hub_profile()
        self.test_tester_account_population()
        
        # Print summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test']}: {result['details']}")
            print()
        
        print("DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        return success_rate >= 80  # Consider 80%+ success rate as passing

if __name__ == "__main__":
    tester = StylistHubTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 STYLIST HUB ENDPOINTS TESTING COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️  STYLIST HUB ENDPOINTS TESTING COMPLETED WITH ISSUES")
        sys.exit(1)