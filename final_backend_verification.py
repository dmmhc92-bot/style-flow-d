#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials
TEST_EMAIL = "admin@styleflow.com"
TEST_PASSWORD = "Admin1234!"

class FinalBackendVerification:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        self.user_id = None
        self.test_client_id = None
        self.test_appointment_id = None
        self.test_formula_id = None
        self.test_post_id = None
        
    def log_result(self, test_name, status, status_code=None, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "status_code": status_code,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌"
        code_info = f" ({status_code})" if status_code else ""
        print(f"{status_symbol} {test_name}{code_info}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            print("\n🔐 AUTHENTICATION TEST")
            print("-" * 40)
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("POST /api/auth/login", "PASS", 200, f"Successfully logged in as {TEST_EMAIL}")
                    return True
                else:
                    self.log_result("POST /api/auth/login", "FAIL", 200, f"No token in response: {data}")
                    return False
            else:
                self.log_result("POST /api/auth/login", "FAIL", response.status_code, f"Login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("POST /api/auth/login", "FAIL", None, f"Authentication error: {str(e)}")
            return False
    
    def test_auth_endpoints(self):
        """Test all authentication endpoints"""
        print("\n🔐 AUTHENTICATION ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/auth/me
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            if response.status_code == 200:
                data = response.json()
                self.log_result("GET /api/auth/me", "PASS", 200, f"Retrieved user profile: {data.get('full_name', 'Unknown')}")
            else:
                self.log_result("GET /api/auth/me", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/auth/me", "FAIL", None, str(e))
        
        # Test PUT /api/auth/profile
        try:
            profile_update = {
                "full_name": "Admin User Test",
                "business_name": "StyleFlow Test Business"
            }
            response = self.session.put(f"{BACKEND_URL}/auth/profile", json=profile_update)
            if response.status_code == 200:
                self.log_result("PUT /api/auth/profile", "PASS", 200, "Profile updated successfully")
            else:
                self.log_result("PUT /api/auth/profile", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("PUT /api/auth/profile", "FAIL", None, str(e))
    
    def test_clients_endpoints(self):
        """Test all clients CRUD endpoints"""
        print("\n👥 CLIENTS CRUD ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/clients
        try:
            response = self.session.get(f"{BACKEND_URL}/clients")
            if response.status_code == 200:
                clients = response.json()
                self.log_result("GET /api/clients", "PASS", 200, f"Retrieved {len(clients)} clients")
            else:
                self.log_result("GET /api/clients", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/clients", "FAIL", None, str(e))
        
        # Test POST /api/clients (create new)
        try:
            new_client = {
                "name": f"Test Client {uuid.uuid4().hex[:8]}",
                "email": f"testclient{uuid.uuid4().hex[:8]}@example.com",
                "phone": "+1234567890",
                "is_vip": False,
                "notes": "Test client for final verification"
            }
            response = self.session.post(f"{BACKEND_URL}/clients", json=new_client)
            if response.status_code == 200:
                data = response.json()
                self.test_client_id = data.get("id")
                self.log_result("POST /api/clients", "PASS", 200, f"Created client with ID: {self.test_client_id}")
            else:
                self.log_result("POST /api/clients", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("POST /api/clients", "FAIL", None, str(e))
        
        # Test GET /api/clients/{id}
        if self.test_client_id:
            try:
                response = self.session.get(f"{BACKEND_URL}/clients/{self.test_client_id}")
                if response.status_code == 200:
                    client = response.json()
                    self.log_result("GET /api/clients/{id}", "PASS", 200, f"Retrieved client: {client.get('name')}")
                else:
                    self.log_result("GET /api/clients/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("GET /api/clients/{id}", "FAIL", None, str(e))
            
            # Test PUT /api/clients/{id}
            try:
                update_data = {
                    "name": f"Updated Test Client {uuid.uuid4().hex[:8]}",
                    "is_vip": True
                }
                response = self.session.put(f"{BACKEND_URL}/clients/{self.test_client_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("PUT /api/clients/{id}", "PASS", 200, "Client updated successfully")
                else:
                    self.log_result("PUT /api/clients/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("PUT /api/clients/{id}", "FAIL", None, str(e))
            
            # Test DELETE /api/clients/{id} - but we'll do this in cleanup to avoid breaking other tests
    
    def test_appointments_endpoints(self):
        """Test appointments endpoints"""
        print("\n📅 APPOINTMENTS ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/appointments
        try:
            response = self.session.get(f"{BACKEND_URL}/appointments")
            if response.status_code == 200:
                appointments = response.json()
                self.log_result("GET /api/appointments", "PASS", 200, f"Retrieved {len(appointments)} appointments")
            else:
                self.log_result("GET /api/appointments", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/appointments", "FAIL", None, str(e))
        
        # Test POST /api/appointments
        if self.test_client_id:
            try:
                new_appointment = {
                    "client_id": self.test_client_id,
                    "appointment_date": "2024-12-20T14:00:00",
                    "service": "Hair Cut & Style",
                    "duration_minutes": 90,
                    "status": "scheduled",
                    "notes": "Test appointment for final verification"
                }
                response = self.session.post(f"{BACKEND_URL}/appointments", json=new_appointment)
                if response.status_code == 200:
                    data = response.json()
                    self.test_appointment_id = data.get("id")
                    self.log_result("POST /api/appointments", "PASS", 200, f"Created appointment with ID: {self.test_appointment_id}")
                else:
                    self.log_result("POST /api/appointments", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("POST /api/appointments", "FAIL", None, str(e))
    
    def test_formulas_endpoints(self):
        """Test formulas endpoints"""
        print("\n🧪 FORMULAS ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/formulas
        try:
            response = self.session.get(f"{BACKEND_URL}/formulas")
            if response.status_code == 200:
                formulas = response.json()
                self.log_result("GET /api/formulas", "PASS", 200, f"Retrieved {len(formulas)} formulas")
            else:
                self.log_result("GET /api/formulas", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/formulas", "FAIL", None, str(e))
        
        # Test POST /api/formulas
        if self.test_client_id:
            try:
                new_formula = {
                    "client_id": self.test_client_id,
                    "formula_name": f"Test Formula {uuid.uuid4().hex[:8]}",
                    "formula_details": "Test formula for final verification - 20vol developer, L'Oreal color",
                    "notes": "Test formula notes"
                }
                response = self.session.post(f"{BACKEND_URL}/formulas", json=new_formula)
                if response.status_code == 200:
                    data = response.json()
                    self.test_formula_id = data.get("id")
                    self.log_result("POST /api/formulas", "PASS", 200, f"Created formula with ID: {self.test_formula_id}")
                else:
                    self.log_result("POST /api/formulas", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("POST /api/formulas", "FAIL", None, str(e))
        
        # Test GET /api/formulas/{id}
        if self.test_formula_id:
            try:
                response = self.session.get(f"{BACKEND_URL}/formulas/{self.test_formula_id}")
                if response.status_code == 200:
                    formula = response.json()
                    self.log_result("GET /api/formulas/{id}", "PASS", 200, f"Retrieved formula: {formula.get('formula_name')}")
                else:
                    self.log_result("GET /api/formulas/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("GET /api/formulas/{id}", "FAIL", None, str(e))
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print("\n📊 DASHBOARD ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/dashboard/stats
        try:
            response = self.session.get(f"{BACKEND_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                self.log_result("GET /api/dashboard/stats", "PASS", 200, f"Retrieved dashboard stats: {list(stats.keys())}")
            else:
                self.log_result("GET /api/dashboard/stats", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/dashboard/stats", "FAIL", None, str(e))
    
    def test_posts_endpoints(self):
        """Test feed/posts endpoints"""
        print("\n📱 FEED/POSTS ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/posts
        try:
            response = self.session.get(f"{BACKEND_URL}/posts")
            if response.status_code == 200:
                posts = response.json()
                self.log_result("GET /api/posts", "PASS", 200, f"Retrieved {len(posts)} posts")
            else:
                self.log_result("GET /api/posts", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/posts", "FAIL", None, str(e))
        
        # Test POST /api/posts
        try:
            new_post = {
                "images": ["data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="],
                "caption": f"Test post for final verification {uuid.uuid4().hex[:8]}",
                "tags": ["#test", "#verification"]
            }
            response = self.session.post(f"{BACKEND_URL}/posts", json=new_post)
            if response.status_code == 200:
                data = response.json()
                self.test_post_id = data.get("id")
                self.log_result("POST /api/posts", "PASS", 200, f"Created post with ID: {self.test_post_id}")
            else:
                self.log_result("POST /api/posts", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("POST /api/posts", "FAIL", None, str(e))
    
    def test_users_endpoints(self):
        """Test users endpoints"""
        print("\n👤 USERS ENDPOINTS")
        print("-" * 40)
        
        # Test GET /api/users/discover
        try:
            response = self.session.get(f"{BACKEND_URL}/users/discover")
            if response.status_code == 200:
                users = response.json()
                self.log_result("GET /api/users/discover", "PASS", 200, f"Retrieved {len(users)} discoverable users")
            else:
                self.log_result("GET /api/users/discover", "FAIL", response.status_code, response.text)
        except Exception as e:
            self.log_result("GET /api/users/discover", "FAIL", None, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n🧹 CLEANUP TEST DATA & DELETE ENDPOINT TESTS")
        print("-" * 40)
        
        # Test DELETE /api/posts/{id}
        if self.test_post_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/posts/{self.test_post_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /api/posts/{id}", "PASS", 200, f"Deleted test post: {self.test_post_id}")
                else:
                    self.log_result("DELETE /api/posts/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("DELETE /api/posts/{id}", "FAIL", None, str(e))
        
        # Test DELETE /api/appointments/{id}
        if self.test_appointment_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/appointments/{self.test_appointment_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /api/appointments/{id}", "PASS", 200, f"Deleted test appointment: {self.test_appointment_id}")
                else:
                    self.log_result("DELETE /api/appointments/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("DELETE /api/appointments/{id}", "FAIL", None, str(e))
        
        # Test DELETE /api/formulas/{id}
        if self.test_formula_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/formulas/{self.test_formula_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /api/formulas/{id}", "PASS", 200, f"Deleted test formula: {self.test_formula_id}")
                else:
                    self.log_result("DELETE /api/formulas/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("DELETE /api/formulas/{id}", "FAIL", None, str(e))
        
        # Test DELETE /api/clients/{id} (this should be last as other entities depend on it)
        if self.test_client_id:
            try:
                response = self.session.delete(f"{BACKEND_URL}/clients/{self.test_client_id}")
                if response.status_code == 200:
                    self.log_result("DELETE /api/clients/{id}", "PASS", 200, f"Deleted test client: {self.test_client_id}")
                else:
                    self.log_result("DELETE /api/clients/{id}", "FAIL", response.status_code, response.text)
            except Exception as e:
                self.log_result("DELETE /api/clients/{id}", "FAIL", None, str(e))
    
    def run_final_verification(self):
        """Run comprehensive final verification of all backend endpoints"""
        print("=" * 80)
        print("🔍 FINAL BACKEND VERIFICATION - ALL ENDPOINTS")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all endpoint tests
        self.test_auth_endpoints()
        self.test_clients_endpoints()
        self.test_appointments_endpoints()
        self.test_formulas_endpoints()
        self.test_dashboard_endpoints()
        self.test_posts_endpoints()
        self.test_users_endpoints()
        
        # Clean up test data
        self.cleanup_test_data()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📋 FINAL VERIFICATION SUMMARY")
        print("=" * 80)
        
        passed = 0
        failed = 0
        forbidden_403 = 0
        
        print("\n🔍 DETAILED RESULTS BY ENDPOINT:")
        print("-" * 50)
        
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌"
            status_code = result.get("status_code", "N/A")
            print(f"{status_symbol} {result['test']} ({status_code})")
            
            if result["status"] == "PASS":
                passed += 1
            else:
                failed += 1
                if result.get("status_code") == 403:
                    forbidden_403 += 1
        
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   403 Forbidden Errors: {forbidden_403}")
        
        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        if forbidden_403 > 0:
            print(f"❌ FAIL - Found {forbidden_403} endpoints returning 403 Forbidden errors")
            print("   These endpoints need immediate attention:")
            for result in self.test_results:
                if result.get("status_code") == 403:
                    print(f"   - {result['test']}")
        elif failed == 0:
            print("✅ PASS - All backend endpoints working correctly, NO 403 errors found")
        else:
            print(f"⚠️  PARTIAL - {failed} endpoints failed but no 403 errors detected")
        
        return forbidden_403 == 0 and failed == 0

if __name__ == "__main__":
    verifier = FinalBackendVerification()
    success = verifier.run_final_verification()
    sys.exit(0 if success else 1)