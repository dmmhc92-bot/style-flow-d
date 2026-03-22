#!/usr/bin/env python3
"""
StyleFlow Backend Testing Suite - User Appeal System
Testing all appeal endpoints and complete workflow
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@styleflow.com"
ADMIN_PASSWORD = "Admin1234!"

class StyleFlowTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.test_user_token = None
        self.test_user_id = None
        self.test_user_email = None
        self.appeal_id = None
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed: {e}")
            return None
    
    def setup_admin_auth(self):
        """Authenticate as admin"""
        self.log("🔐 Setting up admin authentication...")
        
        response = self.make_request("POST", "/auth/login", {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("token")  # Changed from access_token to token
            self.log("✅ Admin authentication successful")
            return True
        else:
            self.log(f"❌ Admin authentication failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
    
    def create_test_user(self):
        """Create a test user for appeal testing"""
        self.log("👤 Creating test user...")
        
        # Generate unique email
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"testuser_{unique_id}@styleflow.com"
        
        response = self.make_request("POST", "/auth/signup", {
            "email": self.test_user_email,
            "password": "TestPass123!",
            "full_name": "Test User Appeal",
            "business_name": "Test Salon"
        })
        
        if response and response.status_code == 200:  # Changed from 201 to 200
            data = response.json()
            self.test_user_token = data.get("token")  # Changed from access_token to token
            
            # Get user ID by calling /auth/me endpoint
            me_response = self.make_request("GET", "/auth/me", token=self.test_user_token)
            if me_response and me_response.status_code == 200:
                user_data = me_response.json()
                self.test_user_id = user_data.get("id")
                self.log(f"✅ Test user created: {self.test_user_email} (ID: {self.test_user_id})")
                return True
            else:
                self.log("❌ Could not get user ID after signup")
                return False
        else:
            self.log(f"❌ Test user creation failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
    
    def suspend_test_user(self):
        """Suspend the test user to enable appeal testing"""
        self.log("⚠️ Suspending test user for appeal testing...")
        
        # First, create a report against the user (required for moderation action)
        report_response = self.make_request("POST", "/report", {
            "reported_user_id": self.test_user_id,
            "content_type": "profile",
            "reason": "spam",
            "details": "Testing appeal system - creating report for moderation"
        }, token=self.admin_token)
        
        if not (report_response and report_response.status_code == 201):
            self.log(f"❌ Could not create report: {report_response.status_code if report_response else 'No response'}")
            if report_response:
                self.log(f"Response: {report_response.text}")
            return False
        
        self.log("✅ Report created successfully")
        
        # Now use admin moderation endpoint to suspend user
        response = self.make_request("POST", f"/admin/moderation/action/user/{self.test_user_id}", {
            "action": "suspend",
            "reason": "Testing appeal system - automated suspension",
            "duration_hours": 24
        }, token=self.admin_token)
        
        if response and response.status_code == 200:
            self.log("✅ Test user suspended successfully")
            return True
        else:
            self.log(f"❌ User suspension failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
    
    def test_appeal_submission_validation(self):
        """Test appeal submission validation rules"""
        self.log("\n🧪 Testing Appeal Submission Validation...")
        
        # Test 1: Submit appeal without moderation action (should fail)
        self.log("Test 1: Appeal without moderation action")
        
        # Create a clean user for this test
        clean_email = f"clean_{str(uuid.uuid4())[:8]}@styleflow.com"
        clean_response = self.make_request("POST", "/auth/signup", {
            "email": clean_email,
            "password": "TestPass123!",
            "full_name": "Clean User",
            "business_name": "Clean Salon"
        })
        
        if clean_response and clean_response.status_code == 200:  # Changed from 201 to 200
            clean_token = clean_response.json().get("token")  # Changed from access_token to token
            
            # Try to submit appeal without moderation action
            response = self.make_request("POST", "/appeals", {
                "reason": "I did nothing wrong",
                "additional_details": "This is a test appeal"
            }, token=clean_token)
            
            if response and response.status_code == 400:
                self.log("✅ Correctly rejected appeal without moderation action")
            else:
                self.log(f"❌ Should reject appeal without moderation action: {response.status_code if response else 'No response'}")
        
        # Test 2: Submit valid appeal with suspended user
        self.log("Test 2: Valid appeal submission")
        response = self.make_request("POST", "/appeals", {
            "reason": "I believe this suspension was unfair and I would like to appeal",
            "additional_details": "I was following all community guidelines and this seems like a mistake"
        }, token=self.test_user_token)
        
        if response and response.status_code == 201:
            data = response.json()
            self.appeal_id = data.get("appeal_id")
            self.log(f"✅ Appeal submitted successfully: {self.appeal_id}")
        else:
            self.log(f"❌ Appeal submission failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        # Test 3: Try to submit duplicate appeal (should fail)
        self.log("Test 3: Duplicate appeal submission")
        response = self.make_request("POST", "/appeals", {
            "reason": "Another appeal",
            "additional_details": "This should be rejected"
        }, token=self.test_user_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected duplicate appeal")
        else:
            self.log(f"❌ Should reject duplicate appeal: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_user_appeal_status(self):
        """Test user appeal status endpoint"""
        self.log("\n🧪 Testing User Appeal Status...")
        
        # Test appeal status for user with appeal
        response = self.make_request("GET", "/appeals/me", token=self.test_user_token)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("has_appeal") and data.get("appeal", {}).get("id") == self.appeal_id:
                self.log("✅ User appeal status returned correctly")
                self.log(f"   Appeal ID: {data['appeal']['id']}")
                self.log(f"   Status: {data['appeal']['status']}")
                self.log(f"   Reason: {data['appeal']['appeal_reason']}")
            else:
                self.log(f"❌ Appeal status data incorrect: {data}")
                return False
        else:
            self.log(f"❌ Appeal status check failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test appeal status for user without appeal
        clean_email = f"noappeals_{str(uuid.uuid4())[:8]}@styleflow.com"
        clean_response = self.make_request("POST", "/auth/signup", {
            "email": clean_email,
            "password": "TestPass123!",
            "full_name": "No Appeals User",
            "business_name": "No Appeals Salon"
        })
        
        if clean_response and clean_response.status_code == 200:  # Changed from 201 to 200
            clean_token = clean_response.json().get("token")  # Changed from access_token to token
            
            response = self.make_request("GET", "/appeals/me", token=clean_token)
            if response and response.status_code == 200:
                data = response.json()
                if not data.get("has_appeal"):
                    self.log("✅ Correctly returned no appeal for clean user")
                else:
                    self.log(f"❌ Should return no appeal for clean user: {data}")
            else:
                self.log(f"❌ Appeal status check failed for clean user: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_admin_appeals_queue(self):
        """Test admin appeals queue endpoint"""
        self.log("\n🧪 Testing Admin Appeals Queue...")
        
        # Test getting all appeals
        response = self.make_request("GET", "/admin/appeals", token=self.admin_token)
        
        if response and response.status_code == 200:
            appeals = response.json()  # The response is directly a list, not wrapped in {"appeals": [...]}
            
            # Find our test appeal
            test_appeal = None
            for appeal in appeals:
                if appeal.get("id") == self.appeal_id:
                    test_appeal = appeal
                    break
            
            if test_appeal:
                self.log("✅ Admin appeals queue working correctly")
                self.log(f"   Found test appeal: {test_appeal['id']}")
                self.log(f"   User: {test_appeal['user']['name']} ({test_appeal['user']['email']})")
                self.log(f"   Status: {test_appeal['status']}")
                self.log(f"   Reason: {test_appeal['appeal_reason']}")
            else:
                self.log(f"❌ Test appeal not found in queue: {appeals}")
                return False
        else:
            self.log(f"❌ Admin appeals queue failed: {response.status_code if response else 'No response'}")
            return False
        
        # Test filtering by status
        response = self.make_request("GET", "/admin/appeals", 
                                   params={"status": "pending"}, 
                                   token=self.admin_token)
        
        if response and response.status_code == 200:
            appeals = response.json()  # Direct list response
            
            # All appeals should be pending
            all_pending = all(appeal.get("status") == "pending" for appeal in appeals)
            if all_pending:
                self.log("✅ Status filtering working correctly")
            else:
                self.log(f"❌ Status filtering failed - found non-pending appeals: {appeals}")
        else:
            self.log(f"❌ Status filtering failed: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_admin_appeals_stats(self):
        """Test admin appeals statistics endpoint"""
        self.log("\n🧪 Testing Admin Appeals Statistics...")
        
        response = self.make_request("GET", "/admin/appeals/stats", token=self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            
            required_fields = ["pending", "under_review", "approved", "denied"]
            if all(field in data for field in required_fields):
                self.log("✅ Appeals statistics working correctly")
                self.log(f"   Pending: {data['pending']}")
                self.log(f"   Under Review: {data['under_review']}")
                self.log(f"   Approved: {data['approved']}")
                self.log(f"   Denied: {data['denied']}")
                
                # Should have at least 1 pending (our test appeal)
                if data["pending"] >= 1:
                    self.log("✅ Pending count includes our test appeal")
                else:
                    self.log("❌ Pending count should include our test appeal")
            else:
                self.log(f"❌ Missing required fields in stats: {data}")
                return False
        else:
            self.log(f"❌ Appeals statistics failed: {response.status_code if response else 'No response'}")
            return False
        
        return True
    
    def test_admin_mark_under_review(self):
        """Test marking appeal as under review"""
        self.log("\n🧪 Testing Mark Appeal Under Review...")
        
        response = self.make_request("PATCH", f"/admin/appeals/{self.appeal_id}/review", 
                                   token=self.admin_token)
        
        if response and response.status_code == 200:
            self.log("✅ Appeal marked as under review successfully")
            
            # Verify status changed
            status_response = self.make_request("GET", "/appeals/me", token=self.test_user_token)
            if status_response and status_response.status_code == 200:
                data = status_response.json()
                if data.get("appeal", {}).get("status") == "under_review":
                    self.log("✅ Appeal status correctly updated to under_review")
                else:
                    self.log(f"❌ Appeal status not updated: {data}")
            else:
                self.log("❌ Could not verify status update")
        else:
            self.log(f"❌ Mark under review failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        return True
    
    def test_admin_approve_appeal(self):
        """Test approving an appeal"""
        self.log("\n🧪 Testing Appeal Approval...")
        
        response = self.make_request("POST", f"/admin/appeals/{self.appeal_id}/action", {
            "action": "approve",
            "admin_notes": "Appeal approved - suspension was indeed unfair"
        }, token=self.admin_token)
        
        if response and response.status_code == 200:
            data = response.json()
            self.log("✅ Appeal approved successfully")
            self.log(f"   Message: {data.get('message')}")
            
            # Verify user status was restored
            # Get user profile to check moderation status
            profile_response = self.make_request("GET", "/auth/me", token=self.test_user_token)
            if profile_response and profile_response.status_code == 200:
                user_data = profile_response.json()
                moderation_status = user_data.get("moderation_status")
                final_warning = user_data.get("final_warning")
                
                if moderation_status == "good_standing" and final_warning:
                    self.log("✅ User correctly restored to good_standing with final_warning")
                else:
                    self.log(f"❌ User status not correctly restored: status={moderation_status}, final_warning={final_warning}")
            else:
                self.log("❌ Could not verify user status restoration")
            
            # Verify appeal status
            appeal_response = self.make_request("GET", "/appeals/me", token=self.test_user_token)
            if appeal_response and appeal_response.status_code == 200:
                appeal_data = appeal_response.json()
                if appeal_data.get("appeal", {}).get("status") == "approved":
                    self.log("✅ Appeal status correctly updated to approved")
                else:
                    self.log(f"❌ Appeal status not updated: {appeal_data}")
        else:
            self.log(f"❌ Appeal approval failed: {response.status_code if response else 'No response'}")
            if response:
                self.log(f"Response: {response.text}")
            return False
        
        return True
    
    def test_appeal_already_processed(self):
        """Test that processed appeals cannot be processed again"""
        self.log("\n🧪 Testing Already Processed Appeal...")
        
        response = self.make_request("POST", f"/admin/appeals/{self.appeal_id}/action", {
            "action": "deny",
            "admin_notes": "This should fail"
        }, token=self.admin_token)
        
        if response and response.status_code == 400:
            self.log("✅ Correctly rejected processing already processed appeal")
        else:
            self.log(f"❌ Should reject processing already processed appeal: {response.status_code if response else 'No response'}")
            return False
        
        return True
    
    def test_banned_user_appeal_flow(self):
        """Test appeal flow for banned user"""
        self.log("\n🧪 Testing Banned User Appeal Flow...")
        
        # Create another test user
        banned_email = f"banned_{str(uuid.uuid4())[:8]}@styleflow.com"
        banned_response = self.make_request("POST", "/auth/signup", {
            "email": banned_email,
            "password": "TestPass123!",
            "full_name": "Banned User",
            "business_name": "Banned Salon"
        })
        
        if not (banned_response and banned_response.status_code == 200):  # Changed from 201 to 200
            self.log("❌ Could not create banned user for testing")
            return False
        
        banned_data = banned_response.json()
        banned_token = banned_data.get("token")  # Changed from access_token to token
        
        # Get user ID by calling /auth/me endpoint
        me_response = self.make_request("GET", "/auth/me", token=banned_token)
        if me_response and me_response.status_code == 200:
            user_data = me_response.json()
            banned_user_id = user_data.get("id")
        else:
            self.log("❌ Could not get banned user ID")
            return False
        
        # Create a report first, then ban the user
        report_response = self.make_request("POST", "/report", {
            "reported_user_id": banned_user_id,
            "content_type": "profile",
            "reason": "spam",
            "details": "Testing banned user appeal flow"
        }, token=self.admin_token)
        
        if not (report_response and report_response.status_code == 201):
            self.log("❌ Could not create report for banned user")
            return False
        
        # Ban the user
        ban_response = self.make_request("POST", f"/admin/moderation/action/user/{banned_user_id}", {
            "action": "ban",
            "reason": "Testing banned user appeal flow"
        }, token=self.admin_token)
        
        if not (ban_response and ban_response.status_code == 200):
            self.log("❌ Could not ban user for testing")
            return False
        
        self.log("✅ User banned successfully")
        
        # Submit appeal as banned user
        appeal_response = self.make_request("POST", "/appeals", {
            "reason": "I believe this ban was unfair",
            "additional_details": "Testing banned user appeal restoration"
        }, token=banned_token)
        
        if not (appeal_response and appeal_response.status_code == 201):
            self.log("❌ Banned user could not submit appeal")
            return False
        
        banned_appeal_id = appeal_response.json().get("appeal_id")
        self.log(f"✅ Banned user appeal submitted: {banned_appeal_id}")
        
        # Approve the appeal
        approve_response = self.make_request("POST", f"/admin/appeals/{banned_appeal_id}/action", {
            "action": "approve",
            "admin_notes": "Ban appeal approved for testing"
        }, token=self.admin_token)
        
        if not (approve_response and approve_response.status_code == 200):
            self.log("❌ Could not approve banned user appeal")
            return False
        
        # Verify user restored to "warned" status with final_warning
        profile_response = self.make_request("GET", "/auth/me", token=banned_token)
        if profile_response and profile_response.status_code == 200:
            user_data = profile_response.json()
            moderation_status = user_data.get("moderation_status")
            final_warning = user_data.get("final_warning")
            
            if moderation_status == "warned" and final_warning:
                self.log("✅ Banned user correctly restored to warned status with final_warning")
            else:
                self.log(f"❌ Banned user not correctly restored: status={moderation_status}, final_warning={final_warning}")
                return False
        else:
            self.log("❌ Could not verify banned user restoration")
            return False
        
        return True
    
    def test_appeal_denial_flow(self):
        """Test appeal denial flow"""
        self.log("\n🧪 Testing Appeal Denial Flow...")
        
        # Create another test user and suspend them
        denied_email = f"denied_{str(uuid.uuid4())[:8]}@styleflow.com"
        denied_response = self.make_request("POST", "/auth/signup", {
            "email": denied_email,
            "password": "TestPass123!",
            "full_name": "Denied User",
            "business_name": "Denied Salon"
        })
        
        if not (denied_response and denied_response.status_code == 200):  # Changed from 201 to 200
            self.log("❌ Could not create user for denial testing")
            return False
        
        denied_data = denied_response.json()
        denied_token = denied_data.get("token")  # Changed from access_token to token
        
        # Get user ID by calling /auth/me endpoint
        me_response = self.make_request("GET", "/auth/me", token=denied_token)
        if me_response and me_response.status_code == 200:
            user_data = me_response.json()
            denied_user_id = user_data.get("id")
        else:
            self.log("❌ Could not get denied user ID")
            return False
        
        # Create a report first, then suspend the user
        report_response = self.make_request("POST", "/report", {
            "reported_user_id": denied_user_id,
            "content_type": "profile",
            "reason": "spam",
            "details": "Testing appeal denial flow"
        }, token=self.admin_token)
        
        if not (report_response and report_response.status_code == 201):
            self.log("❌ Could not create report for denied user")
            return False
        
        # Suspend the user
        suspend_response = self.make_request("POST", f"/admin/moderation/action/user/{denied_user_id}", {
            "action": "suspend",
            "reason": "Testing appeal denial flow",
            "duration_hours": 24
        }, token=self.admin_token)
        
        if not (suspend_response and suspend_response.status_code == 200):
            self.log("❌ Could not suspend user for denial testing")
            return False
        
        # Submit appeal
        appeal_response = self.make_request("POST", "/appeals", {
            "reason": "This suspension is unfair",
            "additional_details": "Testing denial flow"
        }, token=denied_token)
        
        if not (appeal_response and appeal_response.status_code == 201):
            self.log("❌ Could not submit appeal for denial testing")
            return False
        
        denied_appeal_id = appeal_response.json().get("appeal_id")
        
        # Deny the appeal
        deny_response = self.make_request("POST", f"/admin/appeals/{denied_appeal_id}/action", {
            "action": "deny",
            "admin_notes": "Appeal denied - suspension was justified"
        }, token=self.admin_token)
        
        if not (deny_response and deny_response.status_code == 200):
            self.log("❌ Could not deny appeal")
            return False
        
        self.log("✅ Appeal denied successfully")
        
        # Verify user status unchanged (still suspended)
        profile_response = self.make_request("GET", "/auth/me", token=denied_token)
        if profile_response and profile_response.status_code == 200:
            user_data = profile_response.json()
            moderation_status = user_data.get("moderation_status")
            
            if moderation_status == "suspended":
                self.log("✅ User status correctly unchanged after denial")
            else:
                self.log(f"❌ User status should remain suspended: {moderation_status}")
                return False
        else:
            self.log("❌ Could not verify user status after denial")
            return False
        
        # Verify appeal status
        appeal_status_response = self.make_request("GET", "/appeals/me", token=denied_token)
        if appeal_status_response and appeal_status_response.status_code == 200:
            appeal_data = appeal_status_response.json()
            if appeal_data.get("appeal", {}).get("status") == "denied":
                self.log("✅ Appeal status correctly updated to denied")
            else:
                self.log(f"❌ Appeal status not updated to denied: {appeal_data}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all appeal system tests"""
        self.log("🚀 Starting StyleFlow User Appeal System Testing...")
        self.log(f"Backend URL: {self.base_url}")
        
        tests = [
            ("Admin Authentication", self.setup_admin_auth),
            ("Test User Creation", self.create_test_user),
            ("User Suspension", self.suspend_test_user),
            ("Appeal Submission Validation", self.test_appeal_submission_validation),
            ("User Appeal Status", self.test_user_appeal_status),
            ("Admin Appeals Queue", self.test_admin_appeals_queue),
            ("Admin Appeals Statistics", self.test_admin_appeals_stats),
            ("Mark Appeal Under Review", self.test_admin_mark_under_review),
            ("Appeal Approval", self.test_admin_approve_appeal),
            ("Already Processed Appeal", self.test_appeal_already_processed),
            ("Banned User Appeal Flow", self.test_banned_user_appeal_flow),
            ("Appeal Denial Flow", self.test_appeal_denial_flow),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*60}")
            self.log(f"Running: {test_name}")
            self.log('='*60)
            
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} FAILED with exception: {e}")
        
        # Final Results
        self.log(f"\n{'='*60}")
        self.log("🏁 FINAL RESULTS")
        self.log('='*60)
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! User Appeal System is working perfectly!")
        else:
            self.log(f"⚠️ {failed} test(s) failed. Please review the issues above.")
        
        return failed == 0

if __name__ == "__main__":
    tester = StyleFlowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)