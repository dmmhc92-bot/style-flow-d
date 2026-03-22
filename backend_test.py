#!/usr/bin/env python3
"""
StyleFlow Backend API Testing - Full User Flow
Tests all backend APIs according to the review request specifications
"""

import requests
import json
import base64
from datetime import datetime
import sys

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

class StyleFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        self.portfolio_image_id = None
        self.test_results = []
        import time
        self.timestamp = int(time.time())
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None

    def test_auth_flow(self):
        """Test FLOW 1: AUTH (Signup + Login)"""
        print("\n=== FLOW 1: AUTH TESTING ===")
        
        # Test 1: Signup
        signup_data = {
            "full_name": "Test User",
            "email": f"flowtest{self.timestamp}@test.com",
            "password": "Test1234!"
        }
        
        response = self.make_request("POST", "/auth/signup", signup_data)
        if response and response.status_code == 200:
            data = response.json()
            self.user1_token = data.get("token")
            self.log_test("1. User Signup", True, f"Token received: {bool(self.user1_token)}")
        else:
            self.log_test("1. User Signup", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 2: Login
        login_data = {
            "email": f"flowtest{self.timestamp}@test.com",
            "password": "Test1234!"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            data = response.json()
            token = data.get("token")
            self.log_test("2. User Login", True, f"JWT token returned: {bool(token)}")
            # Use the login token for subsequent requests
            self.user1_token = token
        else:
            self.log_test("2. User Login", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        return True

    def test_profile_update_flow(self):
        """Test FLOW 2: PROFILE UPDATE (Critical - must persist)"""
        print("\n=== FLOW 2: PROFILE UPDATE TESTING ===")
        
        if not self.user1_token:
            self.log_test("Profile Update Flow", False, "No auth token available")
            return False
            
        # Test 4: First profile update
        profile_data = {
            "full_name": "Updated Name",
            "bio": "Test bio",
            "city": "New York",
            "specialties": "Hair Color"
        }
        
        response = self.make_request("PUT", "/auth/profile", profile_data, self.user1_token)
        if response and response.status_code == 200:
            self.log_test("4. Profile Update #1", True, "Profile updated successfully")
        else:
            self.log_test("4. Profile Update #1", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 5: Verify profile data persisted
        response = self.make_request("GET", "/auth/me", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            bio_ok = data.get("bio") == "Test bio"
            city_ok = data.get("city") == "New York"
            specialties_ok = data.get("specialties") == "Hair Color"
            name_ok = data.get("full_name") == "Updated Name"
            
            if bio_ok and city_ok and specialties_ok and name_ok:
                self.log_test("5. Profile Data Persistence #1", True, "All fields persisted correctly")
                self.user1_id = data.get("id")
            else:
                missing = []
                if not bio_ok: missing.append("bio")
                if not city_ok: missing.append("city")
                if not specialties_ok: missing.append("specialties")
                if not name_ok: missing.append("full_name")
                self.log_test("5. Profile Data Persistence #1", False, f"Missing/incorrect fields: {missing}")
                return False
        else:
            self.log_test("5. Profile Data Persistence #1", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 6: Second profile update (add instagram)
        profile_data2 = {
            "instagram_handle": "@testsalonista"
        }
        
        response = self.make_request("PUT", "/auth/profile", profile_data2, self.user1_token)
        if response and response.status_code == 200:
            self.log_test("6. Profile Update #2", True, "Instagram handle added")
        else:
            self.log_test("6. Profile Update #2", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 7: Verify all profile data persisted
        response = self.make_request("GET", "/auth/me", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            bio_ok = data.get("bio") == "Test bio"
            city_ok = data.get("city") == "New York"
            specialties_ok = data.get("specialties") == "Hair Color"
            name_ok = data.get("full_name") == "Updated Name"
            instagram_ok = data.get("instagram_handle") == "@testsalonista"
            
            if bio_ok and city_ok and specialties_ok and name_ok and instagram_ok:
                self.log_test("7. Profile Data Persistence #2", True, "All fields including instagram persisted")
            else:
                missing = []
                if not bio_ok: missing.append("bio")
                if not city_ok: missing.append("city")
                if not specialties_ok: missing.append("specialties")
                if not name_ok: missing.append("full_name")
                if not instagram_ok: missing.append("instagram_handle")
                self.log_test("7. Profile Data Persistence #2", False, f"Missing/incorrect fields: {missing}")
                return False
        else:
            self.log_test("7. Profile Data Persistence #2", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        return True

    def test_discover_users_flow(self):
        """Test FLOW 3: DISCOVER USERS"""
        print("\n=== FLOW 3: DISCOVER USERS TESTING ===")
        
        if not self.user1_token:
            self.log_test("Discover Users Flow", False, "No auth token available")
            return False
            
        # Test 8: Get discover users list
        response = self.make_request("GET", "/users/discover", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("8. Discover Users List", True, f"Returned {len(data)} users")
        else:
            self.log_test("8. Discover Users List", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 9: Search users with query param
        response = self.make_request("GET", "/users/discover", token=self.user1_token, params={"search": "test"})
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("9. Discover Users Search", True, f"Search returned {len(data)} users")
        else:
            self.log_test("9. Discover Users Search", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        return True

    def test_user_profile_view_flow(self):
        """Test FLOW 4: USER PROFILE VIEW"""
        print("\n=== FLOW 4: USER PROFILE VIEW TESTING ===")
        
        if not self.user1_token:
            self.log_test("User Profile View Flow", False, "No auth token available")
            return False
            
        # Test 10: Create second user
        signup_data2 = {
            "full_name": "Other Stylist",
            "email": f"otherstylist{self.timestamp}@test.com",
            "password": "Test1234!"
        }
        
        response = self.make_request("POST", "/auth/signup", signup_data2)
        if response and response.status_code == 200:
            data = response.json()
            self.user2_token = data.get("token")
            self.log_test("10. Create Second User", True, f"Second user created")
            
            # Get user2 ID
            response = self.make_request("GET", "/auth/me", token=self.user2_token)
            if response and response.status_code == 200:
                self.user2_id = response.json().get("id")
        else:
            self.log_test("10. Create Second User", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 11: View second user's profile using first user's token
        if self.user2_id:
            response = self.make_request("GET", f"/users/{self.user2_id}/profile", token=self.user1_token)
            if response and response.status_code == 200:
                data = response.json()
                has_following = "is_following" in data
                has_followers_count = "followers_count" in data
                has_following_count = "following_count" in data
                
                if has_following and has_followers_count and has_following_count:
                    self.log_test("11. View User Profile", True, f"Profile returned with follow data")
                else:
                    missing = []
                    if not has_following: missing.append("is_following")
                    if not has_followers_count: missing.append("followers_count")
                    if not has_following_count: missing.append("following_count")
                    self.log_test("11. View User Profile", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("11. View User Profile", False, f"Status: {response.status_code if response else 'No response'}")
                return False
        else:
            self.log_test("11. View User Profile", False, "No user2_id available")
            return False
            
        return True

    def test_follow_unfollow_flow(self):
        """Test FLOW 5: FOLLOW/UNFOLLOW"""
        print("\n=== FLOW 5: FOLLOW/UNFOLLOW TESTING ===")
        
        if not self.user1_token or not self.user2_id:
            self.log_test("Follow/Unfollow Flow", False, "Missing auth token or user2_id")
            return False
            
        # Test 12: Follow user
        response = self.make_request("POST", f"/users/{self.user2_id}/follow", token=self.user1_token)
        if response and response.status_code == 200:
            self.log_test("12. Follow User", True, "Follow successful")
        else:
            self.log_test("12. Follow User", False, f"Status: {response.status_code if response else 'No response'} - ENDPOINT MISSING")
            
        # Test 13: Verify follow state
        response = self.make_request("GET", f"/users/{self.user2_id}/profile", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            is_following = data.get("is_following", False)
            followers_count = data.get("followers_count", 0)
            
            if is_following and followers_count > 0:
                self.log_test("13. Verify Follow State", True, f"is_following=true, followers_count={followers_count}")
            else:
                self.log_test("13. Verify Follow State", False, f"is_following={is_following}, followers_count={followers_count}")
        else:
            self.log_test("13. Verify Follow State", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Test 14: Unfollow user
        response = self.make_request("DELETE", f"/users/{self.user2_id}/follow", token=self.user1_token)
        if response and response.status_code == 200:
            self.log_test("14. Unfollow User", True, "Unfollow successful")
        else:
            self.log_test("14. Unfollow User", False, f"Status: {response.status_code if response else 'No response'} - ENDPOINT MISSING")
            
        # Test 15: Verify unfollow state
        response = self.make_request("GET", f"/users/{self.user2_id}/profile", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            is_following = data.get("is_following", True)  # Should be False
            followers_count = data.get("followers_count", 1)  # Should be 0
            
            if not is_following and followers_count == 0:
                self.log_test("15. Verify Unfollow State", True, f"is_following=false, followers_count={followers_count}")
            else:
                self.log_test("15. Verify Unfollow State", False, f"is_following={is_following}, followers_count={followers_count}")
        else:
            self.log_test("15. Verify Unfollow State", False, f"Status: {response.status_code if response else 'No response'}")
            
        return True

    def test_portfolio_flow(self):
        """Test FLOW 6: PORTFOLIO"""
        print("\n=== FLOW 6: PORTFOLIO TESTING ===")
        
        if not self.user1_token:
            self.log_test("Portfolio Flow", False, "No auth token available")
            return False
            
        # Test 16: Upload portfolio image
        # Create a small valid base64 image
        small_image_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        portfolio_data = {
            "image": small_image_b64,
            "caption": "Test portfolio image"
        }
        
        response = self.make_request("POST", "/portfolio", portfolio_data, self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            self.portfolio_image_id = data.get("id")
            self.log_test("16. Upload Portfolio Image", True, f"Image uploaded with ID: {self.portfolio_image_id}")
        else:
            self.log_test("16. Upload Portfolio Image", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 17: Get portfolio list
        response = self.make_request("GET", "/portfolio", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            if len(data) > 0 and any(item.get("id") == self.portfolio_image_id for item in data):
                self.log_test("17. Get Portfolio List", True, f"Portfolio contains {len(data)} images including uploaded image")
            else:
                self.log_test("17. Get Portfolio List", False, f"Uploaded image not found in portfolio list")
                return False
        else:
            self.log_test("17. Get Portfolio List", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        # Test 18: Delete portfolio image
        if self.portfolio_image_id:
            response = self.make_request("DELETE", f"/portfolio/{self.portfolio_image_id}", token=self.user1_token)
            if response and response.status_code == 200:
                self.log_test("18. Delete Portfolio Image", True, "Image deleted successfully")
            else:
                self.log_test("18. Delete Portfolio Image", False, f"Status: {response.status_code if response else 'No response'}")
                return False
        else:
            self.log_test("18. Delete Portfolio Image", False, "No image ID available")
            return False
            
        # Test 19: Verify image removed
        response = self.make_request("GET", "/portfolio", token=self.user1_token)
        if response and response.status_code == 200:
            data = response.json()
            if not any(item.get("id") == self.portfolio_image_id for item in data):
                self.log_test("19. Verify Image Removed", True, f"Image successfully removed from portfolio")
            else:
                self.log_test("19. Verify Image Removed", False, f"Image still exists in portfolio")
                return False
        else:
            self.log_test("19. Verify Image Removed", False, f"Status: {response.status_code if response else 'No response'}")
            return False
            
        return True

    def run_all_tests(self):
        """Run all test flows"""
        print("🚀 Starting StyleFlow Backend API Testing")
        print(f"Base URL: {self.base_url}")
        
        # Run all test flows
        flows = [
            self.test_auth_flow,
            self.test_profile_update_flow,
            self.test_discover_users_flow,
            self.test_user_profile_view_flow,
            self.test_follow_unfollow_flow,
            self.test_portfolio_flow
        ]
        
        for flow in flows:
            try:
                flow()
            except Exception as e:
                print(f"❌ Flow failed with exception: {str(e)}")
                
        # Summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
                
        # Critical issues
        critical_issues = []
        for test in failed_tests:
            if "ENDPOINT MISSING" in test["details"]:
                critical_issues.append(test["test"])
                
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            print("  • Follow/Unfollow endpoints are missing from backend")
            print("  • Required endpoints: POST /api/users/{id}/follow, DELETE /api/users/{id}/follow")
            
        return passed, total, failed_tests, critical_issues

if __name__ == "__main__":
    tester = StyleFlowTester()
    passed, total, failed_tests, critical_issues = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if failed_tests:
        sys.exit(1)
    else:
        sys.exit(0)