#!/usr/bin/env python3
"""
FINAL APPLE STORE VERIFICATION - Complete StyleFlow Backend API Test
Tests all critical endpoints with Apple tester credentials for App Store submission
"""

import requests
import json
import sys
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:8001/api"
APPLE_TESTER_EMAIL = "appreview@apple.com"
APPLE_TESTER_PASSWORD = "AppleTest123!"

class StyleFlowAPITest:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.test_results = []
        self.created_resources = {
            'clients': [],
            'formulas': [],
            'appointments': [],
            'posts': []
        }
        
    def log_test(self, test_name: str, success: bool, details: str = "", status_code: int = None):
        """Log test result with detailed information"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "status_code": status_code
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if status_code:
            print(f"   Status Code: {status_code}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
        """Make authenticated API request"""
        url = f"{BASE_URL}{endpoint}"
        request_headers = {}
        
        if self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        
        if headers:
            request_headers.update(headers)
            
        try:
            if method.upper() == "GET":
                return self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                return self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                return self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                return self.session.delete(url, headers=request_headers)
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None
    
    def test_authentication(self) -> bool:
        """Test authentication endpoints"""
        print("\n🔐 TESTING AUTHENTICATION")
        print("-" * 40)
        
        # Test login
        try:
            response = self.make_request("POST", "/auth/login", {
                "email": APPLE_TESTER_EMAIL,
                "password": APPLE_TESTER_PASSWORD
            })
            
            if response and response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token") or data.get("token")
                is_tester = data.get("is_tester", False)
                
                self.log_test("POST /auth/login", True, 
                             f"Login successful, is_tester: {is_tester}", response.status_code)
                
                # Test /auth/me
                me_response = self.make_request("GET", "/auth/me")
                if me_response and me_response.status_code == 200:
                    user_data = me_response.json()
                    self.user_id = user_data.get("id")
                    is_tester_me = user_data.get("is_tester", False)
                    
                    self.log_test("GET /auth/me", True, 
                                 f"User ID: {self.user_id}, is_tester: {is_tester_me}", 
                                 me_response.status_code)
                    return True
                else:
                    self.log_test("GET /auth/me", False, 
                                 f"Failed to get user profile", 
                                 me_response.status_code if me_response else None)
                    return False
            else:
                self.log_test("POST /auth/login", False, 
                             f"Login failed", 
                             response.status_code if response else None)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_dashboard(self) -> bool:
        """Test dashboard statistics"""
        print("\n📊 TESTING DASHBOARD")
        print("-" * 40)
        
        try:
            response = self.make_request("GET", "/dashboard/stats")
            
            if response and response.status_code == 200:
                stats = response.json()
                required_fields = ["total_clients", "today_appointments", "vip_clients"]
                
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    self.log_test("GET /dashboard/stats", True, 
                                 f"Stats retrieved: {json.dumps(stats, indent=2)}", 
                                 response.status_code)
                    return True
                else:
                    self.log_test("GET /dashboard/stats", False, 
                                 f"Missing fields: {missing_fields}", 
                                 response.status_code)
                    return False
            else:
                self.log_test("GET /dashboard/stats", False, 
                             "Failed to get dashboard stats", 
                             response.status_code if response else None)
                return False
                
        except Exception as e:
            self.log_test("Dashboard", False, f"Exception: {str(e)}")
            return False
    
    def test_clients_crud(self) -> bool:
        """Test clients CRUD operations"""
        print("\n👥 TESTING CLIENTS CRUD")
        print("-" * 40)
        
        success_count = 0
        total_tests = 4
        
        # Test GET /clients
        try:
            response = self.make_request("GET", "/clients")
            if response and response.status_code == 200:
                clients = response.json()
                self.log_test("GET /clients", True, 
                             f"Retrieved {len(clients)} clients", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /clients", False, 
                             "Failed to get clients", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /clients", False, f"Exception: {str(e)}")
        
        # Test POST /clients
        try:
            client_data = {
                "name": "Apple Test Client",
                "email": "testclient@apple.com",
                "phone": "+1-555-0123",
                "notes": "Test client for Apple Store review",
                "is_vip": False
            }
            
            response = self.make_request("POST", "/clients", client_data)
            if response and response.status_code in [200, 201]:
                client = response.json()
                client_id = client.get("id")
                if client_id:
                    self.created_resources['clients'].append(client_id)
                    self.log_test("POST /clients", True, 
                                 f"Created client with ID: {client_id}", response.status_code)
                    success_count += 1
                    
                    # Test GET /clients/{id}
                    get_response = self.make_request("GET", f"/clients/{client_id}")
                    if get_response and get_response.status_code == 200:
                        self.log_test("GET /clients/{id}", True, 
                                     f"Retrieved client {client_id}", get_response.status_code)
                        success_count += 1
                    else:
                        self.log_test("GET /clients/{id}", False, 
                                     f"Failed to get client {client_id}", 
                                     get_response.status_code if get_response else None)
                else:
                    self.log_test("POST /clients", False, "No client ID returned")
            else:
                self.log_test("POST /clients", False, 
                             "Failed to create client", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("POST /clients", False, f"Exception: {str(e)}")
        
        # Test DELETE /clients/{id}
        if self.created_resources['clients']:
            try:
                client_id = self.created_resources['clients'][0]
                response = self.make_request("DELETE", f"/clients/{client_id}")
                if response and response.status_code == 200:
                    self.log_test("DELETE /clients/{id}", True, 
                                 f"Deleted client {client_id}", response.status_code)
                    success_count += 1
                    self.created_resources['clients'].remove(client_id)
                else:
                    self.log_test("DELETE /clients/{id}", False, 
                                 f"Failed to delete client {client_id}", 
                                 response.status_code if response else None)
            except Exception as e:
                self.log_test("DELETE /clients/{id}", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_formulas_crud(self) -> bool:
        """Test formulas CRUD operations"""
        print("\n🧪 TESTING FORMULAS CRUD")
        print("-" * 40)
        
        success_count = 0
        total_tests = 3
        
        # First, ensure we have a client for the formula
        client_id = None
        if self.created_resources['clients']:
            client_id = self.created_resources['clients'][0]
        else:
            # Create a temporary client
            client_data = {
                "name": "Formula Test Client",
                "email": "formulaclient@apple.com",
                "phone": "+1-555-0124"
            }
            response = self.make_request("POST", "/clients", client_data)
            if response and response.status_code in [200, 201]:
                client = response.json()
                client_id = client.get("id")
                self.created_resources['clients'].append(client_id)
        
        if not client_id:
            self.log_test("Formulas CRUD", False, "No client available for formula testing")
            return False
        
        # Test GET /formulas
        try:
            response = self.make_request("GET", "/formulas")
            if response and response.status_code == 200:
                formulas = response.json()
                self.log_test("GET /formulas", True, 
                             f"Retrieved {len(formulas)} formulas", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /formulas", False, 
                             "Failed to get formulas", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /formulas", False, f"Exception: {str(e)}")
        
        # Test POST /formulas
        try:
            formula_data = {
                "client_id": client_id,
                "formula_name": "Apple Test Formula",
                "formula_details": "20vol + Ash Blonde - Test formula for Apple Store review"
            }
            
            response = self.make_request("POST", "/formulas", formula_data)
            if response and response.status_code in [200, 201]:
                formula = response.json()
                formula_id = formula.get("id")
                if formula_id:
                    self.created_resources['formulas'].append(formula_id)
                    self.log_test("POST /formulas", True, 
                                 f"Created formula with ID: {formula_id}", response.status_code)
                    success_count += 1
                else:
                    self.log_test("POST /formulas", False, "No formula ID returned")
            else:
                self.log_test("POST /formulas", False, 
                             "Failed to create formula", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("POST /formulas", False, f"Exception: {str(e)}")
        
        # Test DELETE /formulas/{id}
        if self.created_resources['formulas']:
            try:
                formula_id = self.created_resources['formulas'][0]
                response = self.make_request("DELETE", f"/formulas/{formula_id}")
                if response and response.status_code == 200:
                    self.log_test("DELETE /formulas/{id}", True, 
                                 f"Deleted formula {formula_id}", response.status_code)
                    success_count += 1
                    self.created_resources['formulas'].remove(formula_id)
                else:
                    self.log_test("DELETE /formulas/{id}", False, 
                                 f"Failed to delete formula {formula_id}", 
                                 response.status_code if response else None)
            except Exception as e:
                self.log_test("DELETE /formulas/{id}", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_appointments_crud(self) -> bool:
        """Test appointments CRUD operations"""
        print("\n📅 TESTING APPOINTMENTS CRUD")
        print("-" * 40)
        
        success_count = 0
        total_tests = 3
        
        # Ensure we have a client for the appointment
        client_id = None
        if self.created_resources['clients']:
            client_id = self.created_resources['clients'][0]
        else:
            # Create a temporary client
            client_data = {
                "name": "Appointment Test Client",
                "email": "apptclient@apple.com",
                "phone": "+1-555-0125"
            }
            response = self.make_request("POST", "/clients", client_data)
            if response and response.status_code in [200, 201]:
                client = response.json()
                client_id = client.get("id")
                self.created_resources['clients'].append(client_id)
        
        if not client_id:
            self.log_test("Appointments CRUD", False, "No client available for appointment testing")
            return False
        
        # Test GET /appointments
        try:
            response = self.make_request("GET", "/appointments")
            if response and response.status_code == 200:
                appointments = response.json()
                self.log_test("GET /appointments", True, 
                             f"Retrieved {len(appointments)} appointments", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /appointments", False, 
                             "Failed to get appointments", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /appointments", False, f"Exception: {str(e)}")
        
        # Test POST /appointments
        try:
            # Create appointment for tomorrow
            tomorrow = datetime.now() + timedelta(days=1)
            appointment_data = {
                "client_id": client_id,
                "service": "Apple Test Service",
                "appointment_date": tomorrow.isoformat(),
                "duration_minutes": 120,
                "notes": "Test appointment for Apple Store review"
            }
            
            response = self.make_request("POST", "/appointments", appointment_data)
            if response and response.status_code in [200, 201]:
                appointment = response.json()
                appointment_id = appointment.get("id")
                if appointment_id:
                    self.created_resources['appointments'].append(appointment_id)
                    self.log_test("POST /appointments", True, 
                                 f"Created appointment with ID: {appointment_id}", response.status_code)
                    success_count += 1
                else:
                    self.log_test("POST /appointments", False, "No appointment ID returned")
            else:
                self.log_test("POST /appointments", False, 
                             "Failed to create appointment", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("POST /appointments", False, f"Exception: {str(e)}")
        
        # Test DELETE /appointments/{id}
        if self.created_resources['appointments']:
            try:
                appointment_id = self.created_resources['appointments'][0]
                response = self.make_request("DELETE", f"/appointments/{appointment_id}")
                if response and response.status_code == 200:
                    self.log_test("DELETE /appointments/{id}", True, 
                                 f"Deleted appointment {appointment_id}", response.status_code)
                    success_count += 1
                    self.created_resources['appointments'].remove(appointment_id)
                else:
                    self.log_test("DELETE /appointments/{id}", False, 
                                 f"Failed to delete appointment {appointment_id}", 
                                 response.status_code if response else None)
            except Exception as e:
                self.log_test("DELETE /appointments/{id}", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_posts_feed(self) -> bool:
        """Test posts and feed functionality"""
        print("\n📱 TESTING POSTS/FEED")
        print("-" * 40)
        
        success_count = 0
        total_tests = 3
        
        # Test GET /posts
        try:
            response = self.make_request("GET", "/posts")
            if response and response.status_code == 200:
                posts = response.json()
                self.log_test("GET /posts", True, 
                             f"Retrieved {len(posts)} posts", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /posts", False, 
                             "Failed to get posts", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /posts", False, f"Exception: {str(e)}")
        
        # Test POST /posts
        try:
            # Create a simple base64 test image
            test_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
            
            post_data = {
                "caption": "Apple Store Review Test Post",
                "images": [test_image],
                "tags": ["test", "apple", "review"]
            }
            
            response = self.make_request("POST", "/posts", post_data)
            if response and response.status_code in [200, 201]:
                post = response.json()
                post_id = post.get("id")
                if post_id:
                    self.created_resources['posts'].append(post_id)
                    self.log_test("POST /posts", True, 
                                 f"Created post with ID: {post_id}", response.status_code)
                    success_count += 1
                else:
                    self.log_test("POST /posts", False, "No post ID returned")
            else:
                self.log_test("POST /posts", False, 
                             "Failed to create post", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("POST /posts", False, f"Exception: {str(e)}")
        
        # Test DELETE /posts/{id}
        if self.created_resources['posts']:
            try:
                post_id = self.created_resources['posts'][0]
                response = self.make_request("DELETE", f"/posts/{post_id}")
                if response and response.status_code == 200:
                    self.log_test("DELETE /posts/{id}", True, 
                                 f"Deleted post {post_id}", response.status_code)
                    success_count += 1
                    self.created_resources['posts'].remove(post_id)
                else:
                    self.log_test("DELETE /posts/{id}", False, 
                                 f"Failed to delete post {post_id}", 
                                 response.status_code if response else None)
            except Exception as e:
                self.log_test("DELETE /posts/{id}", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_ai_assistant(self) -> bool:
        """Test AI assistant functionality"""
        print("\n🤖 TESTING AI ASSISTANT")
        print("-" * 40)
        
        try:
            ai_data = {
                "message": "What are the best hair care tips for damaged hair?"
            }
            
            response = self.make_request("POST", "/ai/chat", ai_data)
            if response and response.status_code == 200:
                ai_response = response.json()
                if "response" in ai_response or "message" in ai_response:
                    self.log_test("POST /ai/chat", True, 
                                 f"AI responded successfully", response.status_code)
                    return True
                else:
                    self.log_test("POST /ai/chat", False, 
                                 "AI response missing expected fields")
                    return False
            else:
                self.log_test("POST /ai/chat", False, 
                             "Failed to get AI response", 
                             response.status_code if response else None)
                return False
                
        except Exception as e:
            self.log_test("AI Assistant", False, f"Exception: {str(e)}")
            return False
    
    def test_profiles(self) -> bool:
        """Test profile endpoints"""
        print("\n👤 TESTING PROFILES")
        print("-" * 40)
        
        success_count = 0
        total_tests = 2
        
        # Test GET /profiles/me
        try:
            response = self.make_request("GET", "/profiles/me")
            if response and response.status_code == 200:
                profile = response.json()
                self.log_test("GET /profiles/me", True, 
                             f"Retrieved profile data", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /profiles/me", False, 
                             "Failed to get profile", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /profiles/me", False, f"Exception: {str(e)}")
        
        # Test GET /profiles/discover
        try:
            response = self.make_request("GET", "/profiles/discover")
            if response and response.status_code == 200:
                profiles = response.json()
                self.log_test("GET /profiles/discover", True, 
                             f"Retrieved {len(profiles)} profiles", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /profiles/discover", False, 
                             "Failed to get discover profiles", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /profiles/discover", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_social(self) -> bool:
        """Test social features (following/followers)"""
        print("\n🤝 TESTING SOCIAL")
        print("-" * 40)
        
        success_count = 0
        total_tests = 2
        
        # Test GET /users/following
        try:
            response = self.make_request("GET", "/users/following")
            if response and response.status_code == 200:
                following = response.json()
                self.log_test("GET /users/following", True, 
                             f"Retrieved {len(following)} following", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /users/following", False, 
                             "Failed to get following", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /users/following", False, f"Exception: {str(e)}")
        
        # Test GET /users/followers
        try:
            response = self.make_request("GET", "/users/followers")
            if response and response.status_code == 200:
                followers = response.json()
                self.log_test("GET /users/followers", True, 
                             f"Retrieved {len(followers)} followers", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /users/followers", False, 
                             "Failed to get followers", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /users/followers", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def test_portfolio_gallery(self) -> bool:
        """Test portfolio and gallery endpoints"""
        print("\n🖼️ TESTING PORTFOLIO/GALLERY")
        print("-" * 40)
        
        success_count = 0
        total_tests = 2
        
        # Test GET /portfolio
        try:
            response = self.make_request("GET", "/portfolio")
            if response and response.status_code == 200:
                portfolio = response.json()
                self.log_test("GET /portfolio", True, 
                             f"Retrieved portfolio data", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /portfolio", False, 
                             "Failed to get portfolio", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /portfolio", False, f"Exception: {str(e)}")
        
        # Test GET /gallery
        try:
            response = self.make_request("GET", "/gallery")
            if response and response.status_code == 200:
                gallery = response.json()
                self.log_test("GET /gallery", True, 
                             f"Retrieved {len(gallery)} gallery items", response.status_code)
                success_count += 1
            else:
                self.log_test("GET /gallery", False, 
                             "Failed to get gallery", 
                             response.status_code if response else None)
        except Exception as e:
            self.log_test("GET /gallery", False, f"Exception: {str(e)}")
        
        return success_count == total_tests
    
    def cleanup_resources(self):
        """Clean up any created test resources"""
        print("\n🧹 CLEANING UP TEST RESOURCES")
        print("-" * 40)
        
        # Clean up posts
        for post_id in self.created_resources['posts']:
            try:
                response = self.make_request("DELETE", f"/posts/{post_id}")
                if response and response.status_code == 200:
                    print(f"✅ Cleaned up post {post_id}")
                else:
                    print(f"⚠️ Failed to clean up post {post_id}")
            except:
                print(f"⚠️ Error cleaning up post {post_id}")
        
        # Clean up appointments
        for appointment_id in self.created_resources['appointments']:
            try:
                response = self.make_request("DELETE", f"/appointments/{appointment_id}")
                if response and response.status_code == 200:
                    print(f"✅ Cleaned up appointment {appointment_id}")
                else:
                    print(f"⚠️ Failed to clean up appointment {appointment_id}")
            except:
                print(f"⚠️ Error cleaning up appointment {appointment_id}")
        
        # Clean up formulas
        for formula_id in self.created_resources['formulas']:
            try:
                response = self.make_request("DELETE", f"/formulas/{formula_id}")
                if response and response.status_code == 200:
                    print(f"✅ Cleaned up formula {formula_id}")
                else:
                    print(f"⚠️ Failed to clean up formula {formula_id}")
            except:
                print(f"⚠️ Error cleaning up formula {formula_id}")
        
        # Clean up clients
        for client_id in self.created_resources['clients']:
            try:
                response = self.make_request("DELETE", f"/clients/{client_id}")
                if response and response.status_code == 200:
                    print(f"✅ Cleaned up client {client_id}")
                else:
                    print(f"⚠️ Failed to clean up client {client_id}")
            except:
                print(f"⚠️ Error cleaning up client {client_id}")
    
    def run_all_tests(self) -> bool:
        """Run complete Apple Store verification test suite"""
        print("=" * 80)
        print("🍎 STYLEFLOW - FINAL APPLE STORE VERIFICATION")
        print("=" * 80)
        print(f"Testing API: {BASE_URL}")
        print(f"Apple Tester: {APPLE_TESTER_EMAIL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Track overall success
        test_sections = []
        
        # 1. Authentication (Critical)
        auth_success = self.test_authentication()
        test_sections.append(("Authentication", auth_success))
        
        if not auth_success:
            print("❌ CRITICAL: Authentication failed. Cannot proceed with other tests.")
            return False
        
        # 2. Dashboard
        dashboard_success = self.test_dashboard()
        test_sections.append(("Dashboard", dashboard_success))
        
        # 3. Clients CRUD
        clients_success = self.test_clients_crud()
        test_sections.append(("Clients CRUD", clients_success))
        
        # 4. Formulas CRUD
        formulas_success = self.test_formulas_crud()
        test_sections.append(("Formulas CRUD", formulas_success))
        
        # 5. Appointments CRUD
        appointments_success = self.test_appointments_crud()
        test_sections.append(("Appointments CRUD", appointments_success))
        
        # 6. Posts/Feed
        posts_success = self.test_posts_feed()
        test_sections.append(("Posts/Feed", posts_success))
        
        # 7. AI Assistant
        ai_success = self.test_ai_assistant()
        test_sections.append(("AI Assistant", ai_success))
        
        # 8. Profiles
        profiles_success = self.test_profiles()
        test_sections.append(("Profiles", profiles_success))
        
        # 9. Social
        social_success = self.test_social()
        test_sections.append(("Social", social_success))
        
        # 10. Portfolio/Gallery
        portfolio_success = self.test_portfolio_gallery()
        test_sections.append(("Portfolio/Gallery", portfolio_success))
        
        # Cleanup
        self.cleanup_resources()
        
        # Final Summary
        print("\n" + "=" * 80)
        print("📋 FINAL TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Section summary
        print("📊 SECTION RESULTS:")
        for section_name, section_success in test_sections:
            status = "✅ PASS" if section_success else "❌ FAIL"
            print(f"  {status} {section_name}")
        
        print()
        
        # Failed tests detail
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}")
                if test['details']:
                    print(f"    Details: {test['details']}")
                if test['status_code']:
                    print(f"    Status Code: {test['status_code']}")
            print()
        
        # Final verdict
        critical_sections = ["Authentication", "Dashboard", "Clients CRUD"]
        critical_failures = [name for name, success in test_sections if name in critical_sections and not success]
        
        if critical_failures:
            print(f"🚨 CRITICAL FAILURES: {', '.join(critical_failures)}")
            print("❌ APPLE STORE SUBMISSION NOT READY")
            return False
        elif success_rate >= 90:
            print("🎉 APPLE STORE SUBMISSION READY!")
            print("✅ All critical endpoints working correctly")
            return True
        else:
            print("⚠️ SOME ISSUES FOUND - Review required before submission")
            return False

if __name__ == "__main__":
    tester = StyleFlowAPITest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)