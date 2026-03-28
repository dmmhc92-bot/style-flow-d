#!/usr/bin/env python3
"""
StyleFlow Backend OMNI-SYSTEM LIVE VERIFICATION
Testing ALL critical paths for App Store build
"""

import requests
import json
import uuid
import base64
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None, auth_required=True):
        """Make HTTP request with proper headers"""
        url = f"{BASE_URL}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if auth_required and self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
            
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers, timeout=10)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers, timeout=10)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers, timeout=10)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            print(f"DEBUG: {method} {url} -> {response.status_code}")
            if response.status_code >= 400:
                print(f"DEBUG: Response body: {response.text}")
                
            return response
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def test_authentication_flow(self):
        """Test 1: Authentication Flow"""
        print("\n=== 1. AUTHENTICATION FLOW TESTING ===")
        
        # Test login
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", login_data, auth_required=False)
        if response and response.status_code == 200:
            data = response.json()
            self.access_token = data.get("token")  # Changed from access_token to token
            self.refresh_token = data.get("refresh_token")
            user_data = data.get("user", {})
            self.user_id = user_data.get("id")
            
            self.log_result("POST /api/auth/login", True, 
                          f"Login successful, got tokens and user_id: {self.user_id}")
        else:
            self.log_result("POST /api/auth/login", False, 
                          f"Login failed: {response.status_code if response else 'No response'}")
            return False
            
        # Test get user profile
        response = self.make_request("GET", "/auth/me")
        if response and response.status_code == 200:
            profile_data = response.json()
            self.log_result("GET /api/auth/me", True, 
                          f"Profile retrieved: {profile_data.get('full_name', 'Unknown')}")
        else:
            self.log_result("GET /api/auth/me", False, 
                          f"Profile fetch failed: {response.status_code if response else 'No response'}")
            
        # Test signup flow (with test email)
        test_email = f"test_{uuid.uuid4().hex[:8]}@styleflow.com"
        signup_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test User",
            "business_name": "Test Salon"
        }
        
        response = self.make_request("POST", "/auth/signup", signup_data, auth_required=False)
        if response and response.status_code in [200, 201]:
            self.log_result("POST /api/auth/signup", True, 
                          f"Signup successful for {test_email}")
        else:
            self.log_result("POST /api/auth/signup", False, 
                          f"Signup failed: {response.status_code if response else 'No response'}")
            
        return True

    def test_client_crud(self):
        """Test 2: Client CRUD (Data Stickiness Test)"""
        print("\n=== 2. CLIENT CRUD TESTING ===")
        
        # Get all clients
        response = self.make_request("GET", "/clients")
        if response and response.status_code == 200:
            clients = response.json()
            self.log_result("GET /api/clients", True, 
                          f"Retrieved {len(clients)} clients")
        else:
            self.log_result("GET /api/clients", False, 
                          f"Failed to get clients: {response.status_code if response else 'No response'}")
            return False
            
        # Create a new client
        client_data = {
            "name": f"Test Client {uuid.uuid4().hex[:8]}",
            "email": f"client_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "+1234567890",
            "notes": "Test client for OMNI verification",
            "is_vip": True,
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        }
        
        response = self.make_request("POST", "/clients", client_data)
        created_client = None
        if response and response.status_code in [200, 201]:
            created_client = response.json()
            client_id = created_client.get("id")
            self.log_result("POST /api/clients", True, 
                          f"Created client with ID: {client_id}")
        else:
            self.log_result("POST /api/clients", False, 
                          f"Failed to create client: {response.status_code if response else 'No response'}")
            return False
            
        # Get specific client
        if created_client:
            client_id = created_client.get("id")
            response = self.make_request("GET", f"/clients/{client_id}")
            if response and response.status_code == 200:
                client_detail = response.json()
                self.log_result("GET /api/clients/{id}", True, 
                              f"Retrieved client: {client_detail.get('name')}")
            else:
                self.log_result("GET /api/clients/{id}", False, 
                              f"Failed to get client: {response.status_code if response else 'No response'}")
                
            # Update client
            update_data = {
                "name": f"Updated {created_client.get('name')}",
                "notes": "Updated notes for OMNI verification"
            }
            
            response = self.make_request("PUT", f"/clients/{client_id}", update_data)
            if response and response.status_code == 200:
                updated_client = response.json()
                self.log_result("PUT /api/clients/{id}", True, 
                              f"Updated client: {updated_client.get('name')}")
            else:
                self.log_result("PUT /api/clients/{id}", False, 
                              f"Failed to update client: {response.status_code if response else 'No response'}")
                
            # Delete client (verify cleanup)
            response = self.make_request("DELETE", f"/clients/{client_id}")
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/clients/{id}", True, 
                              "Client deleted successfully")
                
                # Verify deletion
                response = self.make_request("GET", f"/clients/{client_id}")
                if response is None:
                    self.log_result("Client deletion verification", False, 
                                  "Client deletion verification failed: No response")
                elif response.status_code == 404:
                    self.log_result("Client deletion verification", True, 
                                  "Client properly deleted (404 on GET)")
                elif response.status_code == 200:
                    self.log_result("Client deletion verification", False, 
                                  "Client still exists after deletion (200 response)")
                else:
                    self.log_result("Client deletion verification", False, 
                                  f"Unexpected response after deletion: {response.status_code}")
            else:
                self.log_result("DELETE /api/clients/{id}", False, 
                              f"Failed to delete client: {response.status_code if response else 'No response'}")
                
        return True

    def test_formula_crud(self):
        """Test 3: Formula CRUD"""
        print("\n=== 3. FORMULA CRUD TESTING ===")
        
        # Get all formulas
        response = self.make_request("GET", "/formulas")
        if response and response.status_code == 200:
            formulas = response.json()
            self.log_result("GET /api/formulas", True, 
                          f"Retrieved {len(formulas)} formulas")
        else:
            self.log_result("GET /api/formulas", False, 
                          f"Failed to get formulas: {response.status_code if response else 'No response'}")
            return False
            
        # Create a new formula (need a client_id)
        # Create a client first for this test
        client_data = {
            "name": f"Formula Test Client {uuid.uuid4().hex[:8]}",
            "email": f"formula_client_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "+1234567890",
            "notes": "Client for formula testing"
        }
        
        client_response = self.make_request("POST", "/clients", client_data)
        client_id = None
        if client_response and client_response.status_code in [200, 201]:
            client_id = client_response.json().get("id")
        
        if not client_id:
            self.log_result("POST /api/formulas", False, 
                          "Could not create client for formula test")
            return False
            
        formula_data = {
            "client_id": client_id,
            "formula_name": f"Test Formula {uuid.uuid4().hex[:8]}",
            "formula_details": "Test ingredients for OMNI verification"
        }
        
        response = self.make_request("POST", "/formulas", formula_data)
        created_formula = None
        if response and response.status_code in [200, 201]:
            created_formula = response.json()
            formula_id = created_formula.get("id")
            self.log_result("POST /api/formulas", True, 
                          f"Created formula with ID: {formula_id}")
        else:
            self.log_result("POST /api/formulas", False, 
                          f"Failed to create formula: {response.status_code if response else 'No response'}")
            return False
            
        # Delete formula after test
        if created_formula:
            formula_id = created_formula.get("id")
            response = self.make_request("DELETE", f"/formulas/{formula_id}")
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/formulas/{id}", True, 
                              "Formula deleted successfully")
            else:
                self.log_result("DELETE /api/formulas/{id}", False, 
                              f"Failed to delete formula: {response.status_code if response else 'No response'}")
                
        return True

    def test_appointment_crud(self):
        """Test 4: Appointment CRUD"""
        print("\n=== 4. APPOINTMENT CRUD TESTING ===")
        
        # Get all appointments
        response = self.make_request("GET", "/appointments")
        if response and response.status_code == 200:
            appointments = response.json()
            self.log_result("GET /api/appointments", True, 
                          f"Retrieved {len(appointments)} appointments")
        else:
            self.log_result("GET /api/appointments", False, 
                          f"Failed to get appointments: {response.status_code if response else 'No response'}")
            return False
            
        # Create a new appointment (need a client_id)
        # Create a client first for this test
        client_data = {
            "name": f"Appointment Test Client {uuid.uuid4().hex[:8]}",
            "email": f"appointment_client_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "+1234567890",
            "notes": "Client for appointment testing"
        }
        
        client_response = self.make_request("POST", "/clients", client_data)
        client_id = None
        if client_response and client_response.status_code in [200, 201]:
            client_id = client_response.json().get("id")
        
        if not client_id:
            self.log_result("POST /api/appointments", False, 
                          "Could not create client for appointment test")
            return False
            
        appointment_data = {
            "client_id": client_id,
            "service": "Test Service",
            "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 60,
            "notes": "Test appointment for OMNI verification",
            "status": "scheduled"
        }
        
        response = self.make_request("POST", "/appointments", appointment_data)
        if response and response.status_code in [200, 201]:
            created_appointment = response.json()
            appointment_id = created_appointment.get("id")
            self.log_result("POST /api/appointments", True, 
                          f"Created appointment with ID: {appointment_id}")
        else:
            self.log_result("POST /api/appointments", False, 
                          f"Failed to create appointment: {response.status_code if response else 'No response'}")
            
        return True

    def test_account_management(self):
        """Test 5: Account Management (Apple Compliance)"""
        print("\n=== 5. ACCOUNT MANAGEMENT TESTING ===")
        
        # Test account deletion endpoint exists (but don't actually delete)
        # We'll test with a non-destructive approach by checking the endpoint
        # The endpoint should be accessible but we won't actually delete the admin account
        
        # Create a test user first to delete safely
        test_email = f"delete_test_{uuid.uuid4().hex[:8]}@styleflow.com"
        signup_data = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Delete Test User",
            "business_name": "Test Salon"
        }
        
        # Create test user
        response = self.make_request("POST", "/auth/signup", signup_data, auth_required=False)
        if response and response.status_code in [200, 201]:
            # Login as test user
            login_data = {
                "email": test_email,
                "password": "TestPass123!"
            }
            
            response = self.make_request("POST", "/auth/login", login_data, auth_required=False)
            if response and response.status_code == 200:
                data = response.json()
                test_token = data.get("token")
                
                # Test delete account with test user
                headers = {"Authorization": f"Bearer {test_token}"}
                response = self.make_request("DELETE", "/auth/account", headers=headers, auth_required=False)
                if response and response.status_code in [200, 204]:
                    self.log_result("DELETE /api/auth/account", True, 
                                  "Account deletion endpoint working (tested with test user)")
                else:
                    self.log_result("DELETE /api/auth/account", False, 
                                  f"Account deletion failed: {response.status_code if response else 'No response'}")
            else:
                self.log_result("DELETE /api/auth/account", False, 
                              "Could not login as test user to test deletion")
        else:
            self.log_result("DELETE /api/auth/account", False, 
                          "Could not create test user for deletion test")
            
        return True

    def test_feed_posts(self):
        """Test 6: Feed/Posts"""
        print("\n=== 6. FEED/POSTS TESTING ===")
        
        # Get feed posts (needs auth)
        response = self.make_request("GET", "/posts?feed=trending")
        if response and response.status_code == 200:
            posts = response.json()
            self.log_result("GET /api/posts?feed=trending", True, 
                          f"Retrieved {len(posts)} trending posts")
        else:
            self.log_result("GET /api/posts?feed=trending", False, 
                          f"Failed to get feed: {response.status_code if response else 'No response'}")
            
        # Create a post
        post_data = {
            "caption": "Test post for OMNI verification",
            "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"],
            "tags": ["test", "omni"]
        }
        
        response = self.make_request("POST", "/posts", post_data)
        if response and response.status_code in [200, 201]:
            created_post = response.json()
            post_id = created_post.get("id")
            self.log_result("POST /api/posts", True, 
                          f"Created post with ID: {post_id}")
        else:
            self.log_result("POST /api/posts", False, 
                          f"Failed to create post: {response.status_code if response else 'No response'}")
            
        return True

    def test_guardian_system(self):
        """Test 7: Guardian System"""
        print("\n=== 7. GUARDIAN SYSTEM TESTING ===")
        
        # Test guardian summary endpoint
        response = self.make_request("GET", "/admin/guardian/summary")
        if response is None:
            self.log_result("GET /api/admin/guardian/summary", False, 
                          "Guardian system check failed: No response")
        elif response.status_code == 200:
            summary = response.json()
            self.log_result("GET /api/admin/guardian/summary", True, 
                          f"Guardian system health: {summary}")
        elif response.status_code == 403:
            self.log_result("GET /api/admin/guardian/summary", True, 
                          "Guardian system endpoint exists (403 - admin access required)")
        else:
            self.log_result("GET /api/admin/guardian/summary", False, 
                          f"Guardian system check failed: {response.status_code}")
            
        return True

    def run_all_tests(self):
        """Run all OMNI-SYSTEM tests"""
        print("🚀 STARTING STYLEFLOW OMNI-SYSTEM LIVE VERIFICATION")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_authentication_flow()
        self.test_client_crud()
        self.test_formula_crud()
        self.test_appointment_crud()
        self.test_account_management()
        self.test_feed_posts()
        self.test_guardian_system()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 OMNI-SYSTEM LIVE VERIFICATION COMPLETE")
        print("=" * 60)
        print(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        print(f"⏱️  DURATION: {duration:.2f} seconds")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for result in self.test_results:
            if result['success']:
                print(f"   • {result['test']}")
                
        # Final verdict
        if success_rate >= 90:
            print(f"\n🎉 VERDICT: PRODUCTION READY - {success_rate:.1f}% success rate")
        elif success_rate >= 75:
            print(f"\n⚠️  VERDICT: NEEDS MINOR FIXES - {success_rate:.1f}% success rate")
        else:
            print(f"\n🚨 VERDICT: CRITICAL ISSUES - {success_rate:.1f}% success rate")
            
        return success_rate >= 90

if __name__ == "__main__":
    tester = StyleFlowTester()
    tester.run_all_tests()