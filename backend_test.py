#!/usr/bin/env python3
"""
StyleFlow Moderation System API Testing
Tests all moderation endpoints including report and block functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ModerationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.user_a_token = None
        self.user_b_token = None
        self.user_a_id = None
        self.user_b_id = None
        self.test_results = []
        
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
    
    def make_request(self, method, endpoint, data=None, token=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def test_user_signup(self, email, full_name, password):
        """Test user signup and return token and user_id"""
        data = {
            "email": email,
            "full_name": full_name,
            "password": password
        }
        
        response = self.make_request("POST", "/auth/signup", data)
        
        if response and response.status_code == 200:
            result = response.json()
            return result.get("token"), result.get("user", {}).get("email")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            print(f"Signup failed: {error_msg}")
            return None, None
    
    def get_user_id_from_profile(self, token):
        """Get user ID from profile endpoint"""
        response = self.make_request("GET", "/auth/me", token=token)
        
        if response and response.status_code == 200:
            result = response.json()
            return result.get("id")
        return None
    
    def test_create_report(self, reporter_token, reported_user_id, content_type, reason, details):
        """Test creating a report"""
        data = {
            "reported_user_id": reported_user_id,
            "content_type": content_type,
            "reason": reason,
            "details": details
        }
        
        response = self.make_request("POST", "/report", data, token=reporter_token)
        
        if response and response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            return False, error_msg
    
    def test_block_user(self, blocker_token, user_id_to_block):
        """Test blocking a user"""
        response = self.make_request("POST", f"/block/{user_id_to_block}", token=blocker_token)
        
        if response and response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            return False, error_msg
    
    def test_get_blocked_users(self, token):
        """Test getting blocked users list"""
        response = self.make_request("GET", "/blocked", token=token)
        
        if response and response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            return False, error_msg
    
    def test_discover_users(self, token, search=None):
        """Test user discovery endpoint"""
        endpoint = "/users/discover"
        if search:
            endpoint += f"?search={search}"
        
        response = self.make_request("GET", endpoint, token=token)
        
        if response and response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            return False, error_msg
    
    def test_get_user_profile(self, token, user_id):
        """Test getting user profile"""
        response = self.make_request("GET", f"/users/{user_id}/profile", token=token)
        
        return response.status_code, response.json() if response else None
    
    def test_unblock_user(self, blocker_token, user_id_to_unblock):
        """Test unblocking a user"""
        response = self.make_request("DELETE", f"/block/{user_id_to_unblock}", token=blocker_token)
        
        if response and response.status_code == 200:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            return False, error_msg
    
    def run_moderation_tests(self):
        """Run comprehensive moderation system tests"""
        print("🧪 Starting StyleFlow Moderation System API Tests")
        print("=" * 60)
        
        # FLOW 1: Create test users
        print("\n📝 FLOW 1: USER CREATION")
        
        # Create User A (Reporter)
        self.user_a_token, user_a_email = self.test_user_signup(
            "reporter_test@test.com", 
            "Reporter User", 
            "Test1234!"
        )
        
        if self.user_a_token:
            self.user_a_id = self.get_user_id_from_profile(self.user_a_token)
            self.log_test("Create User A (Reporter)", True, f"Email: {user_a_email}, ID: {self.user_a_id}")
        else:
            self.log_test("Create User A (Reporter)", False, "Failed to create user")
            return
        
        # Create User B (Reported)
        self.user_b_token, user_b_email = self.test_user_signup(
            "reported_test@test.com", 
            "Reported User", 
            "Test1234!"
        )
        
        if self.user_b_token:
            self.user_b_id = self.get_user_id_from_profile(self.user_b_token)
            self.log_test("Create User B (Reported)", True, f"Email: {user_b_email}, ID: {self.user_b_id}")
        else:
            self.log_test("Create User B (Reported)", False, "Failed to create user")
            return
        
        # FLOW 2: Test Report System
        print("\n📋 FLOW 2: REPORT SYSTEM")
        
        success, result = self.test_create_report(
            self.user_a_token,
            self.user_b_id,
            "profile",
            "spam",
            "Test spam report"
        )
        
        if success:
            self.log_test("Create Report", True, f"Report ID: {result.get('report_id', 'N/A')}")
        else:
            self.log_test("Create Report", False, f"Error: {result}")
        
        # FLOW 3: Test Block System
        print("\n🚫 FLOW 3: BLOCK SYSTEM")
        
        # Block User B
        success, result = self.test_block_user(self.user_a_token, self.user_b_id)
        if success:
            self.log_test("Block User B", True, "User blocked successfully")
        else:
            self.log_test("Block User B", False, f"Error: {result}")
            return
        
        # Get blocked users list
        success, blocked_list = self.test_get_blocked_users(self.user_a_token)
        if success:
            blocked_ids = [user["id"] for user in blocked_list]
            if self.user_b_id in blocked_ids:
                self.log_test("Verify Blocked List", True, f"User B found in blocked list ({len(blocked_list)} total)")
            else:
                self.log_test("Verify Blocked List", False, f"User B not found in blocked list")
        else:
            self.log_test("Get Blocked Users", False, f"Error: {blocked_list}")
        
        # FLOW 4: Test Discover Filters
        print("\n🔍 FLOW 4: DISCOVER FILTERS")
        
        # Test User A discover (should not see User B)
        success, discover_results = self.test_discover_users(self.user_a_token)
        if success:
            discovered_ids = [user["id"] for user in discover_results]
            if self.user_b_id not in discovered_ids:
                self.log_test("User A Discover (blocked filter)", True, f"User B correctly filtered out ({len(discover_results)} users found)")
            else:
                self.log_test("User A Discover (blocked filter)", False, "User B should not appear in discover results")
        else:
            self.log_test("User A Discover", False, f"Error: {discover_results}")
        
        # Test User B discover (should not see User A)
        success, discover_results = self.test_discover_users(self.user_b_token)
        if success:
            discovered_ids = [user["id"] for user in discover_results]
            if self.user_a_id not in discovered_ids:
                self.log_test("User B Discover (bidirectional block)", True, f"User A correctly filtered out ({len(discover_results)} users found)")
            else:
                self.log_test("User B Discover (bidirectional block)", False, "User A should not appear in discover results")
        else:
            self.log_test("User B Discover", False, f"Error: {discover_results}")
        
        # FLOW 5: Test Profile Access Blocking
        print("\n👤 FLOW 5: PROFILE ACCESS BLOCKING")
        
        # User A tries to view User B's profile (should get 403)
        status_code, response = self.test_get_user_profile(self.user_a_token, self.user_b_id)
        if status_code == 403:
            self.log_test("Blocked Profile Access (A→B)", True, "403 Forbidden returned correctly")
        else:
            self.log_test("Blocked Profile Access (A→B)", False, f"Expected 403, got {status_code}")
        
        # User B tries to view User A's profile (should get 403)
        status_code, response = self.test_get_user_profile(self.user_b_token, self.user_a_id)
        if status_code == 403:
            self.log_test("Blocked Profile Access (B→A)", True, "403 Forbidden returned correctly")
        else:
            self.log_test("Blocked Profile Access (B→A)", False, f"Expected 403, got {status_code}")
        
        # FLOW 6: Test Unblock System
        print("\n🔓 FLOW 6: UNBLOCK SYSTEM")
        
        # Unblock User B
        success, result = self.test_unblock_user(self.user_a_token, self.user_b_id)
        if success:
            self.log_test("Unblock User B", True, "User unblocked successfully")
        else:
            self.log_test("Unblock User B", False, f"Error: {result}")
            return
        
        # Test profile access after unblock (should work now)
        status_code, response = self.test_get_user_profile(self.user_a_token, self.user_b_id)
        if status_code == 200:
            self.log_test("Profile Access After Unblock", True, "200 OK returned correctly")
        else:
            self.log_test("Profile Access After Unblock", False, f"Expected 200, got {status_code}")
        
        # FLOW 7: Test Re-block for Final Discover Test
        print("\n🔄 FLOW 7: RE-BLOCK FOR FINAL TESTS")
        
        # Re-block for final discover test
        success, result = self.test_block_user(self.user_a_token, self.user_b_id)
        if success:
            self.log_test("Re-block User B", True, "User re-blocked successfully")
        else:
            self.log_test("Re-block User B", False, f"Error: {result}")
        
        # Final discover test
        success, discover_results = self.test_discover_users(self.user_a_token)
        if success:
            discovered_ids = [user["id"] for user in discover_results]
            if self.user_b_id not in discovered_ids:
                self.log_test("Final Discover Filter Test", True, "Blocked users correctly filtered")
            else:
                self.log_test("Final Discover Filter Test", False, "Blocked user still appears in results")
        else:
            self.log_test("Final Discover Filter Test", False, f"Error: {discover_results}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n🎯 CRITICAL MODERATION FEATURES TESTED:")
        print("  ✓ Report creation and validation")
        print("  ✓ User blocking and unblocking")
        print("  ✓ Blocked users list management")
        print("  ✓ Discover endpoint filtering")
        print("  ✓ Profile access restrictions")
        print("  ✓ Bidirectional blocking behavior")

if __name__ == "__main__":
    tester = ModerationTester()
    tester.run_moderation_tests()