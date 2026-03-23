#!/usr/bin/env python3
"""
StyleFlow Backend API Testing - Real-Time Data Persistence + UI Sync
Focus: Verify PUT endpoints return full updated objects (not just success messages)
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import sys

# Backend URL from environment
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def authenticate(self):
        """Login and get JWT token"""
        print("\n=== AUTHENTICATION ===")
        
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_test("Admin Login", True, f"Token obtained: {self.token[:20]}...")
                    return True
                else:
                    self.log_test("Admin Login", False, f"No token in response: {data}")
                    return False
            else:
                self.log_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_clients_crud_with_full_objects(self):
        """Test client CRUD operations with full object returns"""
        print("\n=== CLIENTS CRUD - FULL OBJECT VERIFICATION ===")
        
        # 1. Create a new client (POST)
        client_data = {
            "name": f"Test Client {uuid.uuid4().hex[:8]}",
            "email": f"testclient{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "notes": "Test client for API testing",
            "preferences": "Prefers morning appointments",
            "hair_goals": "Maintain healthy hair",
            "is_vip": False,
            "last_visit": None
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if response.status_code == 200:
                created_client = response.json()
                
                # Verify POST returns full object with ID
                required_fields = ["id", "name", "email", "phone", "photo", "notes", "preferences", "hair_goals", "is_vip", "visit_count", "created_at"]
                missing_fields = [field for field in required_fields if field not in created_client]
                
                if not missing_fields and created_client.get("id"):
                    self.log_test("Client POST - Returns Full Object", True, f"All fields present, ID: {created_client['id']}")
                    client_id = created_client["id"]
                    
                    # 2. Update the client (PUT)
                    update_data = {
                        "name": f"Updated Client {uuid.uuid4().hex[:8]}",
                        "email": created_client["email"],  # Keep same email
                        "phone": "+9876543210",
                        "notes": "Updated notes for testing PUT response",
                        "preferences": "Updated preferences",
                        "hair_goals": "Updated hair goals",
                        "is_vip": True
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/clients/{client_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_client = put_response.json()
                        
                        # Verify PUT returns full updated object (not just success message)
                        if isinstance(updated_client, dict) and "message" not in updated_client:
                            # Check if it contains the updated values
                            if (updated_client.get("name") == update_data["name"] and 
                                updated_client.get("phone") == update_data["phone"] and
                                updated_client.get("notes") == update_data["notes"] and
                                updated_client.get("is_vip") == True and
                                updated_client.get("id") == client_id):
                                
                                self.log_test("Client PUT - Returns Full Updated Object", True, 
                                            f"Updated name: {updated_client['name']}, VIP: {updated_client['is_vip']}")
                            else:
                                self.log_test("Client PUT - Returns Full Updated Object", False, 
                                            f"Updated values not reflected correctly: {updated_client}")
                        else:
                            self.log_test("Client PUT - Returns Full Updated Object", False, 
                                        f"PUT returned message instead of object: {updated_client}")
                    else:
                        self.log_test("Client PUT - Returns Full Updated Object", False, 
                                    f"PUT failed with status: {put_response.status_code}")
                    
                    # Cleanup
                    self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                    
                else:
                    self.log_test("Client POST - Returns Full Object", False, 
                                f"Missing fields: {missing_fields}, Response: {created_client}")
            else:
                self.log_test("Client POST - Returns Full Object", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Client CRUD Test", False, f"Exception: {str(e)}")
    
    def test_formulas_crud_with_full_objects(self):
        """Test formula CRUD operations with full object returns"""
        print("\n=== FORMULAS CRUD - FULL OBJECT VERIFICATION ===")
        
        # First create a client to link the formula to
        client_data = {
            "name": f"Formula Test Client {uuid.uuid4().hex[:8]}",
            "email": f"formulaclient{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "notes": "Client for formula testing",
            "preferences": "",
            "hair_goals": "",
            "is_vip": False
        }
        
        try:
            client_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if client_response.status_code != 200:
                self.log_test("Formula Test - Client Creation", False, "Failed to create test client")
                return
                
            client_id = client_response.json()["id"]
            
            # 1. Create a new formula (POST)
            formula_data = {
                "client_id": client_id,
                "formula_name": f"Test Formula {uuid.uuid4().hex[:8]}",
                "formula_details": "Original formula details for testing",
                "date_created": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/formulas", json=formula_data)
            if response.status_code == 200:
                created_formula = response.json()
                
                # Verify POST returns full object with ID
                required_fields = ["id", "client_id", "formula_name", "formula_details", "date_created"]
                missing_fields = [field for field in required_fields if field not in created_formula]
                
                if not missing_fields and created_formula.get("id"):
                    self.log_test("Formula POST - Returns Full Object", True, f"All fields present, ID: {created_formula['id']}")
                    formula_id = created_formula["id"]
                    
                    # 2. Update the formula (PUT)
                    update_data = {
                        "client_id": client_id,
                        "formula_name": f"Updated Formula {uuid.uuid4().hex[:8]}",
                        "formula_details": "Updated formula details for testing PUT response"
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/formulas/{formula_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_formula = put_response.json()
                        
                        # Verify PUT returns full updated object (not just success message)
                        if isinstance(updated_formula, dict) and "message" not in updated_formula:
                            # Check if it contains the updated values
                            if (updated_formula.get("formula_name") == update_data["formula_name"] and 
                                updated_formula.get("formula_details") == update_data["formula_details"] and
                                updated_formula.get("client_id") == client_id and
                                updated_formula.get("id") == formula_id):
                                
                                self.log_test("Formula PUT - Returns Full Updated Object", True, 
                                            f"Updated name: {updated_formula['formula_name']}")
                            else:
                                self.log_test("Formula PUT - Returns Full Updated Object", False, 
                                            f"Updated values not reflected correctly: {updated_formula}")
                        else:
                            self.log_test("Formula PUT - Returns Full Updated Object", False, 
                                        f"PUT returned message instead of object: {updated_formula}")
                    else:
                        self.log_test("Formula PUT - Returns Full Updated Object", False, 
                                    f"PUT failed with status: {put_response.status_code}")
                    
                    # Cleanup
                    self.session.delete(f"{BACKEND_URL}/formulas/{formula_id}")
                    
                else:
                    self.log_test("Formula POST - Returns Full Object", False, 
                                f"Missing fields: {missing_fields}, Response: {created_formula}")
            else:
                self.log_test("Formula POST - Returns Full Object", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            
            # Cleanup client
            self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                
        except Exception as e:
            self.log_test("Formula CRUD Test", False, f"Exception: {str(e)}")
    
    def test_appointments_crud_with_full_objects(self):
        """Test appointment CRUD operations with full object returns"""
        print("\n=== APPOINTMENTS CRUD - FULL OBJECT VERIFICATION ===")
        
        # First create a client to link the appointment to
        client_data = {
            "name": f"Appointment Test Client {uuid.uuid4().hex[:8]}",
            "email": f"appointmentclient{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "notes": "Client for appointment testing",
            "preferences": "",
            "hair_goals": "",
            "is_vip": False
        }
        
        try:
            client_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if client_response.status_code != 200:
                self.log_test("Appointment Test - Client Creation", False, "Failed to create test client")
                return
                
            client_id = client_response.json()["id"]
            client_name = client_response.json()["name"]
            
            # 1. Create a new appointment (POST)
            appointment_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
            appointment_data = {
                "client_id": client_id,
                "appointment_date": appointment_date,
                "service": "Hair Cut and Style",
                "duration_minutes": 90,
                "notes": "Original appointment notes for testing",
                "status": "scheduled"
            }
            
            response = self.session.post(f"{BACKEND_URL}/appointments", json=appointment_data)
            if response.status_code == 200:
                created_appointment = response.json()
                
                # Verify POST returns full object with ID and client_name
                required_fields = ["id", "client_id", "appointment_date", "service", "duration_minutes", "notes", "status", "client_name"]
                missing_fields = [field for field in required_fields if field not in created_appointment]
                
                if not missing_fields and created_appointment.get("id") and created_appointment.get("client_name"):
                    self.log_test("Appointment POST - Returns Full Object with client_name", True, 
                                f"All fields present, ID: {created_appointment['id']}, Client: {created_appointment['client_name']}")
                    appointment_id = created_appointment["id"]
                    
                    # 2. Update the appointment (PUT)
                    new_appointment_date = (datetime.utcnow() + timedelta(days=2)).isoformat()
                    update_data = {
                        "client_id": client_id,
                        "appointment_date": new_appointment_date,
                        "service": "Hair Cut, Color and Style",
                        "duration_minutes": 120,
                        "notes": "Updated appointment notes for testing PUT response",
                        "status": "scheduled"
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/appointments/{appointment_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_appointment = put_response.json()
                        
                        # Verify PUT returns full updated object (not just success message) with client_name enriched
                        if isinstance(updated_appointment, dict) and "message" not in updated_appointment:
                            # Check if it contains the updated values and client_name
                            if (updated_appointment.get("service") == update_data["service"] and 
                                updated_appointment.get("duration_minutes") == update_data["duration_minutes"] and
                                updated_appointment.get("notes") == update_data["notes"] and
                                updated_appointment.get("client_id") == client_id and
                                updated_appointment.get("id") == appointment_id and
                                updated_appointment.get("client_name") == client_name):
                                
                                self.log_test("Appointment PUT - Returns Full Updated Object with client_name", True, 
                                            f"Updated service: {updated_appointment['service']}, Client: {updated_appointment['client_name']}")
                            else:
                                self.log_test("Appointment PUT - Returns Full Updated Object with client_name", False, 
                                            f"Updated values not reflected correctly: {updated_appointment}")
                        else:
                            self.log_test("Appointment PUT - Returns Full Updated Object with client_name", False, 
                                        f"PUT returned message instead of object: {updated_appointment}")
                    else:
                        self.log_test("Appointment PUT - Returns Full Updated Object with client_name", False, 
                                    f"PUT failed with status: {put_response.status_code}")
                    
                    # Cleanup
                    self.session.delete(f"{BACKEND_URL}/appointments/{appointment_id}")
                    
                else:
                    self.log_test("Appointment POST - Returns Full Object with client_name", False, 
                                f"Missing fields: {missing_fields}, Response: {created_appointment}")
            else:
                self.log_test("Appointment POST - Returns Full Object with client_name", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            
            # Cleanup client
            self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                
        except Exception as e:
            self.log_test("Appointment CRUD Test", False, f"Exception: {str(e)}")
    
    def test_appointment_status_completion_flow(self):
        """Test appointment status change to completed and visit count update"""
        print("\n=== APPOINTMENT COMPLETION FLOW ===")
        
        # Create a client
        client_data = {
            "name": f"Completion Test Client {uuid.uuid4().hex[:8]}",
            "email": f"completionclient{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "notes": "Client for completion testing",
            "preferences": "",
            "hair_goals": "",
            "is_vip": False
        }
        
        try:
            client_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if client_response.status_code != 200:
                self.log_test("Completion Test - Client Creation", False, "Failed to create test client")
                return
                
            client_id = client_response.json()["id"]
            initial_visit_count = client_response.json().get("visit_count", 0)
            
            # Create an appointment
            appointment_data = {
                "client_id": client_id,
                "appointment_date": datetime.utcnow().isoformat(),
                "service": "Hair Cut",
                "duration_minutes": 60,
                "notes": "Test appointment for completion",
                "status": "scheduled"
            }
            
            appointment_response = self.session.post(f"{BACKEND_URL}/appointments", json=appointment_data)
            if appointment_response.status_code != 200:
                self.log_test("Completion Test - Appointment Creation", False, "Failed to create test appointment")
                return
                
            appointment_id = appointment_response.json()["id"]
            
            # Update appointment status to completed
            update_data = {
                "status": "completed"
            }
            
            put_response = self.session.put(f"{BACKEND_URL}/appointments/{appointment_id}", json=update_data)
            if put_response.status_code == 200:
                updated_appointment = put_response.json()
                
                if updated_appointment.get("status") == "completed":
                    self.log_test("Appointment Status Update to Completed", True, 
                                f"Status updated to: {updated_appointment['status']}")
                    
                    # Check if client visit count was incremented
                    client_check = self.session.get(f"{BACKEND_URL}/clients/{client_id}")
                    if client_check.status_code == 200:
                        updated_client = client_check.json()
                        new_visit_count = updated_client.get("visit_count", 0)
                        
                        if new_visit_count == initial_visit_count + 1:
                            self.log_test("Client Visit Count Increment", True, 
                                        f"Visit count increased from {initial_visit_count} to {new_visit_count}")
                        else:
                            self.log_test("Client Visit Count Increment", False, 
                                        f"Visit count not incremented correctly: {initial_visit_count} -> {new_visit_count}")
                    else:
                        self.log_test("Client Visit Count Increment", False, "Failed to retrieve updated client")
                else:
                    self.log_test("Appointment Status Update to Completed", False, 
                                f"Status not updated correctly: {updated_appointment}")
            else:
                self.log_test("Appointment Status Update to Completed", False, 
                            f"PUT failed with status: {put_response.status_code}")
            
            # Cleanup
            self.session.delete(f"{BACKEND_URL}/appointments/{appointment_id}")
            self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                
        except Exception as e:
            self.log_test("Appointment Completion Flow Test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("StyleFlow Backend API Testing - Real-Time Data Persistence + UI Sync")
        print("=" * 70)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all CRUD tests
        self.test_clients_crud_with_full_objects()
        self.test_formulas_crud_with_full_objects()
        self.test_appointments_crud_with_full_objects()
        self.test_appointment_status_completion_flow()
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # List failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = StyleFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)