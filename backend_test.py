#!/usr/bin/env python3
"""
StyleFlow Backend API Test Suite
Comprehensive testing for all StyleFlow backend endpoints
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import base64

class StyleFlowAPITester:
    def __init__(self):
        # Get backend URL from frontend .env file
        self.base_url = self.get_backend_url()
        self.session = None
        self.auth_token = None
        self.test_user_email = "sarah.mitchell@hairsalon.com"
        self.test_user_password = "StrongPassword123!"
        self.test_user_name = "Sarah Mitchell"
        self.test_business_name = "Elegant Hair Studio"
        
        # Store created IDs for cleanup
        self.created_client_id = None
        self.created_appointment_id = None
        self.created_formula_id = None
        self.created_gallery_id = None
        self.created_income_id = None
        self.created_retail_id = None
        self.created_no_show_id = None
        
        # Test results
        self.test_results = {}
        self.failed_tests = []
        
    def get_backend_url(self) -> str:
        """Get backend URL from frontend .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('EXPO_PUBLIC_BACKEND_URL'):
                        url = line.split('=')[1].strip()
                        return f"{url}/api"
            return "https://hairflow-app-1.preview.emergentagent.com/api"  # fallback
        except:
            return "https://hairflow-app-1.preview.emergentagent.com/api"  # fallback
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        print(f"🔧 Testing backend at: {self.base_url}")
    
    async def cleanup(self):
        """Cleanup test session and data"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          headers: Optional[Dict] = None) -> tuple[int, Dict]:
        """Make HTTP request and return status code and response"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if self.auth_token:
            request_headers["Authorization"] = f"Bearer {self.auth_token}"
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                async with self.session.get(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status, response_data
            
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status, response_data
            
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status, response_data
            
            elif method.upper() == "DELETE":
                async with self.session.delete(url, headers=request_headers) as response:
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"error": "Invalid JSON response"}
                    return response.status, response_data
                    
        except Exception as e:
            return 500, {"error": f"Request failed: {str(e)}"}
    
    def log_test_result(self, test_name: str, passed: bool, message: str = "", response_data: Dict = None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if not passed and response_data:
            print(f"    Response: {response_data}")
        
        self.test_results[test_name] = {
            "passed": passed,
            "message": message,
            "response": response_data
        }
        
        if not passed:
            self.failed_tests.append(test_name)
    
    # ==================== AUTHENTICATION TESTS ====================
    
    async def test_auth_signup(self):
        """Test user signup"""
        print("\n📝 Testing Authentication - Signup")
        
        # First, try to delete existing user if any
        try:
            await self.make_request("DELETE", "/auth/delete-account")
        except:
            pass
        
        signup_data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "full_name": self.test_user_name,
            "business_name": self.test_business_name
        }
        
        status_code, response = await self.make_request("POST", "/auth/signup", signup_data)
        
        if status_code == 200 and "token" in response and "user" in response:
            self.auth_token = response["token"]
            self.log_test_result("Auth Signup", True, f"User created with token: {response['token'][:20]}...")
            return True
        else:
            self.log_test_result("Auth Signup", False, f"Status: {status_code}", response)
            return False
    
    async def test_auth_login(self):
        """Test user login"""
        print("\n🔐 Testing Authentication - Login")
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        status_code, response = await self.make_request("POST", "/auth/login", login_data)
        
        if status_code == 200 and "token" in response:
            self.auth_token = response["token"]
            self.log_test_result("Auth Login", True, f"Login successful with token: {response['token'][:20]}...")
            return True
        else:
            self.log_test_result("Auth Login", False, f"Status: {status_code}", response)
            return False
    
    async def test_auth_me(self):
        """Test get current user profile"""
        print("\n👤 Testing Authentication - Get Me")
        
        status_code, response = await self.make_request("GET", "/auth/me")
        
        if status_code == 200 and "email" in response and response["email"] == self.test_user_email:
            self.log_test_result("Auth Get Me", True, f"Profile retrieved for {response['email']}")
            return True
        else:
            self.log_test_result("Auth Get Me", False, f"Status: {status_code}", response)
            return False
    
    async def test_auth_profile_update(self):
        """Test profile update"""
        print("\n✏️ Testing Authentication - Update Profile")
        
        update_data = {
            "bio": "Experienced hair stylist specializing in color and cuts",
            "specialties": "Color correction, Balayage, Precision cuts",
            "salon_info": "Located in downtown, accepting new clients"
        }
        
        status_code, response = await self.make_request("PUT", "/auth/profile", update_data)
        
        if status_code == 200:
            self.log_test_result("Auth Update Profile", True, "Profile updated successfully")
            return True
        else:
            self.log_test_result("Auth Update Profile", False, f"Status: {status_code}", response)
            return False
    
    async def test_auth_forgot_password(self):
        """Test forgot password"""
        print("\n🔄 Testing Authentication - Forgot Password")
        
        forgot_data = {"email": self.test_user_email}
        
        status_code, response = await self.make_request("POST", "/auth/forgot-password", forgot_data)
        
        if status_code == 200 and "message" in response:
            self.log_test_result("Auth Forgot Password", True, "Forgot password request processed")
            return True
        else:
            self.log_test_result("Auth Forgot Password", False, f"Status: {status_code}", response)
            return False
    
    async def test_auth_reset_password(self):
        """Test password reset"""
        print("\n🔑 Testing Authentication - Reset Password")
        
        reset_data = {
            "email": self.test_user_email,
            "new_password": "NewStrongPassword123!"
        }
        
        status_code, response = await self.make_request("POST", "/auth/reset-password", reset_data)
        
        if status_code == 200 and "message" in response:
            # Update our password for future tests
            self.test_user_password = "NewStrongPassword123!"
            self.log_test_result("Auth Reset Password", True, "Password reset successful")
            return True
        else:
            self.log_test_result("Auth Reset Password", False, f"Status: {status_code}", response)
            return False
    
    # ==================== CLIENT TESTS ====================
    
    async def test_client_create(self):
        """Test client creation"""
        print("\n👥 Testing Clients - Create")
        
        # Sample base64 image (small placeholder)
        sample_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        client_data = {
            "name": "Emma Rodriguez",
            "email": "emma.rodriguez@email.com",
            "phone": "(555) 123-4567",
            "photo": sample_photo,
            "notes": "Regular client, loves natural highlights",
            "preferences": "No ammonia products, prefers organic options",
            "hair_goals": "Maintain healthy blonde highlights with subtle lowlights",
            "is_vip": True
        }
        
        status_code, response = await self.make_request("POST", "/clients", client_data)
        
        if status_code == 200 and "id" in response:
            self.created_client_id = response["id"]
            self.log_test_result("Client Create", True, f"Client created with ID: {self.created_client_id}")
            return True
        else:
            self.log_test_result("Client Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_client_list(self):
        """Test client listing"""
        print("\n📋 Testing Clients - List")
        
        status_code, response = await self.make_request("GET", "/clients")
        
        if status_code == 200 and isinstance(response, list):
            client_found = any(c.get("id") == self.created_client_id for c in response)
            if client_found:
                self.log_test_result("Client List", True, f"Found {len(response)} clients including our test client")
                return True
            else:
                self.log_test_result("Client List", False, "Test client not found in list", response)
                return False
        else:
            self.log_test_result("Client List", False, f"Status: {status_code}", response)
            return False
    
    async def test_client_get(self):
        """Test getting specific client"""
        print("\n🔍 Testing Clients - Get by ID")
        
        if not self.created_client_id:
            self.log_test_result("Client Get", False, "No client ID available")
            return False
        
        status_code, response = await self.make_request("GET", f"/clients/{self.created_client_id}")
        
        if status_code == 200 and response.get("id") == self.created_client_id:
            self.log_test_result("Client Get", True, f"Retrieved client: {response.get('name')}")
            return True
        else:
            self.log_test_result("Client Get", False, f"Status: {status_code}", response)
            return False
    
    async def test_client_update(self):
        """Test client update"""
        print("\n✏️ Testing Clients - Update")
        
        if not self.created_client_id:
            self.log_test_result("Client Update", False, "No client ID available")
            return False
        
        update_data = {
            "notes": "Updated notes: Client now prefers weekend appointments",
            "visit_count": 1
        }
        
        status_code, response = await self.make_request("PUT", f"/clients/{self.created_client_id}", update_data)
        
        if status_code == 200:
            self.log_test_result("Client Update", True, "Client updated successfully")
            return True
        else:
            self.log_test_result("Client Update", False, f"Status: {status_code}", response)
            return False
    
    # ==================== APPOINTMENT TESTS ====================
    
    async def test_appointment_create(self):
        """Test appointment creation"""
        print("\n📅 Testing Appointments - Create")
        
        if not self.created_client_id:
            self.log_test_result("Appointment Create", False, "No client ID available")
            return False
        
        # Create appointment for tomorrow
        tomorrow = datetime.utcnow() + timedelta(days=1)
        
        appointment_data = {
            "client_id": self.created_client_id,
            "appointment_date": tomorrow.isoformat(),
            "service": "Full Color & Cut",
            "duration_minutes": 120,
            "notes": "Balayage with toner, trim 2 inches",
            "status": "scheduled"
        }
        
        status_code, response = await self.make_request("POST", "/appointments", appointment_data)
        
        if status_code == 200 and "id" in response:
            self.created_appointment_id = response["id"]
            self.log_test_result("Appointment Create", True, f"Appointment created with ID: {self.created_appointment_id}")
            return True
        else:
            self.log_test_result("Appointment Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_appointment_list(self):
        """Test appointment listing"""
        print("\n📋 Testing Appointments - List")
        
        status_code, response = await self.make_request("GET", "/appointments")
        
        if status_code == 200 and isinstance(response, list):
            appointment_found = any(a.get("id") == self.created_appointment_id for a in response)
            if appointment_found:
                self.log_test_result("Appointment List", True, f"Found {len(response)} appointments including our test appointment")
                return True
            else:
                self.log_test_result("Appointment List", False, "Test appointment not found in list", response)
                return False
        else:
            self.log_test_result("Appointment List", False, f"Status: {status_code}", response)
            return False
    
    async def test_appointment_update(self):
        """Test appointment update"""
        print("\n✏️ Testing Appointments - Update")
        
        if not self.created_appointment_id:
            self.log_test_result("Appointment Update", False, "No appointment ID available")
            return False
        
        update_data = {
            "status": "completed",
            "notes": "Completed successfully - client loved the new color!"
        }
        
        status_code, response = await self.make_request("PUT", f"/appointments/{self.created_appointment_id}", update_data)
        
        if status_code == 200:
            self.log_test_result("Appointment Update", True, "Appointment status updated to completed")
            return True
        else:
            self.log_test_result("Appointment Update", False, f"Status: {status_code}", response)
            return False
    
    # ==================== FORMULA TESTS ====================
    
    async def test_formula_create(self):
        """Test formula creation"""
        print("\n🧪 Testing Formulas - Create")
        
        if not self.created_client_id:
            self.log_test_result("Formula Create", False, "No client ID available")
            return False
        
        formula_data = {
            "client_id": self.created_client_id,
            "formula_name": "Emma's Signature Blonde",
            "formula_details": "Base: Level 7 Natural, Lightener: 30vol + Olaplex, Toner: 9A + 9N (3:1 ratio), Processing time: 45min"
        }
        
        status_code, response = await self.make_request("POST", "/formulas", formula_data)
        
        if status_code == 200 and "id" in response:
            self.created_formula_id = response["id"]
            self.log_test_result("Formula Create", True, f"Formula created with ID: {self.created_formula_id}")
            return True
        else:
            self.log_test_result("Formula Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_formula_list(self):
        """Test formula listing"""
        print("\n📋 Testing Formulas - List")
        
        status_code, response = await self.make_request("GET", "/formulas")
        
        if status_code == 200 and isinstance(response, list):
            formula_found = any(f.get("id") == self.created_formula_id for f in response)
            if formula_found:
                self.log_test_result("Formula List", True, f"Found {len(response)} formulas including our test formula")
                return True
            else:
                self.log_test_result("Formula List", False, "Test formula not found in list", response)
                return False
        else:
            self.log_test_result("Formula List", False, f"Status: {status_code}", response)
            return False
    
    async def test_formula_by_client(self):
        """Test formula filtering by client"""
        print("\n🔍 Testing Formulas - Filter by Client")
        
        if not self.created_client_id:
            self.log_test_result("Formula Filter by Client", False, "No client ID available")
            return False
        
        status_code, response = await self.make_request("GET", f"/formulas?client_id={self.created_client_id}")
        
        if status_code == 200 and isinstance(response, list):
            formula_found = any(f.get("id") == self.created_formula_id for f in response)
            if formula_found:
                self.log_test_result("Formula Filter by Client", True, f"Found formulas for client")
                return True
            else:
                self.log_test_result("Formula Filter by Client", False, "Test formula not found for client", response)
                return False
        else:
            self.log_test_result("Formula Filter by Client", False, f"Status: {status_code}", response)
            return False
    
    async def test_formula_update(self):
        """Test formula update"""
        print("\n✏️ Testing Formulas - Update")
        
        if not self.created_formula_id:
            self.log_test_result("Formula Update", False, "No formula ID available")
            return False
        
        update_data = {
            "formula_details": "Updated formula: Base: Level 7 Natural, Lightener: 20vol + Olaplex, Toner: 9A + 9N (2:1 ratio), Processing time: 35min"
        }
        
        status_code, response = await self.make_request("PUT", f"/formulas/{self.created_formula_id}", update_data)
        
        if status_code == 200:
            self.log_test_result("Formula Update", True, "Formula updated successfully")
            return True
        else:
            self.log_test_result("Formula Update", False, f"Status: {status_code}", response)
            return False
    
    # ==================== GALLERY TESTS ====================
    
    async def test_gallery_create(self):
        """Test gallery creation"""
        print("\n📸 Testing Gallery - Create")
        
        if not self.created_client_id:
            self.log_test_result("Gallery Create", False, "No client ID available")
            return False
        
        # Sample base64 images
        before_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        after_photo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwABIgCr7Q7/0gAAAABJRU5ErkJggg=="
        
        gallery_data = {
            "client_id": self.created_client_id,
            "before_photo": before_photo,
            "after_photo": after_photo,
            "notes": "Dramatic transformation - blonde balayage on dark brown hair"
        }
        
        status_code, response = await self.make_request("POST", "/gallery", gallery_data)
        
        if status_code == 200 and "id" in response:
            self.created_gallery_id = response["id"]
            self.log_test_result("Gallery Create", True, f"Gallery item created with ID: {self.created_gallery_id}")
            return True
        else:
            self.log_test_result("Gallery Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_gallery_list(self):
        """Test gallery listing"""
        print("\n📋 Testing Gallery - List")
        
        status_code, response = await self.make_request("GET", "/gallery")
        
        if status_code == 200 and isinstance(response, list):
            gallery_found = any(g.get("id") == self.created_gallery_id for g in response)
            if gallery_found:
                self.log_test_result("Gallery List", True, f"Found {len(response)} gallery items including our test item")
                return True
            else:
                self.log_test_result("Gallery List", False, "Test gallery item not found in list", response)
                return False
        else:
            self.log_test_result("Gallery List", False, f"Status: {status_code}", response)
            return False
    
    async def test_gallery_by_client(self):
        """Test gallery filtering by client"""
        print("\n🔍 Testing Gallery - Filter by Client")
        
        if not self.created_client_id:
            self.log_test_result("Gallery Filter by Client", False, "No client ID available")
            return False
        
        status_code, response = await self.make_request("GET", f"/gallery?client_id={self.created_client_id}")
        
        if status_code == 200 and isinstance(response, list):
            gallery_found = any(g.get("id") == self.created_gallery_id for g in response)
            if gallery_found:
                self.log_test_result("Gallery Filter by Client", True, f"Found gallery items for client")
                return True
            else:
                self.log_test_result("Gallery Filter by Client", False, "Test gallery item not found for client", response)
                return False
        else:
            self.log_test_result("Gallery Filter by Client", False, f"Status: {status_code}", response)
            return False
    
    # ==================== INCOME TESTS ====================
    
    async def test_income_create(self):
        """Test income creation"""
        print("\n💰 Testing Income - Create")
        
        income_data = {
            "client_id": self.created_client_id,
            "amount": 185.00,
            "service": "Full Color & Cut",
            "payment_method": "Credit Card"
        }
        
        status_code, response = await self.make_request("POST", "/income", income_data)
        
        if status_code == 200 and "id" in response:
            self.created_income_id = response["id"]
            self.log_test_result("Income Create", True, f"Income record created with ID: {self.created_income_id}")
            return True
        else:
            self.log_test_result("Income Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_income_list(self):
        """Test income listing"""
        print("\n📋 Testing Income - List")
        
        status_code, response = await self.make_request("GET", "/income")
        
        if status_code == 200 and isinstance(response, list):
            income_found = any(i.get("id") == self.created_income_id for i in response)
            if income_found:
                self.log_test_result("Income List", True, f"Found {len(response)} income records including our test record")
                return True
            else:
                self.log_test_result("Income List", False, "Test income record not found in list", response)
                return False
        else:
            self.log_test_result("Income List", False, f"Status: {status_code}", response)
            return False
    
    async def test_income_stats(self):
        """Test income statistics"""
        print("\n📊 Testing Income - Statistics")
        
        status_code, response = await self.make_request("GET", "/income/stats")
        
        if status_code == 200 and "total" in response and "today" in response:
            self.log_test_result("Income Stats", True, f"Income stats - Total: ${response['total']}, Today: ${response['today']}")
            return True
        else:
            self.log_test_result("Income Stats", False, f"Status: {status_code}", response)
            return False
    
    # ==================== RETAIL & NO-SHOW TESTS ====================
    
    async def test_retail_create(self):
        """Test retail creation"""
        print("\n🛍️ Testing Retail - Create")
        
        if not self.created_client_id:
            self.log_test_result("Retail Create", False, "No client ID available")
            return False
        
        retail_data = {
            "client_id": self.created_client_id,
            "product_name": "Olaplex No. 3 Hair Perfector",
            "recommended": True,
            "purchased": True
        }
        
        status_code, response = await self.make_request("POST", "/retail", retail_data)
        
        if status_code == 200 and "id" in response:
            self.created_retail_id = response["id"]
            self.log_test_result("Retail Create", True, f"Retail record created with ID: {self.created_retail_id}")
            return True
        else:
            self.log_test_result("Retail Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_retail_list(self):
        """Test retail listing"""
        print("\n📋 Testing Retail - List")
        
        status_code, response = await self.make_request("GET", "/retail")
        
        if status_code == 200 and isinstance(response, list):
            retail_found = any(r.get("id") == self.created_retail_id for r in response)
            if retail_found:
                self.log_test_result("Retail List", True, f"Found {len(response)} retail records including our test record")
                return True
            else:
                self.log_test_result("Retail List", False, "Test retail record not found in list", response)
                return False
        else:
            self.log_test_result("Retail List", False, f"Status: {status_code}", response)
            return False
    
    async def test_no_show_create(self):
        """Test no-show creation"""
        print("\n❌ Testing No-Shows - Create")
        
        if not self.created_client_id:
            self.log_test_result("No-Show Create", False, "No client ID available")
            return False
        
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        no_show_data = {
            "client_id": self.created_client_id,
            "appointment_date": yesterday.isoformat(),
            "notes": "Client did not show up for scheduled appointment"
        }
        
        status_code, response = await self.make_request("POST", "/no-shows", no_show_data)
        
        if status_code == 200 and "id" in response:
            self.created_no_show_id = response["id"]
            self.log_test_result("No-Show Create", True, f"No-show record created with ID: {self.created_no_show_id}")
            return True
        else:
            self.log_test_result("No-Show Create", False, f"Status: {status_code}", response)
            return False
    
    async def test_no_show_list(self):
        """Test no-show listing"""
        print("\n📋 Testing No-Shows - List")
        
        status_code, response = await self.make_request("GET", "/no-shows")
        
        if status_code == 200 and isinstance(response, list):
            no_show_found = any(ns.get("id") == self.created_no_show_id for ns in response)
            if no_show_found:
                self.log_test_result("No-Show List", True, f"Found {len(response)} no-show records including our test record")
                return True
            else:
                self.log_test_result("No-Show List", False, "Test no-show record not found in list", response)
                return False
        else:
            self.log_test_result("No-Show List", False, f"Status: {status_code}", response)
            return False
    
    # ==================== AI & DASHBOARD TESTS ====================
    
    async def test_ai_chat(self):
        """Test AI chat assistant"""
        print("\n🤖 Testing AI Chat Assistant")
        
        ai_data = {
            "message": "What are some good follow-up care tips for a client who just got blonde balayage?",
            "context": "Client has naturally dark brown hair, first time going blonde"
        }
        
        status_code, response = await self.make_request("POST", "/ai/chat", ai_data)
        
        if status_code == 200 and "response" in response and len(response["response"]) > 50:
            self.log_test_result("AI Chat", True, f"AI responded with {len(response['response'])} characters")
            return True
        else:
            self.log_test_result("AI Chat", False, f"Status: {status_code}", response)
            return False
    
    async def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n📊 Testing Dashboard Statistics")
        
        status_code, response = await self.make_request("GET", "/dashboard/stats")
        
        required_fields = ["total_clients", "vip_clients", "today_appointments", "week_appointments", 
                          "today_income", "week_income", "month_income", "clients_due_rebooking"]
        
        if status_code == 200 and all(field in response for field in required_fields):
            self.log_test_result("Dashboard Stats", True, f"All required dashboard metrics present")
            return True
        else:
            missing_fields = [f for f in required_fields if f not in response]
            self.log_test_result("Dashboard Stats", False, f"Status: {status_code}, Missing fields: {missing_fields}", response)
            return False
    
    # ==================== AUTHORIZATION TESTS ====================
    
    async def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        print("\n🔒 Testing Authorization - Unauthorized Access")
        
        # Temporarily remove auth token
        original_token = self.auth_token
        self.auth_token = None
        
        status_code, response = await self.make_request("GET", "/clients")
        
        # Restore auth token
        self.auth_token = original_token
        
        if status_code == 401:
            self.log_test_result("Authorization Check", True, "Correctly blocked unauthorized access")
            return True
        else:
            self.log_test_result("Authorization Check", False, f"Should have returned 401, got {status_code}", response)
            return False
    
    async def test_invalid_token(self):
        """Test that invalid tokens are rejected"""
        print("\n🔒 Testing Authorization - Invalid Token")
        
        # Temporarily set invalid auth token
        original_token = self.auth_token
        self.auth_token = "invalid_token_123"
        
        status_code, response = await self.make_request("GET", "/auth/me")
        
        # Restore auth token
        self.auth_token = original_token
        
        if status_code == 401:
            self.log_test_result("Invalid Token Check", True, "Correctly rejected invalid token")
            return True
        else:
            self.log_test_result("Invalid Token Check", False, f"Should have returned 401, got {status_code}", response)
            return False
    
    # ==================== DATA DELETION TESTS ====================
    
    async def test_data_cleanup(self):
        """Test deletion of created test data"""
        print("\n🗑️ Testing Data Cleanup")
        
        cleanup_results = []
        
        # Delete in reverse order to handle dependencies
        if self.created_no_show_id:
            status_code, _ = await self.make_request("DELETE", f"/no-shows/{self.created_no_show_id}")
            cleanup_results.append(("No-Show", status_code == 200))
        
        if self.created_retail_id:
            status_code, _ = await self.make_request("DELETE", f"/retail/{self.created_retail_id}")
            cleanup_results.append(("Retail", status_code == 200))
        
        if self.created_gallery_id:
            status_code, _ = await self.make_request("DELETE", f"/gallery/{self.created_gallery_id}")
            cleanup_results.append(("Gallery", status_code == 200))
        
        if self.created_formula_id:
            status_code, _ = await self.make_request("DELETE", f"/formulas/{self.created_formula_id}")
            cleanup_results.append(("Formula", status_code == 200))
        
        if self.created_appointment_id:
            status_code, _ = await self.make_request("DELETE", f"/appointments/{self.created_appointment_id}")
            cleanup_results.append(("Appointment", status_code == 200))
        
        if self.created_client_id:
            status_code, _ = await self.make_request("DELETE", f"/clients/{self.created_client_id}")
            cleanup_results.append(("Client", status_code == 200))
        
        all_deleted = all(result[1] for result in cleanup_results)
        
        if all_deleted:
            self.log_test_result("Data Cleanup", True, f"Successfully deleted all test data")
            return True
        else:
            failed_deletes = [item[0] for item in cleanup_results if not item[1]]
            self.log_test_result("Data Cleanup", False, f"Failed to delete: {failed_deletes}")
            return False
    
    async def test_account_deletion(self):
        """Test account deletion"""
        print("\n🗑️ Testing Account Deletion")
        
        status_code, response = await self.make_request("DELETE", "/auth/delete-account")
        
        if status_code == 200:
            self.log_test_result("Account Deletion", True, "Account deleted successfully")
            return True
        else:
            self.log_test_result("Account Deletion", False, f"Status: {status_code}", response)
            return False
    
    # ==================== MAIN TEST RUNNER ====================
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting StyleFlow Backend API Tests")
        print("="*60)
        
        await self.setup()
        
        try:
            # Authentication flow
            await self.test_auth_signup()
            await self.test_auth_login()
            await self.test_auth_me()
            await self.test_auth_profile_update()
            await self.test_auth_forgot_password()
            await self.test_auth_reset_password()
            
            # Re-login with new password
            await self.test_auth_login()
            
            # Client management
            await self.test_client_create()
            await self.test_client_list()
            await self.test_client_get()
            await self.test_client_update()
            
            # Appointments
            await self.test_appointment_create()
            await self.test_appointment_list()
            await self.test_appointment_update()
            
            # Formulas
            await self.test_formula_create()
            await self.test_formula_list()
            await self.test_formula_by_client()
            await self.test_formula_update()
            
            # Gallery
            await self.test_gallery_create()
            await self.test_gallery_list()
            await self.test_gallery_by_client()
            
            # Income tracking
            await self.test_income_create()
            await self.test_income_list()
            await self.test_income_stats()
            
            # Retail & No-shows
            await self.test_retail_create()
            await self.test_retail_list()
            await self.test_no_show_create()
            await self.test_no_show_list()
            
            # AI & Dashboard
            await self.test_ai_chat()
            await self.test_dashboard_stats()
            
            # Authorization
            await self.test_unauthorized_access()
            await self.test_invalid_token()
            
            # Cleanup
            await self.test_data_cleanup()
            await self.test_account_deletion()
            
        finally:
            await self.cleanup()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        passed_tests = [name for name, result in self.test_results.items() if result["passed"]]
        failed_tests = [name for name, result in self.test_results.items() if not result["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print(f"📈 SUCCESS RATE: {len(passed_tests)/(len(passed_tests) + len(failed_tests)) * 100:.1f}%")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test_name in failed_tests:
                result = self.test_results[test_name]
                print(f"  - {test_name}: {result['message']}")
        
        print("\n🎯 COVERAGE:")
        print("  - Authentication: ✅")
        print("  - Client Management: ✅")
        print("  - Appointments: ✅")
        print("  - Formula Vault: ✅")
        print("  - Gallery: ✅")
        print("  - Income Tracking: ✅")
        print("  - Retail & No-Shows: ✅")
        print("  - AI Assistant: ✅")
        print("  - Dashboard Stats: ✅")
        print("  - Authorization: ✅")

async def main():
    """Main test execution"""
    tester = StyleFlowAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())