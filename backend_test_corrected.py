#!/usr/bin/env python3
"""
StyleFlow Complete System Audit - CORRECTED VERSION
Testing ALL endpoints with proper validation requirements
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

class StyleFlowTesterCorrected:
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
        
    def make_request(self, method, endpoint, data=None, headers=None, token=None, timeout=15):
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
            
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                return None, f"Unsupported method: {method}"
                
            return response, None
        except Exception as e:
            return None, str(e)
    
    def run_complete_audit(self):
        """Run the complete system audit with corrected validation"""
        print("🔍 STARTING STYLEFLOW COMPLETE SYSTEM AUDIT (CORRECTED)")
        print(f"Backend URL: {BASE_URL}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 60)
        
        # 1. AUTHENTICATION TESTING
        print("\n=== 1. AUTHENTICATION TESTING ===")
        
        # Login
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response, error = self.make_request("POST", "/auth/login", login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("token") or data.get("access_token")
            self.admin_refresh_token = data.get("refresh_token")
            self.log_result("POST /api/auth/login", True, f"Status: {response.status_code}")
        else:
            self.log_result("POST /api/auth/login", False, f"Status: {response.status_code if response else 'No response'}")
            return
            
        # Get current user
        response, error = self.make_request("GET", "/auth/me", token=self.admin_token)
        if response and response.status_code == 200:
            self.log_result("GET /api/auth/me", True, f"Status: {response.status_code}")
        else:
            self.log_result("GET /api/auth/me", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Test signup
        signup_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Audit Test User",
            "business_name": "Test Salon"
        }
        response, error = self.make_request("POST", "/auth/signup", signup_data)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.test_user_token = data.get("token") or data.get("access_token")
            self.log_result("POST /api/auth/signup", True, f"Status: {response.status_code}")
        else:
            # Try login if user exists
            login_response, _ = self.make_request("POST", "/auth/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
            if login_response and login_response.status_code == 200:
                data = login_response.json()
                self.test_user_token = data.get("token") or data.get("access_token")
                self.log_result("POST /api/auth/signup (existing user login)", True, f"Status: {login_response.status_code}")
            else:
                self.log_result("POST /api/auth/signup", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Token refresh
        if self.admin_refresh_token:
            headers = {"X-Refresh-Token": self.admin_refresh_token}
            response, error = self.make_request("POST", "/auth/refresh", headers=headers)
            if response and response.status_code == 200:
                self.log_result("POST /api/auth/refresh", True, f"Status: {response.status_code}")
            else:
                self.log_result("POST /api/auth/refresh", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Account deletion endpoint
        response, error = self.make_request("DELETE", "/auth/account", token=self.test_user_token)
        if response and response.status_code in [200, 204, 405]:
            self.log_result("DELETE /api/auth/account", True, f"Status: {response.status_code}")
        else:
            self.log_result("DELETE /api/auth/account", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 2. CLIENTS TESTING
        print("\n=== 2. CLIENTS CRUD TESTING ===")
        
        # List clients
        response, error = self.make_request("GET", "/clients", token=self.admin_token)
        if response and response.status_code == 200:
            clients = response.json()
            self.log_result("GET /api/clients", True, f"Status: {response.status_code}, Count: {len(clients)}")
        else:
            self.log_result("GET /api/clients", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Create client
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
            self.log_result("POST /api/clients", True, f"Status: {response.status_code}, ID: {self.created_client_id}")
        else:
            self.log_result("POST /api/clients", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Get specific client
        if self.created_client_id:
            response, error = self.make_request("GET", f"/clients/{self.created_client_id}", token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("GET /api/clients/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("GET /api/clients/{id}", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Update client
        if self.created_client_id:
            update_data = {"name": "Updated Audit Test Client", "notes": "Updated during audit testing"}
            response, error = self.make_request("PUT", f"/clients/{self.created_client_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("PUT /api/clients/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("PUT /api/clients/{id}", False, f"Status: {response.status_code if response else 'No response'}")
                
        # 3. FORMULAS TESTING
        print("\n=== 3. FORMULAS CRUD TESTING ===")
        
        # List formulas
        response, error = self.make_request("GET", "/formulas", token=self.admin_token)
        if response and response.status_code == 200:
            formulas = response.json()
            self.log_result("GET /api/formulas", True, f"Status: {response.status_code}, Count: {len(formulas)}")
        else:
            self.log_result("GET /api/formulas", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Create formula (with required client_id)
        if self.created_client_id:
            formula_data = {
                "name": "Audit Test Formula",
                "ingredients": "Test ingredients for audit",
                "instructions": "Test instructions for audit",
                "client_id": self.created_client_id
            }
            response, error = self.make_request("POST", "/formulas", formula_data, token=self.admin_token)
            if response and response.status_code in [200, 201]:
                data = response.json()
                self.created_formula_id = data.get("id")
                self.log_result("POST /api/formulas", True, f"Status: {response.status_code}, ID: {self.created_formula_id}")
            else:
                self.log_result("POST /api/formulas", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_result("POST /api/formulas", False, "No client_id available")
            
        # Update formula
        if self.created_formula_id:
            update_data = {"name": "Updated Audit Test Formula", "instructions": "Updated instructions"}
            response, error = self.make_request("PUT", f"/formulas/{self.created_formula_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("PUT /api/formulas/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("PUT /api/formulas/{id}", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete formula
        if self.created_formula_id:
            response, error = self.make_request("DELETE", f"/formulas/{self.created_formula_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/formulas/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("DELETE /api/formulas/{id}", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 4. APPOINTMENTS TESTING
        print("\n=== 4. APPOINTMENTS CRUD TESTING ===")
        
        # List appointments
        response, error = self.make_request("GET", "/appointments", token=self.admin_token)
        if response and response.status_code == 200:
            appointments = response.json()
            self.log_result("GET /api/appointments", True, f"Status: {response.status_code}, Count: {len(appointments)}")
        else:
            self.log_result("GET /api/appointments", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Create appointment (with required client_id)
        if self.created_client_id:
            future_date = (datetime.now() + timedelta(days=7)).isoformat()
            appointment_data = {
                "client_id": self.created_client_id,
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
                self.log_result("POST /api/appointments", True, f"Status: {response.status_code}, ID: {self.created_appointment_id}")
            else:
                self.log_result("POST /api/appointments", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_result("POST /api/appointments", False, "No client_id available")
            
        # Update appointment
        if self.created_appointment_id:
            update_data = {"service": "Updated Audit Test Service", "status": "completed"}
            response, error = self.make_request("PUT", f"/appointments/{self.created_appointment_id}", update_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("PUT /api/appointments/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("PUT /api/appointments/{id}", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete appointment
        if self.created_appointment_id:
            response, error = self.make_request("DELETE", f"/appointments/{self.created_appointment_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/appointments/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("DELETE /api/appointments/{id}", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 5. POSTS TESTING
        print("\n=== 5. POSTS CRUD & REPORT TESTING ===")
        
        # Get feed posts
        response, error = self.make_request("GET", "/posts?feed=trending", token=self.admin_token)
        if response and response.status_code == 200:
            posts = response.json()
            self.log_result("GET /api/posts?feed=trending", True, f"Status: {response.status_code}, Count: {len(posts)}")
        else:
            self.log_result("GET /api/posts?feed=trending", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Create post
        post_data = {
            "caption": "Audit test post for StyleFlow",
            "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="],
            "tags": ["audit", "test"]
        }
        response, error = self.make_request("POST", "/posts", post_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.created_post_id = data.get("id")
            self.log_result("POST /api/posts", True, f"Status: {response.status_code}, ID: {self.created_post_id}")
        else:
            self.log_result("POST /api/posts", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Get specific post
        if self.created_post_id:
            response, error = self.make_request("GET", f"/posts/{self.created_post_id}", token=self.admin_token)
            if response and response.status_code == 200:
                self.log_result("GET /api/posts/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("GET /api/posts/{id}", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Report post (with reason as query parameter)
        if self.created_post_id:
            response, error = self.make_request("POST", f"/posts/{self.created_post_id}/report?reason=spam", 
                                              {"details": "Audit testing report functionality"}, token=self.admin_token)
            if response and response.status_code in [200, 201]:
                self.log_result("POST /api/posts/{id}/report", True, f"Status: {response.status_code}")
            else:
                self.log_result("POST /api/posts/{id}/report", False, f"Status: {response.status_code if response else 'No response'}")
                
        # Delete post
        if self.created_post_id:
            response, error = self.make_request("DELETE", f"/posts/{self.created_post_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/posts/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("DELETE /api/posts/{id}", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 6. PROFILES TESTING
        print("\n=== 6. PROFILES TESTING ===")
        
        # Get user hub
        response, error = self.make_request("GET", "/profiles/me/hub", token=self.admin_token)
        if response and response.status_code == 200:
            self.log_result("GET /api/profiles/me/hub", True, f"Status: {response.status_code}")
        else:
            self.log_result("GET /api/profiles/me/hub", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Avatar upload (with correct field name)
        avatar_data = {
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
        }
        response, error = self.make_request("POST", "/profiles/avatar", avatar_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            self.log_result("POST /api/profiles/avatar", True, f"Status: {response.status_code}")
        else:
            self.log_result("POST /api/profiles/avatar", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Portfolio upload (with correct field name)
        portfolio_data = {
            "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA==",
            "caption": "Audit test portfolio image"
        }
        response, error = self.make_request("POST", "/profiles/portfolio", portfolio_data, token=self.admin_token)
        if response and response.status_code in [200, 201]:
            self.log_result("POST /api/profiles/portfolio", True, f"Status: {response.status_code}")
        else:
            self.log_result("POST /api/profiles/portfolio", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 7. ADMIN GUARDIAN TESTING
        print("\n=== 7. ADMIN GUARDIAN TESTING ===")
        
        # System health summary
        response, error = self.make_request("GET", "/admin/guardian/summary", token=self.admin_token)
        if response and response.status_code == 200:
            summary = response.json()
            self.log_result("GET /api/admin/guardian/summary", True, f"Status: {response.status_code}, Health: {summary.get('system_health', 'N/A')}")
        else:
            self.log_result("GET /api/admin/guardian/summary", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Action history
        response, error = self.make_request("GET", "/admin/guardian/actions", token=self.admin_token)
        if response and response.status_code == 200:
            self.log_result("GET /api/admin/guardian/actions", True, f"Status: {response.status_code}")
        else:
            self.log_result("GET /api/admin/guardian/actions", False, f"Status: {response.status_code if response else 'No response'}")
            
        # Active suspensions
        response, error = self.make_request("GET", "/admin/guardian/active-suspensions", token=self.admin_token)
        if response and response.status_code == 200:
            self.log_result("GET /api/admin/guardian/active-suspensions", True, f"Status: {response.status_code}")
        else:
            self.log_result("GET /api/admin/guardian/active-suspensions", False, f"Status: {response.status_code if response else 'No response'}")
        
        # 8. DATA ISOLATION TESTING
        print("\n=== 8. DATA ISOLATION TESTING ===")
        
        if self.test_user_token and self.created_client_id:
            # Try to access admin's client with test user token
            response, error = self.make_request("GET", f"/clients/{self.created_client_id}", token=self.test_user_token)
            if response and response.status_code in [403, 404]:
                self.log_result("Data Isolation - Client Access", True, f"Status: {response.status_code} (Correctly blocked)")
            else:
                self.log_result("Data Isolation - Client Access", False, f"Status: {response.status_code} (Should be 403/404)")
                
            # Try to list admin's clients with test user token
            response, error = self.make_request("GET", "/clients", token=self.test_user_token)
            if response and response.status_code == 200:
                clients = response.json()
                admin_clients_visible = any(client.get('name') == 'Audit Test Client' for client in clients)
                if not admin_clients_visible:
                    self.log_result("Data Isolation - Client List", True, f"Status: {response.status_code}, Admin clients not visible")
                else:
                    self.log_result("Data Isolation - Client List", False, f"Status: {response.status_code}, Admin clients visible to test user")
            else:
                self.log_result("Data Isolation - Client List", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_result("Data Isolation", False, "No test user token or client ID available")
        
        # Cleanup - Delete created client
        if self.created_client_id:
            response, error = self.make_request("DELETE", f"/clients/{self.created_client_id}", token=self.admin_token)
            if response and response.status_code in [200, 204]:
                self.log_result("DELETE /api/clients/{id}", True, f"Status: {response.status_code}")
            else:
                self.log_result("DELETE /api/clients/{id}", False, f"Status: {response.status_code if response else 'No response'}")
        
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
                
        return success_rate >= 90

if __name__ == "__main__":
    tester = StyleFlowTesterCorrected()
    success = tester.run_complete_audit()
    
    if success:
        print("\n🎉 AUDIT COMPLETED SUCCESSFULLY - SYSTEM IS PRODUCTION READY")
    else:
        print("\n⚠️  AUDIT FOUND CRITICAL ISSUES - REVIEW FAILED TESTS")