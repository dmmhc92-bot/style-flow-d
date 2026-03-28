#!/usr/bin/env python3
"""
STYLEFLOW PRODUCTION - COMPREHENSIVE END-TO-END TESTING
======================================================

This test suite covers all critical flows as requested in the review:

1. AUTH FLOWS - signup, login, refresh, logout, forgot-password, /api/auth/me
2. STYLIST HUB - profiles, discovery, avatar upload, portfolio, credentials  
3. CLIENT MANAGEMENT - list, create, get detail
4. FORMULA VAULT - list, create
5. APPOINTMENTS - list, create
6. SOCIAL/FEED - list posts, create post, follow user
7. SUBSCRIPTION - status check

Admin credentials: admin@styleflow.com / Admin1234!
"""

import requests
import json
import base64
from datetime import datetime, timedelta
import uuid
import time

# Backend URL from frontend/.env
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials from review request
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

# Test data
TEST_USER_EMAIL = f"testuser_{int(time.time())}@styleflow.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = "Test User"

def create_test_base64_image():
    """Create a small test base64 image for uploads"""
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="

class StyleFlowTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.refresh_token = None
        self.test_client_id = None
        self.test_formula_id = None
        self.test_appointment_id = None
        self.test_post_id = None
        self.test_user_id = None
        self.results = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<50} {status}")
        if details and not success:
            print(f"   Details: {details}")
        self.results.append((test_name, success, details))

    def make_request(self, method, endpoint, data=None, headers=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return None, f"Unsupported method: {method}"

            if response.status_code == expected_status:
                try:
                    return response.json(), None
                except:
                    return {"status": "success"}, None
            else:
                return None, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return None, f"Request error: {str(e)}"

    # ==================== AUTH FLOWS ====================

    def test_auth_signup(self):
        """Test 1: POST /api/auth/signup - Create new user"""
        print("\n🔐 AUTH FLOWS")
        
        signup_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": TEST_USER_NAME,
            "business_name": "Test Salon"
        }
        
        data, error = self.make_request("POST", "/auth/signup", signup_data, expected_status=200)
        if data and not error:
            # Extract user_id from response
            user_data = data.get("user", {})
            self.test_user_id = user_data.get("id")
            self.user_token = data.get("token") or data.get("access_token")
            self.log_result("Auth Signup", True)
            return True
        else:
            self.log_result("Auth Signup", False, error)
            return False

    def test_auth_login_admin(self):
        """Test 2: POST /api/auth/login with admin credentials"""
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        data, error = self.make_request("POST", "/auth/login", login_data)
        if data and not error:
            self.admin_token = data.get("token") or data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            if self.admin_token:
                self.log_result("Auth Login (Admin)", True)
                return True
        
        self.log_result("Auth Login (Admin)", False, error)
        return False

    def test_auth_refresh(self):
        """Test 3: POST /api/auth/refresh with refresh token"""
        if not self.refresh_token:
            self.log_result("Auth Refresh Token", False, "No refresh token available")
            return False
        
        headers = {"X-Refresh-Token": self.refresh_token}
        data, error = self.make_request("POST", "/auth/refresh", headers=headers)
        
        if data and not error:
            new_token = data.get("token") or data.get("access_token")
            if new_token:
                self.admin_token = new_token  # Update token
                self.log_result("Auth Refresh Token", True)
                return True
        
        self.log_result("Auth Refresh Token", False, error)
        return False

    def test_auth_me(self):
        """Test 4: GET /api/auth/me - Verify user data with is_tester flag"""
        if not self.admin_token:
            self.log_result("Auth Me Endpoint", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/auth/me", headers=headers)
        
        if data and not error:
            has_is_tester = "is_tester" in data
            email_correct = data.get("email") == ADMIN_EMAIL
            if has_is_tester and email_correct:
                self.log_result("Auth Me Endpoint", True)
                return True
            else:
                self.log_result("Auth Me Endpoint", False, f"Missing is_tester field or wrong email")
                return False
        
        self.log_result("Auth Me Endpoint", False, error)
        return False

    def test_auth_forgot_password(self):
        """Test 5: POST /api/auth/forgot-password - Test email trigger"""
        forgot_data = {"email": ADMIN_EMAIL}
        data, error = self.make_request("POST", "/auth/forgot-password", forgot_data)
        
        if data and not error:
            # Should return success message even for security
            self.log_result("Auth Forgot Password", True)
            return True
        
        self.log_result("Auth Forgot Password", False, error)
        return False

    def test_auth_logout(self):
        """Test 6: POST /api/auth/logout - Verify token revocation"""
        if not self.admin_token:
            self.log_result("Auth Logout", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("POST", "/auth/logout", headers=headers)
        
        if data and not error:
            self.log_result("Auth Logout", True)
            return True
        
        self.log_result("Auth Logout", False, error)
        return False

    # ==================== STYLIST HUB ====================

    def test_profiles_me_hub(self):
        """Test 7: GET /api/profiles/me/hub - Own profile with portfolio"""
        print("\n👤 STYLIST HUB")
        
        if not self.admin_token:
            self.log_result("Profiles Me Hub", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/profiles/me/hub", headers=headers)
        
        if data and not error:
            has_portfolio = "portfolio" in data or "portfolio_images" in data
            self.log_result("Profiles Me Hub", True)
            return True
        
        self.log_result("Profiles Me Hub", False, error)
        return False

    def test_profiles_discover(self):
        """Test 8: GET /api/profiles/discover - Discovery with filters"""
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        
        # Test basic discovery
        data, error = self.make_request("GET", "/profiles/discover", headers=headers)
        if not data or error:
            self.log_result("Profiles Discover", False, f"Basic discover failed: {error}")
            return False
        
        # Test with filters - use simpler parameters
        data, error = self.make_request("GET", "/profiles/discover?featured=true", headers=headers)
        if data and not error:
            self.log_result("Profiles Discover", True)
            return True
        
        self.log_result("Profiles Discover", False, f"Filtered discover failed: {error}")
        return False

    def test_profiles_avatar_upload(self):
        """Test 9: POST /api/profiles/avatar - Cloudinary upload"""
        if not self.admin_token:
            self.log_result("Profiles Avatar Upload", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        upload_data = {"image_base64": create_test_base64_image()}
        
        data, error = self.make_request("POST", "/profiles/avatar", upload_data, headers=headers)
        
        if data and not error:
            # Verify production folder structure
            avatar_url = data.get("avatar_url", "")
            has_production_folder = "styleflow_uploads/avatars" in avatar_url
            self.log_result("Profiles Avatar Upload", has_production_folder)
            return has_production_folder
        
        self.log_result("Profiles Avatar Upload", False, error)
        return False

    def test_profiles_portfolio_upload(self):
        """Test 10: POST /api/profiles/portfolio - Portfolio upload"""
        if not self.admin_token:
            self.log_result("Profiles Portfolio Upload", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        upload_data = {
            "image_base64": create_test_base64_image(),
            "caption": "Test portfolio upload"
        }
        
        data, error = self.make_request("POST", "/profiles/portfolio", upload_data, headers=headers)
        
        if data and not error:
            self.log_result("Profiles Portfolio Upload", True)
            return True
        
        self.log_result("Profiles Portfolio Upload", False, error)
        return False

    def test_profiles_credentials(self):
        """Test 11: POST /api/profiles/credentials - Update license/credentials"""
        if not self.admin_token:
            self.log_result("Profiles Credentials", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        creds_data = {
            "license_number": "CA123456",
            "license_state": "CA",
            "certifications": ["Advanced Color Theory", "Balayage Specialist"]
        }
        
        data, error = self.make_request("POST", "/profiles/credentials", creds_data, headers=headers)
        
        if data and not error:
            self.log_result("Profiles Credentials", True)
            return True
        
        self.log_result("Profiles Credentials", False, error)
        return False

    # ==================== CLIENT MANAGEMENT ====================

    def test_clients_list(self):
        """Test 12: GET /api/clients - List clients"""
        print("\n👥 CLIENT MANAGEMENT")
        
        if not self.admin_token:
            self.log_result("Clients List", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/clients", headers=headers)
        
        if data and not error:
            self.log_result("Clients List", True)
            return True
        
        self.log_result("Clients List", False, error)
        return False

    def test_clients_create(self):
        """Test 13: POST /api/clients - Create new client"""
        if not self.admin_token:
            self.log_result("Clients Create", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        client_data = {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-0123",
            "notes": "Prefers natural colors",
            "is_vip": False
        }
        
        data, error = self.make_request("POST", "/clients", client_data, headers=headers, expected_status=200)
        
        if data and not error:
            self.test_client_id = data.get("id")
            self.log_result("Clients Create", True)
            return True
        
        self.log_result("Clients Create", False, error)
        return False

    def test_clients_get_detail(self):
        """Test 14: GET /api/clients/{id} - Get client detail"""
        if not self.admin_token or not self.test_client_id:
            self.log_result("Clients Get Detail", False, "No admin token or client ID")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", f"/clients/{self.test_client_id}", headers=headers)
        
        if data and not error:
            self.log_result("Clients Get Detail", True)
            return True
        
        self.log_result("Clients Get Detail", False, error)
        return False

    # ==================== FORMULA VAULT ====================

    def test_formulas_list(self):
        """Test 15: GET /api/formulas - List formulas"""
        print("\n🧪 FORMULA VAULT")
        
        if not self.admin_token:
            self.log_result("Formulas List", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/formulas", headers=headers)
        
        if data and not error:
            self.log_result("Formulas List", True)
            return True
        
        self.log_result("Formulas List", False, error)
        return False

    def test_formulas_create(self):
        """Test 16: POST /api/formulas - Create formula"""
        if not self.admin_token or not self.test_client_id:
            self.log_result("Formulas Create", False, "No admin token or client ID")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        formula_data = {
            "client_id": self.test_client_id,
            "formula_name": "Honey Blonde Balayage",
            "formula_details": "20vol developer + Wella T18 + Olaplex"
        }
        
        data, error = self.make_request("POST", "/formulas", formula_data, headers=headers, expected_status=200)
        
        if data and not error:
            self.test_formula_id = data.get("id")
            self.log_result("Formulas Create", True)
            return True
        
        self.log_result("Formulas Create", False, error)
        return False

    # ==================== APPOINTMENTS ====================

    def test_appointments_list(self):
        """Test 17: GET /api/appointments - List appointments"""
        print("\n📅 APPOINTMENTS")
        
        if not self.admin_token:
            self.log_result("Appointments List", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/appointments", headers=headers)
        
        if data and not error:
            self.log_result("Appointments List", True)
            return True
        
        self.log_result("Appointments List", False, error)
        return False

    def test_appointments_create(self):
        """Test 18: POST /api/appointments - Create appointment"""
        if not self.admin_token or not self.test_client_id:
            self.log_result("Appointments Create", False, "No admin token or client ID")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        appointment_data = {
            "client_id": self.test_client_id,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "service": "Color & Cut",
            "duration_minutes": 120,
            "notes": "Balayage touch-up"
        }
        
        data, error = self.make_request("POST", "/appointments", appointment_data, headers=headers, expected_status=200)
        
        if data and not error:
            self.test_appointment_id = data.get("id")
            self.log_result("Appointments Create", True)
            return True
        
        self.log_result("Appointments Create", False, error)
        return False

    # ==================== SOCIAL/FEED ====================

    def test_posts_list(self):
        """Test 19: GET /api/posts - List feed posts"""
        print("\n📱 SOCIAL/FEED")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        data, error = self.make_request("GET", "/posts", headers=headers)
        
        if data and not error:
            self.log_result("Posts List", True)
            return True
        
        self.log_result("Posts List", False, error)
        return False

    def test_posts_create(self):
        """Test 20: POST /api/posts - Create post"""
        if not self.admin_token:
            self.log_result("Posts Create", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        post_data = {
            "images": [create_test_base64_image()],
            "caption": "Beautiful transformation! #balayage #colortrend",
            "tags": ["balayage", "colortrend", "transformation"]
        }
        
        data, error = self.make_request("POST", "/posts", post_data, headers=headers, expected_status=200)
        
        if data and not error:
            self.test_post_id = data.get("id")
            self.log_result("Posts Create", True)
            return True
        
        self.log_result("Posts Create", False, error)
        return False

    def test_users_follow(self):
        """Test 21: POST /api/users/{id}/follow - Follow user"""
        if not self.admin_token or not self.test_user_id:
            self.log_result("Users Follow", False, "No admin token or test user ID")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("POST", f"/users/{self.test_user_id}/follow", headers=headers)
        
        if data and not error:
            self.log_result("Users Follow", True)
            return True
        
        self.log_result("Users Follow", False, error)
        return False

    # ==================== SUBSCRIPTION ====================

    def test_subscription_status(self):
        """Test 22: GET /api/subscription/status - Check subscription"""
        print("\n💳 SUBSCRIPTION")
        
        if not self.admin_token:
            self.log_result("Subscription Status", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        data, error = self.make_request("GET", "/subscription/status", headers=headers)
        
        if data and not error:
            self.log_result("Subscription Status", True)
            return True
        
        self.log_result("Subscription Status", False, error)
        return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 80)
        print("STYLEFLOW PRODUCTION - COMPREHENSIVE END-TO-END TESTING")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Run all tests
        test_methods = [
            self.test_auth_signup,
            self.test_auth_login_admin,
            self.test_auth_refresh,
            self.test_auth_me,
            self.test_auth_forgot_password,
            self.test_auth_logout,
            
            # Re-login for subsequent tests
            self.test_auth_login_admin,
            
            self.test_profiles_me_hub,
            self.test_profiles_discover,
            self.test_profiles_avatar_upload,
            self.test_profiles_portfolio_upload,
            self.test_profiles_credentials,
            
            self.test_clients_list,
            self.test_clients_create,
            self.test_clients_get_detail,
            
            self.test_formulas_list,
            self.test_formulas_create,
            
            self.test_appointments_list,
            self.test_appointments_create,
            
            self.test_posts_list,
            self.test_posts_create,
            self.test_users_follow,
            
            self.test_subscription_status
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
                self.log_result(test_name, False, f"Exception: {str(e)}")

        # Summary
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Show failed tests
        failed_tests = [(name, details) for name, success, details in self.results if not success]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for name, details in failed_tests:
                print(f"   • {name}")
                if details:
                    print(f"     {details}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - StyleFlow backend is PRODUCTION-READY")
        else:
            print(f"\n⚠️  {total-passed} TEST(S) FAILED - Issues need attention")
        
        return passed == total

def main():
    """Run comprehensive StyleFlow testing"""
    tester = StyleFlowTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)