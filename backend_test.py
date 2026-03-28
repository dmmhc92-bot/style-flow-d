#!/usr/bin/env python3
"""
StyleFlow Backend Critical Audit Testing
=========================================

This script tests the critical audit items for StyleFlow backend:
1. Data Stickiness/Isolation - User-scoped data protection
2. Client CRUD endpoints - Full CRUD operations
3. Authentication - JWT token handling
4. Profile endpoints - User profile management

Admin credentials: admin@styleflow.com / Admin1234!
Backend URL: https://hairflow-app-1.preview.emergentagent.com/api
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_user_id = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_client_id = None
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        
        # Set up headers
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}", 0
                
            try:
                response_data = response.json()
            except:
                response_data = response.text
                
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}", 0

    def test_admin_authentication(self):
        """Test 1: Admin Authentication - JWT token handling"""
        print("🔐 Testing Admin Authentication...")
        
        # Test login
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        success, response, status_code = self.make_request("POST", "/auth/login", login_data)
        
        if success and "token" in response:
            self.admin_token = response["token"]
            self.admin_user_id = response.get("user", {}).get("id")
            self.log_result(
                "Admin Login", 
                True, 
                f"Successfully authenticated admin user. Token received, User ID: {self.admin_user_id}"
            )
            
            # Test /auth/me endpoint
            success, me_response, _ = self.make_request("GET", "/auth/me", token=self.admin_token)
            if success and "is_tester" in me_response:
                self.log_result(
                    "Auth Me Endpoint", 
                    True, 
                    f"GET /api/auth/me working. is_tester: {me_response.get('is_tester')}, is_admin: {me_response.get('is_admin')}"
                )
            else:
                self.log_result("Auth Me Endpoint", False, "Failed to get user profile", me_response)
                
        else:
            self.log_result("Admin Login", False, f"Login failed with status {status_code}", response)
            return False
            
        return True

    def create_test_user(self):
        """Create a separate test user for data isolation testing"""
        print("👤 Creating Test User for Data Isolation...")
        
        test_email = f"testuser_{uuid.uuid4().hex[:8]}@styleflow.com"
        signup_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "full_name": "Test User",
            "business_name": "Test Salon"
        }
        
        success, response, status_code = self.make_request("POST", "/auth/signup", signup_data)
        
        if success and "token" in response:
            self.test_user_token = response["token"]
            self.test_user_id = response.get("user", {}).get("id")
            self.log_result(
                "Test User Creation", 
                True, 
                f"Created test user: {test_email}, User ID: {self.test_user_id}"
            )
            return True
        else:
            self.log_result("Test User Creation", False, f"Failed to create test user. Status: {status_code}", response)
            return False

    def test_client_crud_operations(self):
        """Test 2: Client CRUD endpoints with admin credentials"""
        print("📋 Testing Client CRUD Operations...")
        
        if not self.admin_token:
            self.log_result("Client CRUD Setup", False, "No admin token available")
            return False
            
        # Test GET /api/clients - list all clients
        success, clients_response, status_code = self.make_request("GET", "/clients", token=self.admin_token)
        
        if success:
            client_count = len(clients_response) if isinstance(clients_response, list) else 0
            self.log_result(
                "GET /api/clients", 
                True, 
                f"Successfully retrieved {client_count} clients for authenticated user"
            )
        else:
            self.log_result("GET /api/clients", False, f"Failed to get clients. Status: {status_code}", clients_response)
            
        # Test POST /api/clients - create a new client
        client_data = {
            "name": f"Test Client {uuid.uuid4().hex[:6]}",
            "email": f"client_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "notes": "Test client for audit",
            "is_vip": False,
            "rebook_interval_days": 42
        }
        
        success, create_response, status_code = self.make_request("POST", "/clients", client_data, token=self.admin_token)
        
        if success and "id" in create_response:
            self.test_client_id = create_response["id"]
            self.log_result(
                "POST /api/clients", 
                True, 
                f"Successfully created client. ID: {self.test_client_id}"
            )
            
            # Test PUT /api/clients/{id} - update client
            update_data = {
                "name": f"Updated Test Client {uuid.uuid4().hex[:6]}",
                "notes": "Updated notes for audit testing",
                "is_vip": True
            }
            
            success, update_response, status_code = self.make_request(
                "PUT", f"/clients/{self.test_client_id}", update_data, token=self.admin_token
            )
            
            if success:
                self.log_result(
                    "PUT /api/clients/{id}", 
                    True, 
                    f"Successfully updated client. VIP status: {update_response.get('is_vip')}"
                )
            else:
                self.log_result("PUT /api/clients/{id}", False, f"Failed to update client. Status: {status_code}", update_response)
                
            # Test DELETE /api/clients/{id} - delete client
            success, delete_response, status_code = self.make_request(
                "DELETE", f"/clients/{self.test_client_id}", token=self.admin_token
            )
            
            if success:
                self.log_result(
                    "DELETE /api/clients/{id}", 
                    True, 
                    "Successfully deleted client"
                )
            else:
                self.log_result("DELETE /api/clients/{id}", False, f"Failed to delete client. Status: {status_code}", delete_response)
                
        else:
            self.log_result("POST /api/clients", False, f"Failed to create client. Status: {status_code}", create_response)

    def test_data_isolation(self):
        """Test 3: Data Stickiness/Isolation - Verify user-scoped data"""
        print("🔒 Testing Data Isolation and User-Scoped Access...")
        
        if not self.admin_token or not self.test_user_token:
            self.log_result("Data Isolation Setup", False, "Missing required tokens for isolation testing")
            return False
            
        # Create a client as admin user
        admin_client_data = {
            "name": f"Admin Client {uuid.uuid4().hex[:6]}",
            "email": f"admin_client_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1111111111",
            "notes": "Admin's private client data"
        }
        
        success, admin_client_response, _ = self.make_request("POST", "/clients", admin_client_data, token=self.admin_token)
        
        if not success or "id" not in admin_client_response:
            self.log_result("Data Isolation - Admin Client Creation", False, "Failed to create admin client", admin_client_response)
            return False
            
        admin_client_id = admin_client_response["id"]
        self.log_result(
            "Data Isolation - Admin Client Creation", 
            True, 
            f"Created admin client with ID: {admin_client_id}"
        )
        
        # Create a client as test user
        test_client_data = {
            "name": f"Test User Client {uuid.uuid4().hex[:6]}",
            "email": f"test_client_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+2222222222",
            "notes": "Test user's private client data"
        }
        
        success, test_client_response, _ = self.make_request("POST", "/clients", test_client_data, token=self.test_user_token)
        
        if not success or "id" not in test_client_response:
            self.log_result("Data Isolation - Test Client Creation", False, "Failed to create test client", test_client_response)
            return False
            
        test_client_id = test_client_response["id"]
        self.log_result(
            "Data Isolation - Test Client Creation", 
            True, 
            f"Created test user client with ID: {test_client_id}"
        )
        
        # Test 1: Admin should NOT see test user's client
        success, admin_clients, _ = self.make_request("GET", "/clients", token=self.admin_token)
        
        if success and isinstance(admin_clients, list):
            admin_client_ids = [client.get("id") for client in admin_clients]
            if test_client_id not in admin_client_ids:
                self.log_result(
                    "Data Isolation - Admin Cannot See Test User Clients", 
                    True, 
                    f"Admin correctly cannot see test user's client. Admin sees {len(admin_clients)} clients."
                )
            else:
                self.log_result(
                    "Data Isolation - Admin Cannot See Test User Clients", 
                    False, 
                    "CRITICAL: Admin can see test user's client - data leak detected!"
                )
        else:
            self.log_result("Data Isolation - Admin Client List", False, "Failed to get admin client list", admin_clients)
            
        # Test 2: Test user should NOT see admin's client
        success, test_clients, _ = self.make_request("GET", "/clients", token=self.test_user_token)
        
        if success and isinstance(test_clients, list):
            test_client_ids = [client.get("id") for client in test_clients]
            if admin_client_id not in test_client_ids:
                self.log_result(
                    "Data Isolation - Test User Cannot See Admin Clients", 
                    True, 
                    f"Test user correctly cannot see admin's client. Test user sees {len(test_clients)} clients."
                )
            else:
                self.log_result(
                    "Data Isolation - Test User Cannot See Admin Clients", 
                    False, 
                    "CRITICAL: Test user can see admin's client - data leak detected!"
                )
        else:
            self.log_result("Data Isolation - Test User Client List", False, "Failed to get test user client list", test_clients)
            
        # Test 3: Cross-user access should return 404/403
        success, cross_access_response, status_code = self.make_request(
            "GET", f"/clients/{admin_client_id}", token=self.test_user_token
        )
        
        if not success and status_code in [403, 404]:
            self.log_result(
                "Data Isolation - Cross-User Access Blocked", 
                True, 
                f"Cross-user client access correctly blocked with status {status_code}"
            )
        else:
            self.log_result(
                "Data Isolation - Cross-User Access Blocked", 
                False, 
                f"CRITICAL: Cross-user access allowed! Status: {status_code}",
                cross_access_response
            )
            
        # Test 4: Formulas should be user-scoped
        formula_data = {
            "client_id": admin_client_id,
            "formula_name": "Admin's Secret Formula",
            "formula_details": "Confidential formula details"
        }
        
        success, admin_formula_response, _ = self.make_request("POST", "/formulas", formula_data, token=self.admin_token)
        
        if success and "id" in admin_formula_response:
            admin_formula_id = admin_formula_response["id"]
            
            # Test user should not see admin's formulas
            success, test_formulas, _ = self.make_request("GET", "/formulas", token=self.test_user_token)
            
            if success and isinstance(test_formulas, list):
                test_formula_ids = [formula.get("id") for formula in test_formulas]
                if admin_formula_id not in test_formula_ids:
                    self.log_result(
                        "Data Isolation - Formulas User-Scoped", 
                        True, 
                        "Formulas are correctly user-scoped"
                    )
                else:
                    self.log_result(
                        "Data Isolation - Formulas User-Scoped", 
                        False, 
                        "CRITICAL: Formula data leak detected!"
                    )
            else:
                self.log_result("Data Isolation - Formula List Test", False, "Failed to get test user formulas", test_formulas)
                
        # Test 5: Appointments should be user-scoped
        appointment_data = {
            "client_id": admin_client_id,
            "appointment_date": "2025-01-15T10:00:00Z",
            "service": "Confidential Hair Service",
            "notes": "Private appointment notes"
        }
        
        success, admin_appointment_response, _ = self.make_request("POST", "/appointments", appointment_data, token=self.admin_token)
        
        if success and "id" in admin_appointment_response:
            admin_appointment_id = admin_appointment_response["id"]
            
            # Test user should not see admin's appointments
            success, test_appointments, _ = self.make_request("GET", "/appointments", token=self.test_user_token)
            
            if success and isinstance(test_appointments, list):
                test_appointment_ids = [apt.get("id") for apt in test_appointments]
                if admin_appointment_id not in test_appointment_ids:
                    self.log_result(
                        "Data Isolation - Appointments User-Scoped", 
                        True, 
                        "Appointments are correctly user-scoped"
                    )
                else:
                    self.log_result(
                        "Data Isolation - Appointments User-Scoped", 
                        False, 
                        "CRITICAL: Appointment data leak detected!"
                    )
            else:
                self.log_result("Data Isolation - Appointment List Test", False, "Failed to get test user appointments", test_appointments)
                
        # Cleanup: Delete test clients
        self.make_request("DELETE", f"/clients/{admin_client_id}", token=self.admin_token)
        self.make_request("DELETE", f"/clients/{test_client_id}", token=self.test_user_token)

    def test_profile_endpoints(self):
        """Test 4: Profile endpoints"""
        print("👤 Testing Profile Endpoints...")
        
        if not self.admin_token:
            self.log_result("Profile Endpoints Setup", False, "No admin token available")
            return False
            
        # Test GET /api/profiles/me/hub
        success, hub_response, status_code = self.make_request("GET", "/profiles/me/hub", token=self.admin_token)
        
        if success and "id" in hub_response:
            self.log_result(
                "GET /api/profiles/me/hub", 
                True, 
                f"Successfully retrieved own profile. User ID: {hub_response.get('id')}, is_tester: {hub_response.get('is_tester')}"
            )
        else:
            self.log_result("GET /api/profiles/me/hub", False, f"Failed to get hub profile. Status: {status_code}", hub_response)

    def run_all_tests(self):
        """Run all critical audit tests"""
        print("🚀 Starting StyleFlow Backend Critical Audit Tests")
        print("=" * 60)
        print()
        
        # Test 1: Authentication
        if not self.test_admin_authentication():
            print("❌ Authentication failed - stopping tests")
            return False
            
        # Create test user for isolation testing
        if not self.create_test_user():
            print("❌ Test user creation failed - skipping isolation tests")
        
        # Test 2: Client CRUD
        self.test_client_crud_operations()
        
        # Test 3: Data Isolation
        if self.test_user_token:
            self.test_data_isolation()
        else:
            self.log_result("Data Isolation Tests", False, "Skipped - no test user available")
            
        # Test 4: Profile Endpoints
        self.test_profile_endpoints()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 STYLEFLOW BACKEND AUDIT SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS: {passed}/{total} tests passed ({success_rate:.1f}% success rate)")
        print()
        
        # Group results by category
        categories = {
            "🔐 Authentication": [],
            "📋 Client CRUD": [],
            "🔒 Data Isolation": [],
            "👤 Profile Endpoints": [],
            "⚙️ Setup": []
        }
        
        for result in self.results:
            test_name = result["test"]
            if "Auth" in test_name or "Login" in test_name:
                categories["🔐 Authentication"].append(result)
            elif "Client" in test_name and "Isolation" not in test_name:
                categories["📋 Client CRUD"].append(result)
            elif "Isolation" in test_name or "Cross-User" in test_name or "User-Scoped" in test_name:
                categories["🔒 Data Isolation"].append(result)
            elif "Profile" in test_name or "Hub" in test_name:
                categories["👤 Profile Endpoints"].append(result)
            else:
                categories["⚙️ Setup"].append(result)
        
        for category, tests in categories.items():
            if tests:
                print(f"{category}:")
                for test in tests:
                    print(f"  {test['status']} {test['test']}")
                    if test['details']:
                        print(f"      {test['details']}")
                print()
        
        # Critical issues
        failed_tests = [r for r in self.results if not r["success"]]
        if failed_tests:
            print("🚨 CRITICAL ISSUES FOUND:")
            for test in failed_tests:
                if "CRITICAL" in test["details"]:
                    print(f"  ❌ {test['test']}: {test['details']}")
            print()
        
        # Data security assessment
        isolation_tests = [r for r in self.results if "Isolation" in r["test"] or "Cross-User" in r["test"]]
        isolation_passed = sum(1 for r in isolation_tests if r["success"])
        isolation_total = len(isolation_tests)
        
        if isolation_total > 0:
            isolation_rate = (isolation_passed / isolation_total * 100)
            if isolation_rate == 100:
                print("🛡️ DATA SECURITY: EXCELLENT - All data isolation tests passed")
            elif isolation_rate >= 80:
                print("⚠️ DATA SECURITY: GOOD - Most data isolation tests passed")
            else:
                print("🚨 DATA SECURITY: CRITICAL ISSUES - Data isolation failures detected")
            print()
        
        print("✅ Audit completed successfully!" if success_rate >= 80 else "❌ Audit completed with issues")
        print("=" * 60)

if __name__ == "__main__":
    tester = StyleFlowTester()
    tester.run_all_tests()