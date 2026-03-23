#!/usr/bin/env python3
"""
StyleFlow Backend API Testing - OFFLINE-FIRST and REAL-TIME SYNC
Focus: Comprehensive CRUD testing for clients, appointments, formulas, and dashboard
Verify all POST/PUT responses return complete objects with proper JSON structure
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
    
    def test_clients_full_crud(self):
        """Test complete CRUD operations for clients"""
        print("\n=== CLIENTS FULL CRUD OPERATIONS ===")
        
        # Test data
        client_data = {
            "name": f"Sarah Johnson {uuid.uuid4().hex[:8]}",
            "email": f"sarah.johnson{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1-555-0123",
            "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
            "notes": "Regular client, prefers morning appointments",
            "preferences": "Organic products only",
            "hair_goals": "Maintain healthy blonde highlights",
            "is_vip": True,
            "last_visit": None
        }
        
        try:
            # 1. POST /api/clients - Create client
            response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if response.status_code == 200:
                created_client = response.json()
                if created_client.get("id") and created_client.get("name") == client_data["name"]:
                    self.log_test("POST /api/clients - Create client", True, 
                                f"Client created with ID: {created_client['id']}")
                    client_id = created_client["id"]
                    
                    # 2. GET /api/clients - List all clients
                    list_response = self.session.get(f"{BACKEND_URL}/clients")
                    if list_response.status_code == 200:
                        clients_list = list_response.json()
                        if isinstance(clients_list, list) and any(c.get("id") == client_id for c in clients_list):
                            self.log_test("GET /api/clients - List all clients", True, 
                                        f"Found {len(clients_list)} clients, including created client")
                        else:
                            self.log_test("GET /api/clients - List all clients", False, 
                                        f"Created client not found in list: {clients_list}")
                    else:
                        self.log_test("GET /api/clients - List all clients", False, 
                                    f"Status: {list_response.status_code}")
                    
                    # 3. GET /api/clients/{id} - Get single client
                    get_response = self.session.get(f"{BACKEND_URL}/clients/{client_id}")
                    if get_response.status_code == 200:
                        single_client = get_response.json()
                        if single_client.get("id") == client_id and single_client.get("name") == client_data["name"]:
                            self.log_test("GET /api/clients/{id} - Get single client", True, 
                                        f"Retrieved client: {single_client['name']}")
                        else:
                            self.log_test("GET /api/clients/{id} - Get single client", False, 
                                        f"Client data mismatch: {single_client}")
                    else:
                        self.log_test("GET /api/clients/{id} - Get single client", False, 
                                    f"Status: {get_response.status_code}")
                    
                    # 4. PUT /api/clients/{id} - Update client
                    update_data = {
                        "name": f"Sarah Johnson-Smith {uuid.uuid4().hex[:8]}",
                        "email": created_client["email"],  # Keep same email
                        "phone": "+1-555-9876",
                        "notes": "Updated notes - VIP client with special requests",
                        "preferences": "Eco-friendly products preferred",
                        "hair_goals": "Transition to natural color",
                        "is_vip": True
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/clients/{client_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_client = put_response.json()
                        if (updated_client.get("name") == update_data["name"] and 
                            updated_client.get("phone") == update_data["phone"] and
                            updated_client.get("id") == client_id):
                            self.log_test("PUT /api/clients/{id} - Update client", True, 
                                        f"Client updated successfully: {updated_client['name']}")
                        else:
                            self.log_test("PUT /api/clients/{id} - Update client", False, 
                                        f"Update not reflected: {updated_client}")
                    else:
                        self.log_test("PUT /api/clients/{id} - Update client", False, 
                                    f"Status: {put_response.status_code}")
                    
                    # 5. DELETE /api/clients/{id} - Delete client
                    delete_response = self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                    if delete_response.status_code == 200:
                        # Verify deletion by trying to get the client
                        verify_response = self.session.get(f"{BACKEND_URL}/clients/{client_id}")
                        if verify_response.status_code == 404:
                            self.log_test("DELETE /api/clients/{id} - Delete client", True, 
                                        "Client successfully deleted")
                        else:
                            self.log_test("DELETE /api/clients/{id} - Delete client", False, 
                                        f"Client still exists after deletion: {verify_response.status_code}")
                    else:
                        self.log_test("DELETE /api/clients/{id} - Delete client", False, 
                                    f"Status: {delete_response.status_code}")
                        # Cleanup if delete failed
                        self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                        
                else:
                    self.log_test("POST /api/clients - Create client", False, 
                                f"Invalid response: {created_client}")
            else:
                self.log_test("POST /api/clients - Create client", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Clients CRUD Test", False, f"Exception: {str(e)}")
    
    def test_appointments_full_crud(self):
        """Test complete CRUD operations for appointments"""
        print("\n=== APPOINTMENTS FULL CRUD OPERATIONS ===")
        
        # First create a client for the appointment
        client_data = {
            "name": f"Michael Chen {uuid.uuid4().hex[:8]}",
            "email": f"michael.chen{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1-555-0456",
            "notes": "Client for appointment testing",
            "preferences": "",
            "hair_goals": "",
            "is_vip": False
        }
        
        try:
            client_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if client_response.status_code != 200:
                self.log_test("Appointments Test - Client Creation", False, "Failed to create test client")
                return
                
            client_id = client_response.json()["id"]
            client_name = client_response.json()["name"]
            
            # Test data
            appointment_data = {
                "client_id": client_id,
                "appointment_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "service": "Haircut and Styling",
                "duration_minutes": 90,
                "notes": "First appointment with new client",
                "status": "scheduled"
            }
            
            # 1. POST /api/appointments - Create appointment
            response = self.session.post(f"{BACKEND_URL}/appointments", json=appointment_data)
            if response.status_code == 200:
                created_appointment = response.json()
                if (created_appointment.get("id") and 
                    created_appointment.get("client_id") == client_id and
                    created_appointment.get("client_name")):
                    self.log_test("POST /api/appointments - Create appointment", True, 
                                f"Appointment created with ID: {created_appointment['id']}, Client: {created_appointment['client_name']}")
                    appointment_id = created_appointment["id"]
                    
                    # 2. GET /api/appointments - List all appointments
                    list_response = self.session.get(f"{BACKEND_URL}/appointments")
                    if list_response.status_code == 200:
                        appointments_list = list_response.json()
                        if isinstance(appointments_list, list) and any(a.get("id") == appointment_id for a in appointments_list):
                            self.log_test("GET /api/appointments - List all appointments", True, 
                                        f"Found {len(appointments_list)} appointments, including created appointment")
                        else:
                            self.log_test("GET /api/appointments - List all appointments", False, 
                                        f"Created appointment not found in list")
                    else:
                        self.log_test("GET /api/appointments - List all appointments", False, 
                                    f"Status: {list_response.status_code}")
                    
                    # 3. PUT /api/appointments/{id} - Update appointment
                    update_data = {
                        "client_id": client_id,
                        "appointment_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                        "service": "Haircut, Color, and Styling",
                        "duration_minutes": 150,
                        "notes": "Updated appointment - added color service",
                        "status": "scheduled"
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/appointments/{appointment_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_appointment = put_response.json()
                        if (updated_appointment.get("service") == update_data["service"] and 
                            updated_appointment.get("duration_minutes") == update_data["duration_minutes"] and
                            updated_appointment.get("client_name") and
                            updated_appointment.get("id") == appointment_id):
                            self.log_test("PUT /api/appointments/{id} - Update appointment", True, 
                                        f"Appointment updated: {updated_appointment['service']}, Client: {updated_appointment['client_name']}")
                        else:
                            self.log_test("PUT /api/appointments/{id} - Update appointment", False, 
                                        f"Update not reflected: {updated_appointment}")
                    else:
                        self.log_test("PUT /api/appointments/{id} - Update appointment", False, 
                                    f"Status: {put_response.status_code}")
                    
                    # 4. DELETE /api/appointments/{id} - Delete appointment
                    delete_response = self.session.delete(f"{BACKEND_URL}/appointments/{appointment_id}")
                    if delete_response.status_code == 200:
                        # Verify deletion by checking the list
                        verify_response = self.session.get(f"{BACKEND_URL}/appointments")
                        if verify_response.status_code == 200:
                            remaining_appointments = verify_response.json()
                            if not any(a.get("id") == appointment_id for a in remaining_appointments):
                                self.log_test("DELETE /api/appointments/{id} - Delete appointment", True, 
                                            "Appointment successfully deleted")
                            else:
                                self.log_test("DELETE /api/appointments/{id} - Delete appointment", False, 
                                            "Appointment still exists after deletion")
                        else:
                            self.log_test("DELETE /api/appointments/{id} - Delete appointment", False, 
                                        "Could not verify deletion")
                    else:
                        self.log_test("DELETE /api/appointments/{id} - Delete appointment", False, 
                                    f"Status: {delete_response.status_code}")
                        
                else:
                    self.log_test("POST /api/appointments - Create appointment", False, 
                                f"Invalid response: {created_appointment}")
            else:
                self.log_test("POST /api/appointments - Create appointment", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            
            # Cleanup client
            self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                
        except Exception as e:
            self.log_test("Appointments CRUD Test", False, f"Exception: {str(e)}")
    
    def test_formulas_full_crud(self):
        """Test complete CRUD operations for formulas"""
        print("\n=== FORMULAS FULL CRUD OPERATIONS ===")
        
        # First create a client for the formula
        client_data = {
            "name": f"Emma Rodriguez {uuid.uuid4().hex[:8]}",
            "email": f"emma.rodriguez{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1-555-0789",
            "notes": "Client for formula testing",
            "preferences": "Sensitive scalp",
            "hair_goals": "Maintain vibrant red color",
            "is_vip": True
        }
        
        try:
            client_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if client_response.status_code != 200:
                self.log_test("Formulas Test - Client Creation", False, "Failed to create test client")
                return
                
            client_id = client_response.json()["id"]
            
            # Test data
            formula_data = {
                "client_id": client_id,
                "formula_name": f"Vibrant Red Formula {uuid.uuid4().hex[:8]}",
                "formula_details": "Base: 6RR + 20vol developer (1:1 ratio), Processing time: 35 minutes, Toner: 9.13 + 10vol (1:2 ratio)",
                "date_created": datetime.utcnow().isoformat()
            }
            
            # 1. POST /api/formulas - Create formula
            response = self.session.post(f"{BACKEND_URL}/formulas", json=formula_data)
            if response.status_code == 200:
                created_formula = response.json()
                if (created_formula.get("id") and 
                    created_formula.get("client_id") == client_id and
                    created_formula.get("formula_name") == formula_data["formula_name"]):
                    self.log_test("POST /api/formulas - Create formula", True, 
                                f"Formula created with ID: {created_formula['id']}")
                    formula_id = created_formula["id"]
                    
                    # 2. GET /api/formulas - List all formulas
                    list_response = self.session.get(f"{BACKEND_URL}/formulas")
                    if list_response.status_code == 200:
                        formulas_list = list_response.json()
                        if isinstance(formulas_list, list) and any(f.get("id") == formula_id for f in formulas_list):
                            self.log_test("GET /api/formulas - List all formulas", True, 
                                        f"Found {len(formulas_list)} formulas, including created formula")
                        else:
                            self.log_test("GET /api/formulas - List all formulas", False, 
                                        f"Created formula not found in list")
                    else:
                        self.log_test("GET /api/formulas - List all formulas", False, 
                                    f"Status: {list_response.status_code}")
                    
                    # 3. PUT /api/formulas/{id} - Update formula
                    update_data = {
                        "client_id": client_id,
                        "formula_name": f"Updated Vibrant Red Formula {uuid.uuid4().hex[:8]}",
                        "formula_details": "UPDATED: Base: 6RR + 30vol developer (1:1.5 ratio), Processing time: 40 minutes, Toner: 9.13 + 10vol (1:2 ratio), Added bond builder"
                    }
                    
                    put_response = self.session.put(f"{BACKEND_URL}/formulas/{formula_id}", json=update_data)
                    if put_response.status_code == 200:
                        updated_formula = put_response.json()
                        if (updated_formula.get("formula_name") == update_data["formula_name"] and 
                            updated_formula.get("formula_details") == update_data["formula_details"] and
                            updated_formula.get("id") == formula_id):
                            self.log_test("PUT /api/formulas/{id} - Update formula", True, 
                                        f"Formula updated: {updated_formula['formula_name']}")
                        else:
                            self.log_test("PUT /api/formulas/{id} - Update formula", False, 
                                        f"Update not reflected: {updated_formula}")
                    else:
                        self.log_test("PUT /api/formulas/{id} - Update formula", False, 
                                    f"Status: {put_response.status_code}")
                    
                    # 4. DELETE /api/formulas/{id} - Delete formula
                    delete_response = self.session.delete(f"{BACKEND_URL}/formulas/{formula_id}")
                    if delete_response.status_code == 200:
                        # Verify deletion by checking the list
                        verify_response = self.session.get(f"{BACKEND_URL}/formulas")
                        if verify_response.status_code == 200:
                            remaining_formulas = verify_response.json()
                            if not any(f.get("id") == formula_id for f in remaining_formulas):
                                self.log_test("DELETE /api/formulas/{id} - Delete formula", True, 
                                            "Formula successfully deleted")
                            else:
                                self.log_test("DELETE /api/formulas/{id} - Delete formula", False, 
                                            "Formula still exists after deletion")
                        else:
                            self.log_test("DELETE /api/formulas/{id} - Delete formula", False, 
                                        "Could not verify deletion")
                    else:
                        self.log_test("DELETE /api/formulas/{id} - Delete formula", False, 
                                    f"Status: {delete_response.status_code}")
                        
                else:
                    self.log_test("POST /api/formulas - Create formula", False, 
                                f"Invalid response: {created_formula}")
            else:
                self.log_test("POST /api/formulas - Create formula", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
            
            # Cleanup client
            self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
                
        except Exception as e:
            self.log_test("Formulas CRUD Test", False, f"Exception: {str(e)}")
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        print("\n=== DASHBOARD STATISTICS ===")
        
        try:
            # GET /api/dashboard/stats - Verify returns stats object
            response = self.session.get(f"{BACKEND_URL}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                
                # Check for expected stats fields
                expected_fields = ["total_clients", "total_appointments", "monthly_income", "rebooking_alerts"]
                missing_fields = [field for field in expected_fields if field not in stats]
                
                if not missing_fields:
                    self.log_test("GET /api/dashboard/stats - Returns stats object", True, 
                                f"Stats: {stats['total_clients']} clients, {stats['total_appointments']} appointments, ${stats['monthly_income']} income")
                else:
                    self.log_test("GET /api/dashboard/stats - Returns stats object", False, 
                                f"Missing fields: {missing_fields}, Response: {stats}")
            else:
                self.log_test("GET /api/dashboard/stats - Returns stats object", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Dashboard Stats Test", False, f"Exception: {str(e)}")
    
    def test_data_persistence(self):
        """Test data persistence - create, then retrieve to verify data persists"""
        print("\n=== DATA PERSISTENCE VERIFICATION ===")
        
        try:
            # Create a client
            client_data = {
                "name": f"Persistence Test Client {uuid.uuid4().hex[:8]}",
                "email": f"persistence{uuid.uuid4().hex[:8]}@example.com",
                "phone": "+1-555-PERSIST",
                "notes": "Testing data persistence",
                "preferences": "Data must persist",
                "hair_goals": "Verify persistence",
                "is_vip": True
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/clients", json=client_data)
            if create_response.status_code == 200:
                created_client = create_response.json()
                client_id = created_client["id"]
                
                # Wait a moment then retrieve to verify persistence
                import time
                time.sleep(1)
                
                retrieve_response = self.session.get(f"{BACKEND_URL}/clients/{client_id}")
                if retrieve_response.status_code == 200:
                    retrieved_client = retrieve_response.json()
                    
                    # Verify all data persisted correctly
                    if (retrieved_client.get("name") == client_data["name"] and
                        retrieved_client.get("email") == client_data["email"] and
                        retrieved_client.get("phone") == client_data["phone"] and
                        retrieved_client.get("notes") == client_data["notes"] and
                        retrieved_client.get("is_vip") == client_data["is_vip"]):
                        
                        self.log_test("Data Persistence - Create then Retrieve", True, 
                                    f"All data persisted correctly for client: {retrieved_client['name']}")
                    else:
                        self.log_test("Data Persistence - Create then Retrieve", False, 
                                    f"Data mismatch. Created: {client_data}, Retrieved: {retrieved_client}")
                else:
                    self.log_test("Data Persistence - Create then Retrieve", False, 
                                f"Failed to retrieve created client: {retrieve_response.status_code}")
                
                # Cleanup
                self.session.delete(f"{BACKEND_URL}/clients/{client_id}")
            else:
                self.log_test("Data Persistence - Create then Retrieve", False, 
                            f"Failed to create client: {create_response.status_code}")
                
        except Exception as e:
            self.log_test("Data Persistence Test", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all comprehensive CRUD tests"""
        print("StyleFlow Backend API Testing - OFFLINE-FIRST and REAL-TIME SYNC")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run comprehensive CRUD tests
        self.test_clients_full_crud()
        self.test_appointments_full_crud()
        self.test_formulas_full_crud()
        self.test_dashboard_stats()
        self.test_data_persistence()
        
        # Run existing real-time sync tests
        self.test_clients_crud_with_full_objects()
        self.test_formulas_crud_with_full_objects()
        self.test_appointments_crud_with_full_objects()
        self.test_appointment_status_completion_flow()
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
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