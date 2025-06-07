import requests
import unittest
import json
import random
import string
from datetime import datetime
import sys

class DeveloperRegistrationTester(unittest.TestCase):
    """Test suite for Developer Registration and Role Assignment"""
    
    def setUp(self):
        """Set up test data for each test"""
        self.base_url = "https://3b89f303-b6c0-4d98-84c7-7a8ab55f134a.preview.emergentagent.com/api"
        
        # Generate unique username and email to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        unique_username = f"test_developer_{timestamp}_{random_suffix}"
        unique_email = f"test_{timestamp}_{random_suffix}@test.com"
        
        # Test user data
        self.test_user = {
            "username": unique_username,
            "email": unique_email,
            "password": "TestPass123!",
            "role": "developer",
            "manager_id": ""  # Can be left empty as per requirements
        }
        
    def test_01_register_developer(self):
        """Test registering a new developer user with role 'developer'"""
        print("\n🔍 Testing developer registration...")
        
        # Register the developer user
        response = requests.post(f"{self.base_url}/auth/register", json=self.test_user)
        
        # Check if registration was successful
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        
        # Parse the response
        data = response.json()
        
        # Verify the response structure
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        self.assertIn("user", data, "User data not found in response")
        
        # Verify user data
        user = data["user"]
        self.assertEqual(user["username"], self.test_user["username"], "Username mismatch")
        self.assertEqual(user["email"], self.test_user["email"], "Email mismatch")
        self.assertEqual(user["role"], "developer", "Role mismatch - expected 'developer'")
        
        # Store token for login test
        self.access_token = data["access_token"]
        
        print("✅ Developer registration successful")
        print(f"✅ Role correctly set to: {user['role']}")
        print(f"✅ Full user data: {json.dumps(user, indent=2)}")
        
        # Store username and password for login test
        self.__class__.test_username = self.test_user["username"]
        self.__class__.test_password = self.test_user["password"]
        
    def test_02_login_developer(self):
        """Test login with the new developer credentials"""
        print("\n🔍 Testing developer login...")
        
        # Skip if registration failed
        if not hasattr(self.__class__, 'test_username'):
            self.skipTest("Registration failed, skipping login test")
        
        # Login data
        login_data = {
            "username": self.__class__.test_username,
            "password": self.__class__.test_password
        }
        
        print(f"🔍 Logging in with username: {login_data['username']}")
        
        # Login with the developer credentials
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        
        # Check if login was successful
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        # Parse the response
        data = response.json()
        
        # Verify the response structure
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        self.assertIn("user", data, "User data not found in response")
        
        # Verify user data
        user = data["user"]
        self.assertEqual(user["username"], self.__class__.test_username, "Username mismatch")
        self.assertEqual(user["role"], "developer", "Role mismatch - expected 'developer'")
        
        print("✅ Developer login successful")
        print(f"✅ Role correctly returned as: {user['role']}")
        print(f"✅ Full user data: {json.dumps(user, indent=2)}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
        
    def test_01_register_developer(self):
        """Test registering a new developer user with role 'developer'"""
        print("\n🔍 Testing developer registration...")
        
        # Register the developer user
        response = requests.post(f"{self.base_url}/auth/register", json=self.test_user)
        
        # Check if registration was successful
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        
        # Parse the response
        data = response.json()
        
        # Verify the response structure
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        self.assertIn("user", data, "User data not found in response")
        
        # Verify user data
        user = data["user"]
        self.assertEqual(user["username"], self.test_user["username"], "Username mismatch")
        self.assertEqual(user["email"], self.test_user["email"], "Email mismatch")
        self.assertEqual(user["role"], "developer", "Role mismatch - expected 'developer'")
        
        # Store token for login test
        self.access_token = data["access_token"]
        
        print("✅ Developer registration successful")
        print(f"✅ Role correctly set to: {user['role']}")
        
    def test_02_login_developer(self):
        """Test login with the new developer credentials"""
        print("\n🔍 Testing developer login...")
        
        # Skip if registration failed
        if not hasattr(self, 'access_token'):
            self.skipTest("Registration failed, skipping login test")
        
        # Login data
        login_data = {
            "username": self.test_user["username"],
            "password": self.test_user["password"]
        }
        
        # Login with the developer credentials
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        
        # Check if login was successful
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        # Parse the response
        data = response.json()
        
        # Verify the response structure
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("token_type", data, "Token type not found in response")
        self.assertIn("user", data, "User data not found in response")
        
        # Verify user data
        user = data["user"]
        self.assertEqual(user["username"], self.test_user["username"], "Username mismatch")
        self.assertEqual(user["email"], self.test_user["email"], "Email mismatch")
        self.assertEqual(user["role"], "developer", "Role mismatch - expected 'developer'")
        
        print("✅ Developer login successful")
        print(f"✅ Role correctly returned as: {user['role']}")

if __name__ == "__main__":
    unittest.main(verbosity=2)