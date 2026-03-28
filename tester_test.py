#!/usr/bin/env python3
"""
TESTER ACCOUNT AUTO-POPULATION TEST
===================================
Testing that tester accounts automatically get demo portfolio items populated.
"""

import requests
import json

# Backend URL
BACKEND_URL = "https://hairflow-app-1.preview.emergentagent.com/api"

# Tester credentials
TESTER_EMAIL = "review@styleflow.com"
TESTER_PASSWORD = "TestPass123!"

def test_tester_auto_population():
    """Test tester account auto-population"""
    session = requests.Session()
    
    print("🧪 TESTING TESTER ACCOUNT AUTO-POPULATION...")
    print()
    
    # Login with tester account
    print("🔐 Logging in with tester account...")
    response = session.post(f"{BACKEND_URL}/auth/login", json={
        "email": TESTER_EMAIL,
        "password": TESTER_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    token = data.get("token")
    user_data = data.get("user", {})
    
    print(f"✅ Login successful")
    print(f"   User ID: {user_data.get('id')}")
    print(f"   Is Tester: {user_data.get('is_tester')}")
    print(f"   Is Admin: {user_data.get('is_admin')}")
    print()
    
    # Set authorization header
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Test the profile endpoint that should trigger auto-population
    print("📋 Getting profile to trigger auto-population...")
    response = session.get(f"{BACKEND_URL}/profiles/me/hub")
    
    if response.status_code != 200:
        print(f"❌ Profile request failed: {response.status_code} - {response.text}")
        return False
    
    profile_data = response.json()
    portfolio = profile_data.get("portfolio", [])
    
    print(f"✅ Profile retrieved successfully")
    print(f"   Portfolio items: {len(portfolio)}")
    print()
    
    if len(portfolio) > 0:
        print("🎉 TESTER AUTO-POPULATION WORKING!")
        print(f"   Found {len(portfolio)} demo portfolio items")
        print()
        
        # Show first few items
        for i, item in enumerate(portfolio[:3]):
            print(f"   Item {i+1}:")
            print(f"     Caption: {item.get('caption', 'No caption')}")
            print(f"     Image URL: {item.get('image', 'No image')[:50]}...")
            print()
        
        # Verify structure
        first_item = portfolio[0]
        required_fields = ["id", "image", "caption", "created_at"]
        missing_fields = [field for field in required_fields if field not in first_item]
        
        if not missing_fields:
            print("✅ Portfolio item structure is correct")
        else:
            print(f"⚠️  Portfolio item missing fields: {missing_fields}")
        
        return True
    else:
        print("❌ TESTER AUTO-POPULATION NOT WORKING")
        print("   No demo portfolio items found")
        return False

if __name__ == "__main__":
    success = test_tester_auto_population()
    
    if success:
        print("\n🎉 TESTER AUTO-POPULATION TEST PASSED!")
    else:
        print("\n❌ TESTER AUTO-POPULATION TEST FAILED!")