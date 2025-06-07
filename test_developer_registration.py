import requests
import unittest
import json

class DeveloperRegistrationTester(unittest.TestCase):
    """Test suite for Developer Registration and Role Assignment"""
    
    def setUp(self):
        """Set up test data for each test"""
        self.base_url = "https://985d2939-72f1-42ea-a645-3d477bacf989.preview.emergentagent.com/api"
        
        # Test user data
        self.test_user = {
            "username": "test_developer_new",
            "email": "test@test.com",
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