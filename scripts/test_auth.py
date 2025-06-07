#!/usr/bin/env python3
"""
Quick test script to verify authentication is working
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_login():
    """Test login with sample user"""
    login_data = {
        "username": "john_dev",
        "password": "Demo123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print(f"✅ Login successful for john_dev")
            print(f"Token: {token[:20]}...")
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            logs_response = requests.get(f"{BASE_URL}/logs", headers=headers)
            
            if logs_response.status_code == 200:
                logs = logs_response.json()
                print(f"✅ Protected endpoint working - found {len(logs)} logs")
                return True
            else:
                print(f"❌ Protected endpoint failed: {logs_response.status_code}")
                return False
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_login()