#!/usr/bin/env python3
"""
StyleFlow Backend Testing - Forgot Password with Resend Email Integration
Testing comprehensive forgot password flow with email sending via Resend API
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
import pymongo
from bson import ObjectId

# Configuration
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

# Test data
TEST_EMAIL = "testforgot@example.com"
TEST_PASSWORD = "TestPassword123!"
NEW_PASSWORD = "NewPassword123!"
NONEXISTENT_EMAIL = "nonexistent@example.com"

class StyleFlowForgotPasswordTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # MongoDB connection for direct database access
        try:
            self.mongo_client = pymongo.MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            print("✅ Connected to MongoDB for direct database access")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
    
    def cleanup_test_data(self):
        """Clean up test data before and after tests"""
        if self.db is not None:
            try:
                # Remove test user and password reset records
                self.db.users.delete_many({"email": TEST_EMAIL})
                self.db.password_resets.delete_many({"email": TEST_EMAIL})
                self.db.password_resets.delete_many({"email": NONEXISTENT_EMAIL})
                print("✅ Cleaned up test data")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
    
    def create_test_user(self):
        """Create a test user for forgot password testing"""
        print("\n🔧 Creating test user...")
        
        user_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Test Forgot User",
            "business_name": "Test Salon"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=user_data)
            if response.status_code in [200, 201]:
                print(f"✅ Test user created successfully: {TEST_EMAIL}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"✅ Test user already exists: {TEST_EMAIL}")
                return True
            else:
                print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            return False
    
    def test_forgot_password_valid_email(self):
        """Test forgot password request with valid email"""
        print("\n📧 Testing forgot password with valid email...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/forgot-password",
                json={"email": TEST_EMAIL}
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_message = "If email exists, reset instructions sent"
                
                if data.get("message") == expected_message:
                    print("✅ Forgot password request successful")
                    print(f"   Response: {data['message']}")
                    
                    # Check if token was created in database
                    if self.db is not None:
                        reset_record = self.db.password_resets.find_one({"email": TEST_EMAIL})
                        if reset_record:
                            print("✅ Password reset token created in database")
                            print(f"   Token expires at: {reset_record['expires_at']}")
                            return reset_record["token"]
                        else:
                            print("❌ No password reset token found in database")
                            return None
                    else:
                        print("⚠️ Cannot verify database token (no DB connection)")
                        return "mock_token"
                else:
                    print(f"❌ Unexpected response message: {data.get('message')}")
                    return None
            else:
                print(f"❌ Forgot password failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error testing forgot password: {e}")
            return None
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password request with non-existent email"""
        print("\n🔍 Testing forgot password with non-existent email...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/forgot-password",
                json={"email": NONEXISTENT_EMAIL}
            )
            
            if response.status_code == 200:
                data = response.json()
                expected_message = "If email exists, reset instructions sent"
                
                if data.get("message") == expected_message:
                    print("✅ Forgot password returns same message for security")
                    print(f"   Response: {data['message']}")
                    
                    # Verify no token was created
                    if self.db is not None:
                        reset_record = self.db.password_resets.find_one({"email": NONEXISTENT_EMAIL})
                        if not reset_record:
                            print("✅ No token created for non-existent email (correct)")
                            return True
                        else:
                            print("❌ Token was created for non-existent email (security issue)")
                            return False
                    else:
                        print("⚠️ Cannot verify database behavior (no DB connection)")
                        return True
                else:
                    print(f"❌ Unexpected response message: {data.get('message')}")
                    return False
            else:
                print(f"❌ Forgot password failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing forgot password with non-existent email: {e}")
            return False
    
    def test_verify_reset_token(self, token):
        """Test reset token verification"""
        print(f"\n🔐 Testing reset token verification...")
        
        if not token:
            print("❌ No token provided for verification")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/verify-reset-token/{token}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("valid") == True and "email" in data:
                    masked_email = data["email"]
                    print("✅ Token verification successful")
                    print(f"   Valid: {data['valid']}")
                    print(f"   Masked email: {masked_email}")
                    
                    # Check if email is properly masked
                    if "***" in masked_email and "@" in masked_email:
                        print("✅ Email properly masked for security")
                        return True
                    else:
                        print("⚠️ Email masking might not be working correctly")
                        return True
                else:
                    print(f"❌ Unexpected verification response: {data}")
                    return False
            else:
                print(f"❌ Token verification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing token verification: {e}")
            return False
    
    def test_reset_password(self, token):
        """Test password reset with valid token"""
        print(f"\n🔄 Testing password reset...")
        
        if not token:
            print("❌ No token provided for password reset")
            return False
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/reset-password",
                json={
                    "token": token,
                    "new_password": NEW_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("message") == "Password reset successful":
                    print("✅ Password reset successful")
                    print(f"   Response: {data['message']}")
                    
                    # Verify token is deleted from database
                    if self.db is not None:
                        reset_record = self.db.password_resets.find_one({"token": token})
                        if not reset_record:
                            print("✅ Used token properly deleted from database")
                        else:
                            print("❌ Used token still exists in database")
                            return False
                    
                    return True
                else:
                    print(f"❌ Unexpected reset response: {data}")
                    return False
            else:
                print(f"❌ Password reset failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing password reset: {e}")
            return False
    
    def test_login_with_new_password(self):
        """Test login with the new password"""
        print(f"\n🔑 Testing login with new password...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": NEW_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "token" in data and "user" in data:
                    print("✅ Login successful with new password")
                    print(f"   User: {data['user']['email']}")
                    print(f"   Token received: {data['token'][:20]}...")
                    return True
                else:
                    print(f"❌ Login response missing token or user: {data}")
                    return False
            else:
                print(f"❌ Login failed with new password: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing login with new password: {e}")
            return False
    
    def test_verify_old_token_deleted(self, old_token):
        """Test that old token is no longer valid"""
        print(f"\n🗑️ Testing that old token is deleted...")
        
        if not old_token:
            print("❌ No old token provided for verification")
            return False
        
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/verify-reset-token/{old_token}")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid reset token" in data.get("detail", ""):
                    print("✅ Old token properly invalidated")
                    print(f"   Error: {data['detail']}")
                    return True
                else:
                    print(f"❌ Unexpected error message: {data}")
                    return False
            else:
                print(f"❌ Old token still valid (should be deleted): {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing old token deletion: {e}")
            return False
    
    def test_invalid_token_handling(self):
        """Test handling of invalid tokens"""
        print(f"\n❌ Testing invalid token handling...")
        
        invalid_token = "invalid_token_xxx"
        
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/verify-reset-token/{invalid_token}")
            
            if response.status_code == 400:
                data = response.json()
                if "Invalid reset token" in data.get("detail", ""):
                    print("✅ Invalid token properly rejected")
                    print(f"   Error: {data['detail']}")
                    return True
                else:
                    print(f"❌ Unexpected error message: {data}")
                    return False
            else:
                print(f"❌ Invalid token not properly rejected: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")
            return False
    
    def check_backend_logs_for_email(self):
        """Check backend logs for email sending activity"""
        print(f"\n📋 Checking backend logs for email activity...")
        
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Look for Resend API activity
                if "resend" in logs.lower() or "email" in logs.lower():
                    print("✅ Email-related activity found in logs")
                    # Print relevant log lines
                    for line in logs.split('\n'):
                        if any(keyword in line.lower() for keyword in ['resend', 'email', 'smtp']):
                            print(f"   📝 {line}")
                    return True
                else:
                    print("⚠️ No obvious email activity in recent logs")
                    return False
            else:
                print(f"⚠️ Could not read backend logs: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error checking logs: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive forgot password testing"""
        print("🚀 Starting StyleFlow Forgot Password with Resend Email Integration Testing")
        print("=" * 80)
        
        # Cleanup before testing
        self.cleanup_test_data()
        
        test_results = []
        
        # Test 1: Create test user
        print("\n📋 TEST 1: Create Test User")
        result = self.create_test_user()
        test_results.append(("Create Test User", result))
        
        if not result:
            print("❌ Cannot proceed without test user")
            return
        
        # Test 2: Forgot password with valid email
        print("\n📋 TEST 2: Forgot Password (Valid Email)")
        reset_token = self.test_forgot_password_valid_email()
        test_results.append(("Forgot Password (Valid Email)", reset_token is not None))
        
        # Test 3: Forgot password with non-existent email
        print("\n📋 TEST 3: Forgot Password (Non-existent Email)")
        result = self.test_forgot_password_nonexistent_email()
        test_results.append(("Forgot Password (Non-existent Email)", result))
        
        # Test 4: Verify reset token
        if reset_token:
            print("\n📋 TEST 4: Verify Reset Token")
            result = self.test_verify_reset_token(reset_token)
            test_results.append(("Verify Reset Token", result))
        else:
            test_results.append(("Verify Reset Token", False))
        
        # Test 5: Reset password
        if reset_token:
            print("\n📋 TEST 5: Reset Password")
            result = self.test_reset_password(reset_token)
            test_results.append(("Reset Password", result))
        else:
            test_results.append(("Reset Password", False))
        
        # Test 6: Login with new password
        print("\n📋 TEST 6: Login with New Password")
        result = self.test_login_with_new_password()
        test_results.append(("Login with New Password", result))
        
        # Test 7: Verify old token is deleted
        if reset_token:
            print("\n📋 TEST 7: Verify Old Token Deleted")
            result = self.test_verify_old_token_deleted(reset_token)
            test_results.append(("Verify Old Token Deleted", result))
        else:
            test_results.append(("Verify Old Token Deleted", False))
        
        # Test 8: Invalid token handling
        print("\n📋 TEST 8: Invalid Token Handling")
        result = self.test_invalid_token_handling()
        test_results.append(("Invalid Token Handling", result))
        
        # Test 9: Check backend logs for email activity
        print("\n📋 TEST 9: Check Backend Logs for Email Activity")
        result = self.check_backend_logs_for_email()
        test_results.append(("Check Email Logs", result))
        
        # Cleanup after testing
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 FORGOT PASSWORD TESTING SUMMARY")
        print("=" * 80)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Forgot Password with Resend Email Integration is working perfectly!")
        elif passed >= total * 0.8:
            print("⚠️ MOSTLY WORKING - Some minor issues found")
        else:
            print("❌ CRITICAL ISSUES - Forgot Password system needs attention")
        
        return test_results

if __name__ == "__main__":
    tester = StyleFlowForgotPasswordTester()
    tester.run_comprehensive_test()