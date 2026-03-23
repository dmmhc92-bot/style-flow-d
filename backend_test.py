#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "admin@styleflow.com"
TEST_PASSWORD = "Admin1234!"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")  # Changed from "access_token" to "token"
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("Authentication", "PASS", f"Successfully logged in as {TEST_EMAIL}")
                    print(f"   Token: {self.auth_token[:20]}...")
                    return True
                else:
                    self.log_result("Authentication", "FAIL", f"No token in response: {data}")
                    return False
            else:
                self.log_result("Authentication", "FAIL", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "FAIL", f"Authentication error: {str(e)}")
            return False
    
    def test_get_formula_by_id(self):
        """Test GET /api/formulas/{id} endpoint"""
        try:
            # First, get list of formulas to find an ID
            response = self.session.get(f"{BACKEND_URL}/formulas")
            
            if response.status_code != 200:
                self.log_result("GET /api/formulas/{id}", "FAIL", f"Could not get formulas list: {response.status_code}")
                return
            
            formulas = response.json()
            if not formulas:
                # Create a test formula first
                test_formula = {
                    "client_id": "test_client_123",
                    "formula_name": "Test Formula for ID Test",
                    "formula_details": "Test formula details for endpoint testing"
                }
                
                create_response = self.session.post(f"{BACKEND_URL}/formulas", json=test_formula)
                if create_response.status_code != 200:
                    self.log_result("GET /api/formulas/{id}", "FAIL", f"Could not create test formula: {create_response.status_code}")
                    return
                
                created_formula = create_response.json()
                formula_id = created_formula["id"]
            else:
                formula_id = formulas[0]["id"]
            
            # Now test the GET by ID endpoint
            response = self.session.get(f"{BACKEND_URL}/formulas/{formula_id}")
            
            if response.status_code == 200:
                formula = response.json()
                if formula.get("id") == formula_id:
                    self.log_result("GET /api/formulas/{id}", "PASS", f"Successfully retrieved formula with ID: {formula_id}")
                else:
                    self.log_result("GET /api/formulas/{id}", "FAIL", "Formula ID mismatch in response")
            else:
                self.log_result("GET /api/formulas/{id}", "FAIL", f"Failed to get formula by ID: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("GET /api/formulas/{id}", "FAIL", f"Error testing formula by ID: {str(e)}")
    
    def test_follow_user(self):
        """Test POST /api/users/{id}/follow endpoint"""
        try:
            # First, discover users to find someone to follow
            response = self.session.get(f"{BACKEND_URL}/users/discover")
            
            if response.status_code != 200:
                self.log_result("POST /api/users/{id}/follow", "FAIL", f"Could not discover users: {response.status_code}")
                return
            
            users = response.json()
            if not users:
                self.log_result("POST /api/users/{id}/follow", "FAIL", "No users found to follow")
                return
            
            # Get the first user to follow
            target_user = users[0]
            target_user_id = target_user["id"]
            
            # Test following the user
            response = self.session.post(f"{BACKEND_URL}/users/{target_user_id}/follow")
            
            if response.status_code == 200:
                self.log_result("POST /api/users/{id}/follow", "PASS", f"Successfully followed user: {target_user.get('full_name', target_user_id)}")
                
                # Clean up - unfollow the user
                unfollow_response = self.session.delete(f"{BACKEND_URL}/users/{target_user_id}/follow")
                if unfollow_response.status_code == 200:
                    print(f"   Cleanup: Successfully unfollowed user")
                    
            elif response.status_code == 400 and "already following" in response.text.lower():
                # User is already being followed, try to unfollow first then follow again
                unfollow_response = self.session.delete(f"{BACKEND_URL}/users/{target_user_id}/follow")
                if unfollow_response.status_code == 200:
                    # Now try to follow again
                    follow_response = self.session.post(f"{BACKEND_URL}/users/{target_user_id}/follow")
                    if follow_response.status_code == 200:
                        self.log_result("POST /api/users/{id}/follow", "PASS", f"Successfully followed user after unfollowing: {target_user.get('full_name', target_user_id)}")
                    else:
                        self.log_result("POST /api/users/{id}/follow", "FAIL", f"Failed to follow after unfollow: {follow_response.status_code}")
                else:
                    self.log_result("POST /api/users/{id}/follow", "FAIL", f"User already followed and could not unfollow: {unfollow_response.status_code}")
            else:
                self.log_result("POST /api/users/{id}/follow", "FAIL", f"Failed to follow user: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/users/{id}/follow", "FAIL", f"Error testing follow user: {str(e)}")
    
    def test_create_post(self):
        """Test POST /api/posts endpoint"""
        try:
            # Create test post data
            test_post = {
                "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="],
                "caption": "Test post for endpoint verification",
                "tags": ["#balayage", "#highlights"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/posts", json=test_post)
            
            if response.status_code == 200:
                data = response.json()
                post_id = data.get("id")
                if post_id:
                    self.log_result("POST /api/posts", "PASS", f"Successfully created post with ID: {post_id}")
                    
                    # Clean up - delete the test post
                    delete_response = self.session.delete(f"{BACKEND_URL}/posts/{post_id}")
                    if delete_response.status_code == 200:
                        print(f"   Cleanup: Successfully deleted test post")
                else:
                    self.log_result("POST /api/posts", "FAIL", "Post created but no ID returned")
            else:
                self.log_result("POST /api/posts", "FAIL", f"Failed to create post: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("POST /api/posts", "FAIL", f"Error testing post creation: {str(e)}")
    
    def run_tests(self):
        """Run all specified tests"""
        print("=" * 60)
        print("BACKEND ENDPOINT VERIFICATION TESTS")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {TEST_EMAIL}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        print("\nRunning endpoint tests...")
        print("-" * 40)
        
        # Test the three specific endpoints
        self.test_get_formula_by_id()
        self.test_follow_user()
        self.test_create_post()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        total = len(self.test_results)
        
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_symbol} {result['test']}: {result['status']}")
        
        print(f"\nOverall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - see details above")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)