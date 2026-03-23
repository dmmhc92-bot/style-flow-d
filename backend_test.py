#!/usr/bin/env python3
"""
StyleFlow Backend Testing - SMART REBOOK ENGINE + CLIENT TIMELINE + DATA PRIVACY
Testing comprehensive rebook functionality and data isolation
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.user_a_token = None
        self.user_b_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append(f"{status} {test_name}: {details}")
        print(f"{status} {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, token: str = None, data: dict = None) -> requests.Response:
        """Make HTTP request with optional auth"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        if method.upper() == "GET":
            return requests.get(url, headers=headers)
        elif method.upper() == "POST":
            return requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            return requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            return requests.delete(url, headers=headers)
            
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user"""
        try:
            response = self.make_request("POST", "/auth/login", data={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token")  # Changed from access_token to token
                self.log_test("Admin Authentication", True, f"Token obtained: {self.admin_token[:20]}...")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
            
    def create_test_user(self, email_suffix: str) -> Optional[str]:
        """Create a test user and return token"""
        try:
            unique_id = str(uuid.uuid4())[:8]
            email = f"testuser_{email_suffix}_{unique_id}@styleflow.com"
            
            response = self.make_request("POST", "/auth/signup", data={
                "full_name": f"Test User {email_suffix.upper()}",
                "business_name": f"Test Business {email_suffix.upper()}",
                "email": email,
                "password": "TestPassword123!"
            })
            
            if response.status_code in [200, 201]:  # Accept both 200 and 201
                data = response.json()
                token = data.get("token")  # Changed from access_token to token
                self.log_test(f"Create Test User {email_suffix.upper()}", True, f"Email: {email}")
                return token
            else:
                self.log_test(f"Create Test User {email_suffix.upper()}", False, f"Status: {response.status_code}, Response: {response.text}")
                return None
        except Exception as e:
            self.log_test(f"Create Test User {email_suffix.upper()}", False, f"Exception: {str(e)}")
            return None
            
    def test_client_rebook_status(self) -> bool:
        """Test CLIENT REBOOK STATUS functionality"""
        print("\n=== TESTING CLIENT REBOOK STATUS ===")
        
        try:
            # Create a client with rebook_interval_days=30
            client_data = {
                "name": "Sarah Johnson",
                "phone": "+1234567890",
                "email": "sarah.johnson@email.com",
                "rebook_interval_days": 30,
                "notes": "Prefers morning appointments"
            }
            
            response = self.make_request("POST", "/clients", self.admin_token, client_data)
            
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Client with Rebook Interval", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            client = response.json()
            client_id = client.get("id")
            
            # Verify response includes required fields
            required_fields = ["rebook_interval_days", "next_visit_due", "rebook_status"]
            missing_fields = [field for field in required_fields if field not in client]
            
            if missing_fields:
                self.log_test("Client Rebook Fields", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Client Rebook Fields", True, f"All fields present: {required_fields}")
                
            # Verify rebook_status is valid
            valid_statuses = ["new", "on_track", "due_soon", "overdue"]
            if client.get("rebook_status") not in valid_statuses:
                self.log_test("Rebook Status Validation", False, f"Invalid status: {client.get('rebook_status')}")
                return False
            else:
                self.log_test("Rebook Status Validation", True, f"Status: {client.get('rebook_status')}")
                
            # Test GET /api/clients - verify all clients have rebook_status
            response = self.make_request("GET", "/clients", self.admin_token)
            
            if response.status_code != 200:
                self.log_test("Get All Clients", False, f"Status: {response.status_code}")
                return False
                
            clients = response.json()
            clients_without_rebook = [c for c in clients if "rebook_status" not in c]
            
            if clients_without_rebook:
                self.log_test("All Clients Have Rebook Status", False, f"{len(clients_without_rebook)} clients missing rebook_status")
                return False
            else:
                self.log_test("All Clients Have Rebook Status", True, f"All {len(clients)} clients have rebook_status")
                
            return True
            
        except Exception as e:
            self.log_test("Client Rebook Status Test", False, f"Exception: {str(e)}")
            return False
            
    def test_client_timeline(self) -> bool:
        """Test CLIENT TIMELINE functionality"""
        print("\n=== TESTING CLIENT TIMELINE ===")
        
        try:
            # Create a client
            client_data = {
                "name": "Michael Chen",
                "phone": "+1987654321",
                "email": "michael.chen@email.com",
                "rebook_interval_days": 35
            }
            
            response = self.make_request("POST", "/clients", self.admin_token, client_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Client for Timeline", False, f"Status: {response.status_code}")
                return False
                
            client = response.json()
            client_id = client.get("id")
            self.log_test("Create Client for Timeline", True, f"Client ID: {client_id}")
            
            # Create an appointment for the client
            appointment_data = {
                "client_id": client_id,
                "service": "Haircut & Style",
                "appointment_date": "2024-01-15T10:00:00",  # Combined datetime
                "duration_minutes": 90,  # Changed from duration to duration_minutes
                "status": "completed"
            }
            
            response = self.make_request("POST", "/appointments", self.admin_token, appointment_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Appointment for Timeline", False, f"Status: {response.status_code}")
                return False
            else:
                self.log_test("Create Appointment for Timeline", True, "Appointment created")
                
            # Create a formula for the client
            formula_data = {
                "client_id": client_id,
                "formula_name": "Custom Blonde Mix",
                "formula_details": "20vol developer, L'Oreal 9.1, Olaplex. Process time: 45 minutes. Apply from mid-length to ends first."
            }
            
            response = self.make_request("POST", "/formulas", self.admin_token, formula_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Formula for Timeline", False, f"Status: {response.status_code}")
                return False
            else:
                self.log_test("Create Formula for Timeline", True, "Formula created")
                
            # Test GET /api/clients/{client_id}/timeline
            response = self.make_request("GET", f"/clients/{client_id}/timeline", self.admin_token)
            
            if response.status_code != 200:
                self.log_test("Get Client Timeline", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            timeline_data = response.json()
            
            # Verify response structure
            required_keys = ["client", "timeline", "last_formula", "stats"]
            missing_keys = [key for key in required_keys if key not in timeline_data]
            
            if missing_keys:
                self.log_test("Timeline Response Structure", False, f"Missing keys: {missing_keys}")
                return False
            else:
                self.log_test("Timeline Response Structure", True, f"All keys present: {required_keys}")
                
            # Verify client has rebook status
            client_data = timeline_data.get("client", {})
            if "rebook_status" not in client_data:
                self.log_test("Timeline Client Rebook Status", False, "Client missing rebook_status")
                return False
            else:
                self.log_test("Timeline Client Rebook Status", True, f"Status: {client_data.get('rebook_status')}")
                
            # Verify timeline is an array and sorted by date descending
            timeline = timeline_data.get("timeline", [])
            if not isinstance(timeline, list):
                self.log_test("Timeline Array Structure", False, "Timeline is not an array")
                return False
            else:
                self.log_test("Timeline Array Structure", True, f"Timeline has {len(timeline)} events")
                
            # Check if timeline is sorted by date descending (if multiple events)
            if len(timeline) > 1:
                dates = [event.get("date") for event in timeline if event.get("date")]
                if dates != sorted(dates, reverse=True):
                    self.log_test("Timeline Date Sorting", False, "Timeline not sorted by date descending")
                    return False
                else:
                    self.log_test("Timeline Date Sorting", True, "Timeline properly sorted")
            else:
                self.log_test("Timeline Date Sorting", True, "Single/no events - sorting not applicable")
                
            return True
            
        except Exception as e:
            self.log_test("Client Timeline Test", False, f"Exception: {str(e)}")
            return False
            
    def test_smart_rebook_due_endpoint(self) -> bool:
        """Test SMART REBOOK DUE ENDPOINT"""
        print("\n=== TESTING SMART REBOOK DUE ENDPOINT ===")
        
        try:
            # Test GET /api/clients/rebook/due
            response = self.make_request("GET", "/clients/rebook/due", self.admin_token)
            
            if response.status_code != 200:
                self.log_test("Get Rebook Due Clients", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            due_data = response.json()
            
            # Verify response structure
            required_keys = ["due_soon", "overdue", "total_due"]
            missing_keys = [key for key in required_keys if key not in due_data]
            
            if missing_keys:
                self.log_test("Rebook Due Response Structure", False, f"Missing keys: {missing_keys}")
                return False
            else:
                self.log_test("Rebook Due Response Structure", True, f"All keys present: {required_keys}")
                
            # Verify arrays
            if not isinstance(due_data.get("due_soon"), list):
                self.log_test("Due Soon Array", False, "due_soon is not an array")
                return False
            else:
                self.log_test("Due Soon Array", True, f"{len(due_data.get('due_soon'))} clients due soon")
                
            if not isinstance(due_data.get("overdue"), list):
                self.log_test("Overdue Array", False, "overdue is not an array")
                return False
            else:
                self.log_test("Overdue Array", True, f"{len(due_data.get('overdue'))} clients overdue")
                
            # Verify total_due count
            expected_total = len(due_data.get("due_soon", [])) + len(due_data.get("overdue", []))
            actual_total = due_data.get("total_due", 0)
            
            if expected_total != actual_total:
                self.log_test("Total Due Count", False, f"Expected: {expected_total}, Actual: {actual_total}")
                return False
            else:
                self.log_test("Total Due Count", True, f"Correct total: {actual_total}")
                
            return True
            
        except Exception as e:
            self.log_test("Smart Rebook Due Test", False, f"Exception: {str(e)}")
            return False
            
    def test_dashboard_stats_with_rebook(self) -> bool:
        """Test DASHBOARD STATS WITH REBOOK"""
        print("\n=== TESTING DASHBOARD STATS WITH REBOOK ===")
        
        try:
            # Test GET /api/dashboard/stats
            response = self.make_request("GET", "/dashboard/stats", self.admin_token)
            
            if response.status_code != 200:
                self.log_test("Get Dashboard Stats", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            stats = response.json()
            
            # Verify rebook-related fields are present
            rebook_fields = ["clients_due_soon", "clients_overdue"]
            missing_fields = [field for field in rebook_fields if field not in stats]
            
            if missing_fields:
                self.log_test("Dashboard Rebook Fields", False, f"Missing fields: {missing_fields}")
                return False
            else:
                self.log_test("Dashboard Rebook Fields", True, f"Fields present: {rebook_fields}")
                
            # Verify values are numbers
            for field in rebook_fields:
                value = stats.get(field)
                if not isinstance(value, (int, float)):
                    self.log_test(f"Dashboard {field} Type", False, f"Expected number, got {type(value)}")
                    return False
                else:
                    self.log_test(f"Dashboard {field} Type", True, f"Value: {value}")
                    
            return True
            
        except Exception as e:
            self.log_test("Dashboard Stats Test", False, f"Exception: {str(e)}")
            return False
            
    def test_data_privacy(self) -> bool:
        """Test DATA PRIVACY - Cross-user data isolation"""
        print("\n=== TESTING DATA PRIVACY ===")
        
        try:
            # Create User A and User B
            self.user_a_token = self.create_test_user("a")
            self.user_b_token = self.create_test_user("b")
            
            if not self.user_a_token or not self.user_b_token:
                self.log_test("Create Test Users", False, "Failed to create test users")
                return False
                
            # Create a client under User A
            client_data = {
                "name": "Private Client A",
                "phone": "+1111111111",
                "email": "private.a@email.com",
                "notes": "This is User A's private client"
            }
            
            response = self.make_request("POST", "/clients", self.user_a_token, client_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Client for User A", False, f"Status: {response.status_code}")
                return False
                
            user_a_client = response.json()
            user_a_client_id = user_a_client.get("id")
            self.log_test("Create Client for User A", True, f"Client ID: {user_a_client_id}")
            
            # Test: User B (admin) tries to access User A's client list
            response = self.make_request("GET", "/clients", self.user_b_token)
            if response.status_code != 200:
                self.log_test("User B Get Clients", False, f"Status: {response.status_code}")
                return False
                
            user_b_clients = response.json()
            user_a_client_visible = any(c.get("id") == user_a_client_id for c in user_b_clients)
            
            if user_a_client_visible:
                self.log_test("Data Isolation - Client List", False, "User B can see User A's client")
                return False
            else:
                self.log_test("Data Isolation - Client List", True, "User B cannot see User A's client")
                
            # Test: User B tries to access User A's specific client (should return 404, not 403)
            response = self.make_request("GET", f"/clients/{user_a_client_id}", self.user_b_token)
            
            if response.status_code == 404:
                self.log_test("Data Privacy - Client Access 404", True, "Returns 404 (not found)")
            elif response.status_code == 403:
                self.log_test("Data Privacy - Client Access 404", False, "Returns 403 instead of 404")
                return False
            else:
                self.log_test("Data Privacy - Client Access 404", False, f"Unexpected status: {response.status_code}")
                return False
                
            # Test: User B tries to access User A's client timeline (should return 404)
            response = self.make_request("GET", f"/clients/{user_a_client_id}/timeline", self.user_b_token)
            
            if response.status_code == 404:
                self.log_test("Data Privacy - Timeline Access 404", True, "Returns 404 (not found)")
            elif response.status_code == 403:
                self.log_test("Data Privacy - Timeline Access 404", False, "Returns 403 instead of 404")
                return False
            else:
                self.log_test("Data Privacy - Timeline Access 404", False, f"Unexpected status: {response.status_code}")
                return False
                
            # Test: Admin user (original admin) should also not see other users' data
            response = self.make_request("GET", "/clients", self.admin_token)
            if response.status_code != 200:
                self.log_test("Admin Get Clients", False, f"Status: {response.status_code}")
                return False
                
            admin_clients = response.json()
            user_a_client_visible_to_admin = any(c.get("id") == user_a_client_id for c in admin_clients)
            
            if user_a_client_visible_to_admin:
                self.log_test("Admin Data Isolation", False, "Admin can see other users' clients")
                return False
            else:
                self.log_test("Admin Data Isolation", True, "Admin cannot see other users' private clients")
                
            return True
            
        except Exception as e:
            self.log_test("Data Privacy Test", False, f"Exception: {str(e)}")
            return False
            
    def test_data_isolation_queries(self) -> bool:
        """Test DATA ISOLATION - User-scoped queries"""
        print("\n=== TESTING DATA ISOLATION QUERIES ===")
        
        try:
            # Create formulas and appointments for User A
            if not self.user_a_token:
                self.log_test("User A Token Check", False, "User A token not available")
                return False
                
            # Create a client for User A first
            client_data = {
                "name": "Isolation Test Client",
                "phone": "+2222222222",
                "email": "isolation.test@email.com"
            }
            
            response = self.make_request("POST", "/clients", self.user_a_token, client_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Client for Isolation Test", False, f"Status: {response.status_code}")
                return False
                
            client = response.json()
            client_id = client.get("id")
            
            # Create formula for User A
            formula_data = {
                "client_id": client_id,
                "formula_name": "User A Formula",
                "formula_details": "Secret ingredients and process details"
            }
            
            response = self.make_request("POST", "/formulas", self.user_a_token, formula_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Formula for User A", False, f"Status: {response.status_code}")
                return False
            else:
                self.log_test("Create Formula for User A", True, "Formula created")
                
            # Create appointment for User A
            appointment_data = {
                "client_id": client_id,
                "service": "User A Service",
                "appointment_date": "2024-02-01T14:00:00",  # Combined datetime
                "duration_minutes": 60  # Changed from duration to duration_minutes
            }
            
            response = self.make_request("POST", "/appointments", self.user_a_token, appointment_data)
            if response.status_code not in [200, 201]:  # Accept both 200 and 201
                self.log_test("Create Appointment for User A", False, f"Status: {response.status_code}")
                return False
            else:
                self.log_test("Create Appointment for User A", True, "Appointment created")
                
            # Test: User B queries formulas (should not see User A's formulas)
            response = self.make_request("GET", "/formulas", self.user_b_token)
            if response.status_code != 200:
                self.log_test("User B Get Formulas", False, f"Status: {response.status_code}")
                return False
                
            user_b_formulas = response.json()
            user_a_formula_visible = any("User A Formula" in f.get("formula_name", "") for f in user_b_formulas)
            
            if user_a_formula_visible:
                self.log_test("Formula Isolation", False, "User B can see User A's formulas")
                return False
            else:
                self.log_test("Formula Isolation", True, "User B cannot see User A's formulas")
                
            # Test: User B queries appointments (should not see User A's appointments)
            response = self.make_request("GET", "/appointments", self.user_b_token)
            if response.status_code != 200:
                self.log_test("User B Get Appointments", False, f"Status: {response.status_code}")
                return False
                
            user_b_appointments = response.json()
            user_a_appointment_visible = any("User A Service" in a.get("service", "") for a in user_b_appointments)
            
            if user_a_appointment_visible:
                self.log_test("Appointment Isolation", False, "User B can see User A's appointments")
                return False
            else:
                self.log_test("Appointment Isolation", True, "User B cannot see User A's appointments")
                
            # Test: Timeline endpoint should only return data for authenticated user's client
            # This was already tested in the data privacy section, but let's verify again
            response = self.make_request("GET", f"/clients/{client_id}/timeline", self.user_b_token)
            
            if response.status_code == 404:
                self.log_test("Timeline Data Isolation", True, "Timeline properly isolated (404)")
            else:
                self.log_test("Timeline Data Isolation", False, f"Unexpected status: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("Data Isolation Test", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting StyleFlow SMART REBOOK ENGINE + CLIENT TIMELINE + DATA PRIVACY Testing")
        print("=" * 80)
        
        # Authenticate admin
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return
            
        # Run all test scenarios
        tests = [
            ("CLIENT REBOOK STATUS", self.test_client_rebook_status),
            ("CLIENT TIMELINE", self.test_client_timeline),
            ("SMART REBOOK DUE ENDPOINT", self.test_smart_rebook_due_endpoint),
            ("DASHBOARD STATS WITH REBOOK", self.test_dashboard_stats_with_rebook),
            ("DATA PRIVACY", self.test_data_privacy),
            ("DATA ISOLATION QUERIES", self.test_data_isolation_queries)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, str(e))
                
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            print(result)
            
        print(f"\n🎯 OVERALL RESULT: {passed}/{total} test scenarios passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! SMART REBOOK ENGINE + DATA PRIVACY working correctly")
        else:
            print(f"⚠️  {total - passed} test scenario(s) failed - requires attention")

if __name__ == "__main__":
    tester = StyleFlowTester()
    tester.run_all_tests()