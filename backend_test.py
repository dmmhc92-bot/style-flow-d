#!/usr/bin/env python3
"""
Backend Testing Script for StyleFlow Following/Followers System
Tests all Following/Followers endpoints with admin credentials
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class FollowingFollowersTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.admin_user_id = None
        self.test_user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
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
    
    def login_admin(self):
        """Login as admin user"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")
                
                # Get admin user profile to get user ID
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                profile_response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    self.admin_user_id = profile_data.get("id")
                    self.log_test("Admin Login", True, f"Admin ID: {self.admin_user_id}")
                    return True
                else:
                    self.log_test("Admin Login", False, f"Failed to get profile: {profile_response.status_code}")
                    return False
            else:
                self.log_test("Admin Login", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def get_discover_users(self):
        """Get users from discover endpoint to find someone to follow"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/profiles/discover", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                if users and len(users) > 0:
                    # Find a user that's not the admin
                    for user in users:
                        if user.get("id") != self.admin_user_id:
                            self.test_user_id = user.get("id")
                            self.log_test("Get Discover Users", True, f"Found test user: {user.get('full_name')} (ID: {self.test_user_id})")
                            return True
                    
                    self.log_test("Get Discover Users", False, "No suitable test user found")
                    return False
                else:
                    self.log_test("Get Discover Users", False, "No users found in discover")
                    return False
            else:
                self.log_test("Get Discover Users", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Discover Users", False, f"Exception: {str(e)}")
            return False
    
    def test_get_following_empty(self):
        """Test GET /api/users/following - should be empty initially"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/users/following", headers=headers)
            
            if response.status_code == 200:
                following = response.json()
                if isinstance(following, list):
                    self.log_test("GET /users/following (empty)", True, f"Following list: {len(following)} users")
                    return True
                else:
                    self.log_test("GET /users/following (empty)", False, f"Expected list, got: {type(following)}")
                    return False
            else:
                self.log_test("GET /users/following (empty)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /users/following (empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_get_followers_empty(self):
        """Test GET /api/users/followers - should be empty initially"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/users/followers", headers=headers)
            
            if response.status_code == 200:
                followers = response.json()
                if isinstance(followers, list):
                    self.log_test("GET /users/followers (empty)", True, f"Followers list: {len(followers)} users")
                    return True
                else:
                    self.log_test("GET /users/followers (empty)", False, f"Expected list, got: {type(followers)}")
                    return False
            else:
                self.log_test("GET /users/followers (empty)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /users/followers (empty)", False, f"Exception: {str(e)}")
            return False
    
    def test_follow_user(self):
        """Test POST /api/users/{user_id}/follow"""
        if not self.test_user_id:
            self.log_test("POST /users/{user_id}/follow", False, "No test user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BASE_URL}/users/{self.test_user_id}/follow", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("POST /users/{user_id}/follow", True, f"Response: {data.get('message', 'Success')}")
                return True
            else:
                self.log_test("POST /users/{user_id}/follow", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("POST /users/{user_id}/follow", False, f"Exception: {str(e)}")
            return False
    
    def test_get_following_with_user(self):
        """Test GET /api/users/following - should contain the followed user"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/users/following", headers=headers)
            
            if response.status_code == 200:
                following = response.json()
                if isinstance(following, list) and len(following) > 0:
                    # Check if our test user is in the list
                    found_user = False
                    for user in following:
                        if user.get("id") == self.test_user_id:
                            found_user = True
                            break
                    
                    if found_user:
                        self.log_test("GET /users/following (with user)", True, f"Following list contains test user: {len(following)} users")
                        return True
                    else:
                        self.log_test("GET /users/following (with user)", False, f"Test user not found in following list")
                        return False
                else:
                    self.log_test("GET /users/following (with user)", False, f"Following list is empty or invalid")
                    return False
            else:
                self.log_test("GET /users/following (with user)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /users/following (with user)", False, f"Exception: {str(e)}")
            return False
    
    def test_unfollow_user(self):
        """Test DELETE /api/users/{user_id}/follow"""
        if not self.test_user_id:
            self.log_test("DELETE /users/{user_id}/follow", False, "No test user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{BASE_URL}/users/{self.test_user_id}/follow", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("DELETE /users/{user_id}/follow", True, f"Response: {data.get('message', 'Success')}")
                return True
            else:
                self.log_test("DELETE /users/{user_id}/follow", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("DELETE /users/{user_id}/follow", False, f"Exception: {str(e)}")
            return False
    
    def test_get_following_empty_again(self):
        """Test GET /api/users/following - should be empty again after unfollow"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/users/following", headers=headers)
            
            if response.status_code == 200:
                following = response.json()
                if isinstance(following, list) and len(following) == 0:
                    self.log_test("GET /users/following (empty again)", True, "Following list is empty after unfollow")
                    return True
                else:
                    self.log_test("GET /users/following (empty again)", False, f"Following list not empty: {len(following)} users")
                    return False
            else:
                self.log_test("GET /users/following (empty again)", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("GET /users/following (empty again)", False, f"Exception: {str(e)}")
            return False
    
    def test_remove_follower_error(self):
        """Test DELETE /api/users/{user_id}/follower - should return error since admin has no followers"""
        if not self.test_user_id:
            self.log_test("DELETE /users/{user_id}/follower (error test)", False, "No test user ID available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{BASE_URL}/users/{self.test_user_id}/follower", headers=headers)
            
            # This should return 404 since the test user is not following admin
            if response.status_code == 404:
                data = response.json()
                self.log_test("DELETE /users/{user_id}/follower (error test)", True, f"Correctly returned 404: {data.get('detail', 'User is not following you')}")
                return True
            else:
                self.log_test("DELETE /users/{user_id}/follower (error test)", False, f"Expected 404, got: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("DELETE /users/{user_id}/follower (error test)", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all Following/Followers system tests"""
        print("=" * 60)
        print("STYLEFLOW FOLLOWING/FOLLOWERS SYSTEM TESTING")
        print("=" * 60)
        print(f"Testing against: {BASE_URL}")
        print(f"Admin credentials: {ADMIN_EMAIL}")
        print()
        
        # Step 1: Login as admin
        if not self.login_admin():
            print("❌ CRITICAL: Admin login failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Get a user to follow from discover
        if not self.get_discover_users():
            print("❌ CRITICAL: Could not find test user. Cannot proceed with follow tests.")
            return False
        
        # Step 3: Test initial empty states
        self.test_get_following_empty()
        self.test_get_followers_empty()
        
        # Step 4: Test follow flow
        if self.test_follow_user():
            # Step 5: Verify user appears in following list
            self.test_get_following_with_user()
            
            # Step 6: Test unfollow
            if self.test_unfollow_user():
                # Step 7: Verify following list is empty again
                self.test_get_following_empty_again()
        
        # Step 8: Test error handling for remove follower
        self.test_remove_follower_error()
        
        # Print summary
        print()
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        # Print detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        if passed == total:
            print("🎉 ALL TESTS PASSED! Following/Followers system is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Please review the issues above.")
        
        return passed == total

if __name__ == "__main__":
    tester = FollowingFollowersTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)