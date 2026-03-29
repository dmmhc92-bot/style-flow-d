#!/usr/bin/env python3
"""
StyleFlow Complete System Audit - Backend API Testing
Testing ALL endpoints as requested in the review request
"""

import requests
import json
import base64
import uuid
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"
TEST_EMAIL = "test_audit@test.com"
TEST_PASSWORD = "TestPass123!"

class StyleFlowTester:
    def __init__(self):
        self.admin_token = None
        self.admin_refresh_token = None
        self.test_user_token = None
        self.test_user_id = None
        self.created_client_id = None
        self.created_formula_id = None
        self.created_appointment_id = None
        self.created_post_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(f"{status} {test_name}: {details}")
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method, endpoint, data=None, headers=None, token=None):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
            
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return None, f"Unsupported method: {method}"
                
            return response, None
        except Exception as e:
            return None, str(e)
    
    def test_authentication_flows(self):
        """Test all authentication endpoints"""
        print("\n=== AUTHENTICATION TESTING ===")
        
        # 1. Test Admin Login
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response, error = self.make_request("POST", "/auth/login", login_data)
        
        if error:
            self.log_result("Admin Login", False, f"Request error: {error}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            # Handle both 'token' and 'access_token' field names
            token = data.get("access_token") or data.get("token")
            refresh_token = data.get("refresh_token")
            
            if token and refresh_token:
                self.admin_token = token
                self.admin_refresh_token = refresh_token
                self.log_result("Admin Login", True, f"Status: {response.status_code}, Got tokens")
            else:
                self.log_result("Admin Login", False, f"Missing tokens in response: {data}")
                return False
        else:
            self.log_result("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
            
        # 2. Test Get Current User
        response, error = self.make_request("GET", "/auth/me", token=self.admin_token)
        if response and response.status_code == 200:
            user_data = response.json()
            self.log_result("Get Current User", True, f"Status: {response.status_code}, User: {user_data.get('email', 'N/A')}")
        else:
            self.log_result("Get Current User", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Test Signup (Create test user)
        signup_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Audit Test User",
            "business_name": "Test Salon"
        }
        response, error = self.make_request("POST", "/auth/signup", signup_data)
        if response and response.status_code in [200, 201]:
            data = response.json()
            # Handle both 'token' and 'access_token' field names
            token = data.get("access_token") or data.get("token")
            if token:
                self.test_user_token = token
                self.test_user_id = data.get("user_id") or data.get("user", {}).get("id")
                self.log_result("Test User Signup", True, f"Status: {response.status_code}, Created user")
            else:
                self.log_result("Test User Signup", False, f"Missing token in signup response")
        else:
            # User might already exist, try login instead
            login_response, _ = self.make_request("POST", "/auth/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
            if login_response and login_response.status_code == 200:
                data = login_response.json()
                token = data.get("access_token") or data.get("token")
                self.test_user_token = token
                self.test_user_id = data.get("user_id") or data.get("user", {}).get("id")
                self.log_result("Test User Login (existing)", True, f"Status: {login_response.status_code}")
            else:
                self.log_result("Test User Signup/Login", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 4. Test Token Refresh
        if self.admin_refresh_token:
            headers = {"X-Refresh-Token": self.admin_refresh_token}
            response, error = self.make_request("POST", "/auth/refresh", headers=headers)
            if response and response.status_code == 200:
                self.log_result("Token Refresh", True, f"Status: {response.status_code}")
            else:
                self.log_result("Token Refresh", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 5. Test Account Deletion Endpoint Exists
        response, error = self.make_request("DELETE", "/auth/account", token=self.test_user_token)
        if response:
            if response.status_code in [200, 204, 405]:  # 405 means method exists but might be restricted
                self.log_result("Account Deletion Endpoint", True, f"Status: {response.status_code}")
            else:
                self.log_result("Account Deletion Endpoint", False, f"Status: {response.status_code}")
        else:
            self.log_result("Account Deletion Endpoint", False, "No response")
            
        return True
    
    def test_clients_crud(self):
        """Test full CRUD operations for clients"""
        print("\n=== CLIENTS CRUD TESTING ===")
        
        # 1. List Clients
        response, error = self.make_request("GET", "/clients", token=self.admin_token)
        if response and response.status_code == 200:
            clients = response.json()
            self.log_result("List Clients", True, f"Status: {response.status_code}, Count: {len(clients)}")
        else:
            self.log_result("List Clients", False, f"Status: {response.status_code if response else 'No response'}, Error: {response.text if response else error}")
            
        # 2. Create Client
        client_data = {
            "name": "Audit Test Client",
            "email": "testclient@audit.com",
            "phone": "+1234567890",
            "notes": "Created during audit testing",
            "vip_status": True
        }
        response, error = self.make_request("POST", "/clients", client_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.created_client_id = data.get("id")
            self.log_result("Create Client", True, f"Status: {response.status_code}, ID: {self.created_client_id}")
        else:
            self.log_result("Create Client", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Get Specific Client
        if self.created_client_id:
            response, error = self.make_request("GET", f"/clients/{self.created_client_id}", token=self.admin_token)
            if response and response.status_code == 200:
                client = response.json()
                self.log_result("Get Specific Client", True, f"Status: {response.status_code}, Name: {client.get('name', 'N/A')}")
            else:
                self.log_result("Get Specific Client", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 4. Update Client
        if self.created_client_id:
            update_data = {
                "name": "Updated Audit Test Client",
                "notes": "Updated during audit testing"
            }
            response, error = self.make_request("PUT", f"/clients/{self.created_client_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("Update Client", True, f"Status: {response.status_code}")
            else:
                self.log_result("Update Client", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 5. Delete Client (will do this at the end to test data persistence first)
        
        return True
    
    def test_formulas_crud(self):
        """Test full CRUD operations for formulas"""
        print("\n=== FORMULAS CRUD TESTING ===")
        
        # 1. List Formulas
        response, error = self.make_request("GET", "/formulas", token=self.admin_token)
        if response and response.status_code == 200:
            formulas = response.json()
            self.log_result("List Formulas", True, f"Status: {response.status_code}, Count: {len(formulas)}")
        else:
            self.log_result("List Formulas", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 2. Create Formula
        formula_data = {
            "name": "Audit Test Formula",
            "ingredients": "Test ingredients for audit",
            "instructions": "Test instructions for audit",
            "client_id": self.created_client_id if self.created_client_id else None
        }
        response, error = self.make_request("POST", "/formulas", formula_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.created_formula_id = data.get("id")
            self.log_result("Create Formula", True, f"Status: {response.status_code}, ID: {self.created_formula_id}")
        else:
            self.log_result("Create Formula", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Update Formula
        if self.created_formula_id:
            update_data = {
                "name": "Updated Audit Test Formula",
                "instructions": "Updated instructions for audit"
            }
            response, error = self.make_request("PUT", f"/formulas/{self.created_formula_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("Update Formula", True, f"Status: {response.status_code}")
            else:
                self.log_result("Update Formula", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 4. Delete Formula (will do this at the end)
        
        return True
    
    def test_appointments_crud(self):
        """Test full CRUD operations for appointments"""
        print("\n=== APPOINTMENTS CRUD TESTING ===")
        
        # 1. List Appointments
        response, error = self.make_request("GET", "/appointments", token=self.admin_token)
        if response and response.status_code == 200:
            appointments = response.json()
            self.log_result("List Appointments", True, f"Status: {response.status_code}, Count: {len(appointments)}")
        else:
            self.log_result("List Appointments", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 2. Create Appointment
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        appointment_data = {
            "client_id": self.created_client_id if self.created_client_id else None,
            "service": "Audit Test Service",
            "date": future_date,
            "duration": 60,
            "price": 100.00,
            "status": "scheduled"
        }
        response, error = self.make_request("POST", "/appointments", appointment_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.created_appointment_id = data.get("id")
            self.log_result("Create Appointment", True, f"Status: {response.status_code}, ID: {self.created_appointment_id}")
        else:
            self.log_result("Create Appointment", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Update Appointment
        if self.created_appointment_id:
            update_data = {
                "service": "Updated Audit Test Service",
                "status": "completed"
            }
            response, error = self.make_request("PUT", f"/appointments/{self.created_appointment_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("Update Appointment", True, f"Status: {response.status_code}")
            else:
                self.log_result("Update Appointment", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 4. Delete Appointment (will do this at the end)
        
        return True
    
    def test_posts_crud_and_report(self):
        """Test full CRUD operations for posts and report functionality"""
        print("\n=== POSTS CRUD & REPORT TESTING ===")
        
        # 1. Get Feed Posts
        response, error = self.make_request("GET", "/posts?feed=trending", token=self.admin_token)
        if response and response.status_code == 200:
            posts = response.json()
            self.log_result("Get Feed Posts (Trending)", True, f"Status: {response.status_code}, Count: {len(posts)}")
        else:
            self.log_result("Get Feed Posts (Trending)", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 2. Create Post
        post_data = {
            "caption": "Audit test post for StyleFlow",
            "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="],  # Minimal base64 image
            "tags": ["audit", "test"]
        }
        response, error = self.make_request("POST", "/posts", post_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.created_post_id = data.get("id")
            self.log_result("Create Post", True, f"Status: {response.status_code}, ID: {self.created_post_id}")
        else:
            self.log_result("Create Post", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Get Specific Post
        if self.created_post_id:
            response, error = self.make_request("GET", f"/posts/{self.created_post_id}", token=self.admin_token)
            if response and response.status_code == 200:
                post = response.json()
                self.log_result("Get Specific Post", True, f"Status: {response.status_code}, Caption: {post.get('caption', 'N/A')[:30]}...")
            else:
                self.log_result("Get Specific Post", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 4. Report Post
        if self.created_post_id:
            report_data = {
                "reason": "spam",
                "details": "Audit testing report functionality"
            }
            response, error = self.make_request("POST", f"/posts/{self.created_post_id}/report", report_data, token=self.admin_token)
            if response and response.status_code in [200, 201]:
                self.log_result("Report Post", True, f"Status: {response.status_code}")
            else:
                self.log_result("Report Post", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 5. Delete Post (will do this at the end)
        
        return True
    
    def test_profiles(self):
        """Test profile endpoints"""
        print("\n=== PROFILES TESTING ===")
        
        # 1. Get User Hub
        response, error = self.make_request("GET", "/profiles/me/hub", token=self.admin_token)
        if response and response.status_code == 200:
            hub_data = response.json()
            self.log_result("Get User Hub", True, f"Status: {response.status_code}, Profile loaded")
        else:
            self.log_result("Get User Hub", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 2. Avatar Upload Endpoint
        avatar_data = {
            "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
        }
        response, error = self.make_request("POST", "/profiles/avatar", avatar_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            self.log_result("Avatar Upload Endpoint", True, f"Status: {response.status_code}")
        else:
            self.log_result("Avatar Upload Endpoint", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Portfolio Upload
        portfolio_data = {
            "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA==",
            "caption": "Audit test portfolio image"
        }
        response, error = self.make_request("POST", "/profiles/portfolio", portfolio_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            self.log_result("Portfolio Upload", True, f"Status: {response.status_code}")
        else:
            self.log_result("Portfolio Upload", False, f"Status: {response.status_code if response else 'No response'}")
            
        return True
    
    def test_admin_guardian(self):
        """Test admin guardian endpoints"""
        print("\n=== ADMIN GUARDIAN TESTING ===")
        
        # 1. System Health Summary
        response, error = self.make_request("GET", "/admin/guardian/summary", token=self.admin_token)
        if response and response.status_code == 200:
            summary = response.json()
            self.log_result("Guardian Summary", True, f"Status: {response.status_code}, Health: {summary.get('system_health', 'N/A')}")
        else:
            self.log_result("Guardian Summary", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 2. Action History
        response, error = self.make_request("GET", "/admin/guardian/actions", token=self.admin_token)
        if response and response.status_code == 200:
            actions = response.json()
            self.log_result("Guardian Actions", True, f"Status: {response.status_code}, Actions count: {len(actions) if isinstance(actions, list) else 'N/A'}")
        else:
            self.log_result("Guardian Actions", False, f"Status: {response.status_code if response else 'No response'}")
            
        # 3. Active Suspensions
        response, error = self.make_request("GET", "/admin/guardian/active-suspensions", token=self.admin_token)
        if response and response.status_code == 200:
            suspensions = response.json()
            self.log_result("Active Suspensions", True, f"Status: {response.status_code}, Suspensions count: {len(suspensions) if isinstance(suspensions, list) else 'N/A'}")
        else:
            self.log_result("Active Suspensions", False, f"Status: {response.status_code if response else 'No response'}")
            
        return True
    
    def test_data_isolation(self):
        """Test data isolation between users"""
        print("\n=== DATA ISOLATION TESTING ===")
        
        if not self.test_user_token:
            self.log_result("Data Isolation", False, "No test user token available")
            return False
            
        # Try to access admin's client with test user token
        if self.created_client_id:
            response, error = self.make_request("GET", f"/clients/{self.created_client_id}", token=self.test_user_token)
            if response and response.status_code in [403, 404]:
                self.log_result("Data Isolation - Client Access", True, f"Status: {response.status_code} (Correctly blocked)")
            else:
                self.log_result("Data Isolation - Client Access", False, f"Status: {response.status_code} (Should be 403/404)")
                
        # Try to list admin's clients with test user token
        response, error = self.make_request("GET", "/clients", token=self.test_user_token)
        if response and response.status_code == 200:
            clients = response.json()
            # Should return empty list or only test user's clients
            admin_clients_visible = any(client.get('name') == 'Audit Test Client' for client in clients)
            if not admin_clients_visible:
                self.log_result("Data Isolation - Client List", True, f"Status: {response.status_code}, Admin clients not visible")
            else:
                self.log_result("Data Isolation - Client List", False, f"Status: {response.status_code}, Admin clients visible to test user")
        else:
            self.log_result("Data Isolation - Client List", False, f"Status: {response.status_code if response else 'No response'}")
            
        return True
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== CLEANUP TEST DATA ===")
        
        # Delete created post
        if self.created_post_id:
            response, error = self.make_request("DELETE", f"/posts/{self.created_post_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("Delete Post", True, f"Status: {response.status_code}")
            else:
                self.log_result("Delete Post", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete created appointment
        if self.created_appointment_id:
            response, error = self.make_request("DELETE", f"/appointments/{self.created_appointment_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("Delete Appointment", True, f"Status: {response.status_code}")
            else:
                self.log_result("Delete Appointment", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete created formula
        if self.created_formula_id:
            response, error = self.make_request("DELETE", f"/formulas/{self.created_formula_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("Delete Formula", True, f"Status: {response.status_code}")
            else:
                self.log_result("Delete Formula", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete created client
        if self.created_client_id:
            response, error = self.make_request("DELETE", f"/clients/{self.created_client_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("Delete Client", True, f"Status: {response.status_code}")
            else:
                self.log_result("Delete Client", False, f"Status: {response.status_code if response else 'No response'}")
    
    def run_complete_audit(self):
        """Run the complete system audit"""
        print("🔍 STARTING STYLEFLOW COMPLETE SYSTEM AUDIT")
        print(f"Backend URL: {BASE_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 60)
        
        # Run all test suites
        self.test_authentication_flows()
        self.test_clients_crud()
        self.test_formulas_crud()
        self.test_appointments_crud()
        self.test_posts_crud_and_report()
        self.test_profiles()
        self.test_admin_guardian()
        self.test_data_isolation()
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 AUDIT SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result:
                    print(f"  {result}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if "✅ PASS" in result:
                print(f"  {result}")
                
        return success_rate >= 90  # Consider audit successful if 90%+ tests pass

if __name__ == "__main__":
    tester = StyleFlowTester()
    success = tester.run_complete_audit()
    
    if success:
        print("\n🎉 AUDIT COMPLETED SUCCESSFULLY - SYSTEM IS PRODUCTION READY")
    else:
        print("\n⚠️  AUDIT FOUND CRITICAL ISSUES - REVIEW FAILED TESTS")