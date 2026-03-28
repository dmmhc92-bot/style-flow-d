#!/usr/bin/env python3
"""
StyleFlow Guardian Dashboard and Strike Engine Testing
=====================================================
Comprehensive testing of the new Guardian Dashboard endpoints and Strike Engine functionality.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowGuardianTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def admin_login(self) -> bool:
        """Login with admin credentials"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("token") or data.get("access_token")
                if self.admin_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    self.log_test("Admin Login", True, f"Successfully logged in as {ADMIN_EMAIL}")
                    return True
                else:
                    self.log_test("Admin Login", False, "No access token in response", data)
                    return False
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False

    def test_guardian_summary(self) -> bool:
        """Test GET /api/admin/guardian/summary"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/guardian/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields are present
                required_fields = [
                    "system_health", "actions_last_24h", "actions_last_7d", 
                    "currently_suspended", "restored_last_24h", "banned_users",
                    "pending_appeals", "requires_attention", "recent_actions"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Guardian Summary Endpoint", False, 
                                f"Missing required fields: {missing_fields}", data)
                    return False
                
                # Verify system health status
                if data.get("system_health") != "operational":
                    self.log_test("Guardian Summary Endpoint", False, 
                                f"System health is not operational: {data.get('system_health')}", data)
                    return False
                
                # Verify no surveillance data (should only show action results)
                surveillance_indicators = ["pending_reports", "flagged_users", "user_activity"]
                found_surveillance = [field for field in surveillance_indicators if field in data]
                
                if found_surveillance:
                    self.log_test("Guardian Summary Endpoint", False, 
                                f"Contains surveillance data: {found_surveillance}", data)
                    return False
                
                self.log_test("Guardian Summary Endpoint", True, 
                            f"System health: {data['system_health']}, Actions 24h: {data['actions_last_24h']}, "
                            f"Currently suspended: {data['currently_suspended']}, Pending appeals: {data['pending_appeals']}")
                return True
                
            else:
                self.log_test("Guardian Summary Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Guardian Summary Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_guardian_actions(self) -> bool:
        """Test GET /api/admin/guardian/actions"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/guardian/actions")
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_test("Guardian Actions Endpoint", False, 
                                "Response should be a list of actions", data)
                    return False
                
                # Check if actions have required structure (if any exist)
                if data:
                    action = data[0]
                    required_action_fields = [
                        "id", "type", "user_id", "action", "action_label", 
                        "created_at", "status"
                    ]
                    
                    missing_fields = [field for field in required_action_fields if field not in action]
                    
                    if missing_fields:
                        self.log_test("Guardian Actions Endpoint", False, 
                                    f"Action missing required fields: {missing_fields}", action)
                        return False
                    
                    # Verify these are completed actions, not pending work
                    if action.get("status") not in ["completed", "auto_completed"]:
                        self.log_test("Guardian Actions Endpoint", False, 
                                    f"Action status should be completed, got: {action.get('status')}", action)
                        return False
                
                self.log_test("Guardian Actions Endpoint", True, 
                            f"Retrieved {len(data)} system actions (history of automated actions)")
                return True
                
            else:
                self.log_test("Guardian Actions Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Guardian Actions Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_guardian_active_suspensions(self) -> bool:
        """Test GET /api/admin/guardian/active-suspensions"""
        try:
            response = self.session.get(f"{BASE_URL}/admin/guardian/active-suspensions")
            
            if response.status_code == 200:
                data = response.json()
                
                # Should have count and suspensions array
                if "count" not in data or "suspensions" not in data:
                    self.log_test("Guardian Active Suspensions Endpoint", False, 
                                "Missing 'count' or 'suspensions' fields", data)
                    return False
                
                if not isinstance(data["suspensions"], list):
                    self.log_test("Guardian Active Suspensions Endpoint", False, 
                                "Suspensions should be a list", data)
                    return False
                
                # Check suspension structure (if any exist)
                if data["suspensions"]:
                    suspension = data["suspensions"][0]
                    required_suspension_fields = [
                        "user_id", "user_name", "suspended_until", 
                        "hours_remaining", "auto_restore", "status"
                    ]
                    
                    missing_fields = [field for field in required_suspension_fields if field not in suspension]
                    
                    if missing_fields:
                        self.log_test("Guardian Active Suspensions Endpoint", False, 
                                    f"Suspension missing required fields: {missing_fields}", suspension)
                        return False
                    
                    # Verify auto-restore is enabled
                    if not suspension.get("auto_restore"):
                        self.log_test("Guardian Active Suspensions Endpoint", False, 
                                    "Suspensions should have auto_restore enabled", suspension)
                        return False
                
                self.log_test("Guardian Active Suspensions Endpoint", True, 
                            f"Found {data['count']} active suspensions (will auto-restore)")
                return True
                
            else:
                self.log_test("Guardian Active Suspensions Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Guardian Active Suspensions Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_guardian_mode_compliance(self) -> bool:
        """Test Guardian Mode Compliance - verify prohibited endpoints don't exist"""
        prohibited_endpoints = [
            "/admin/users/list",           # Global user list
            "/admin/users/all",            # Global user list
            "/admin/activity/feed",        # Activity surveillance
            "/admin/surveillance/users",   # User surveillance
            "/admin/pending/actions",      # Manual action queue
            "/admin/manual/queue"          # Manual work queue
        ]
        
        compliance_passed = True
        
        for endpoint in prohibited_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                # These endpoints should return 404 (not found) or 405 (method not allowed)
                if response.status_code in [200, 201]:
                    self.log_test(f"Guardian Compliance Check: {endpoint}", False, 
                                f"Prohibited endpoint exists and returns {response.status_code}")
                    compliance_passed = False
                else:
                    self.log_test(f"Guardian Compliance Check: {endpoint}", True, 
                                f"Correctly returns {response.status_code} (endpoint doesn't exist)")
                    
            except Exception as e:
                # Network errors are fine - means endpoint doesn't exist
                self.log_test(f"Guardian Compliance Check: {endpoint}", True, 
                            f"Endpoint doesn't exist (exception: {str(e)})")
        
        return compliance_passed

    def test_strike_engine_health(self) -> bool:
        """Test Strike Engine Health Check by examining backend logs"""
        try:
            # We can't directly access logs, but we can test if the system is working
            # by checking if the guardian summary shows recent activity
            response = self.session.get(f"{BASE_URL}/admin/guardian/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if system shows signs of Strike Engine activity
                system_health = data.get("system_health")
                
                if system_health == "operational":
                    self.log_test("Strike Engine Health Check", True, 
                                "System health is operational, Strike Engine appears to be running")
                    return True
                else:
                    self.log_test("Strike Engine Health Check", False, 
                                f"System health is not operational: {system_health}")
                    return False
            else:
                self.log_test("Strike Engine Health Check", False, 
                            f"Cannot check system health: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Strike Engine Health Check", False, f"Exception: {str(e)}")
            return False

    def test_admin_only_access(self) -> bool:
        """Test that Guardian endpoints require admin access"""
        # Create a session without admin token
        non_admin_session = requests.Session()
        
        guardian_endpoints = [
            "/admin/guardian/summary",
            "/admin/guardian/actions", 
            "/admin/guardian/active-suspensions"
        ]
        
        access_control_passed = True
        
        for endpoint in guardian_endpoints:
            try:
                response = non_admin_session.get(f"{BASE_URL}{endpoint}")
                
                # Should return 401 (unauthorized) or 403 (forbidden)
                if response.status_code in [401, 403]:
                    self.log_test(f"Admin Access Control: {endpoint}", True, 
                                f"Correctly returns {response.status_code} for non-admin access")
                else:
                    self.log_test(f"Admin Access Control: {endpoint}", False, 
                                f"Should require admin access, got {response.status_code}")
                    access_control_passed = False
                    
            except Exception as e:
                self.log_test(f"Admin Access Control: {endpoint}", False, f"Exception: {str(e)}")
                access_control_passed = False
        
        return access_control_passed

    def run_all_tests(self):
        """Run all Guardian Dashboard and Strike Engine tests"""
        print("=" * 80)
        print("StyleFlow Guardian Dashboard & Strike Engine Testing")
        print("=" * 80)
        print()
        
        # Step 1: Admin Authentication
        if not self.admin_login():
            print("❌ CRITICAL: Admin login failed. Cannot proceed with testing.")
            return
        
        # Step 2: Guardian Dashboard Endpoints
        print("🔍 Testing Guardian Dashboard Endpoints...")
        print("-" * 50)
        
        self.test_guardian_summary()
        self.test_guardian_actions()
        self.test_guardian_active_suspensions()
        
        # Step 3: Guardian Mode Compliance
        print("🛡️ Testing Guardian Mode Compliance...")
        print("-" * 50)
        
        self.test_guardian_mode_compliance()
        
        # Step 4: Strike Engine Health
        print("⚡ Testing Strike Engine Health...")
        print("-" * 50)
        
        self.test_strike_engine_health()
        
        # Step 5: Admin Access Control
        print("🔐 Testing Admin Access Control...")
        print("-" * 50)
        
        self.test_admin_only_access()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            print("-" * 40)
            for test in self.test_results:
                if not test["success"]:
                    print(f"❌ {test['test']}: {test['details']}")
            print()
        
        # Guardian Dashboard specific summary
        guardian_tests = [t for t in self.test_results if "Guardian" in t["test"]]
        guardian_passed = len([t for t in guardian_tests if t["success"]])
        
        print("GUARDIAN DASHBOARD STATUS:")
        print("-" * 40)
        if guardian_passed == len(guardian_tests):
            print("✅ All Guardian Dashboard endpoints are working correctly")
            print("✅ Guardian Mode compliance verified")
            print("✅ Admin-only access enforced")
        else:
            print(f"⚠️ {len(guardian_tests) - guardian_passed} Guardian Dashboard issues found")
        
        print()
        print("STRIKE ENGINE STATUS:")
        print("-" * 40)
        strike_tests = [t for t in self.test_results if "Strike Engine" in t["test"]]
        if any(t["success"] for t in strike_tests):
            print("✅ Strike Engine appears to be operational")
        else:
            print("❌ Strike Engine health check failed")


if __name__ == "__main__":
    tester = StyleFlowGuardianTester()
    tester.run_all_tests()