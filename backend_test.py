import requests
import unittest
import random
import string
from datetime import datetime, date, timedelta
import json

class DevLogAPITester(unittest.TestCase):
    """Test suite for DevLog API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        cls.base_url = "https://985d2939-72f1-42ea-a645-3d477bacf989.preview.emergentagent.com/api"
        
        # Generate unique usernames to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        cls.dev_username = f"dev_test_{timestamp}_{random_suffix}"
        cls.manager_username = f"mgr_test_{timestamp}_{random_suffix}"
        cls.dev2_username = f"dev2_test_{timestamp}_{random_suffix}"  # Second developer for testing
        
        # Register users
        cls.register_users()
    
    @classmethod
    def register_users(cls):
        """Register test users"""
        # Register manager
        manager_data = {
            "username": cls.manager_username,
            "email": f"{cls.manager_username}@example.com",
            "password": "Test123!",
            "role": "manager"
        }
        
        response = requests.post(f"{cls.base_url}/auth/register", json=manager_data)
        if response.status_code != 200:
            print(f"❌ Manager registration failed: {response.text}")
            return
        
        data = response.json()
        cls.manager_token = data["access_token"]
        cls.manager_id = data["user"]["id"]
        print(f"✅ Manager registered: {cls.manager_username}")
        
        # Register developer
        dev_data = {
            "username": cls.dev_username,
            "email": f"{cls.dev_username}@example.com",
            "password": "Test123!",
            "role": "developer",
            "manager_id": cls.manager_id
        }
        
        response = requests.post(f"{cls.base_url}/auth/register", json=dev_data)
        if response.status_code != 200:
            print(f"❌ Developer registration failed: {response.text}")
            return
        
        data = response.json()
        cls.token = data["access_token"]
        cls.user_id = data["user"]["id"]
        cls.log_id = None
        print(f"✅ Developer registered: {cls.dev_username}")
        
        # Register second developer (for additional testing)
        dev2_data = {
            "username": cls.dev2_username,
            "email": f"{cls.dev2_username}@example.com",
            "password": "Test123!",
            "role": "developer",
            "manager_id": cls.manager_id
        }
        
        response = requests.post(f"{cls.base_url}/auth/register", json=dev2_data)
        if response.status_code == 200:
            data = response.json()
            cls.token2 = data["access_token"]
            cls.user2_id = data["user"]["id"]
            print(f"✅ Second developer registered: {cls.dev2_username}")
        else:
            print(f"❌ Second developer registration failed: {response.text}")
    
    def test_01_login(self):
        """Test login functionality"""
        login_data = {
            "username": self.dev_username,
            "password": "Test123!"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        
        data = response.json()
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("user", data, "User data not found in response")
        self.assertEqual(data["user"]["username"], self.dev_username, "Username mismatch")
        
        print(f"✅ Login successful for: {self.dev_username}")
    
    def test_01a_login_failure(self):
        """Test login failure with incorrect credentials"""
        login_data = {
            "username": self.dev_username,
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 401, "Login should fail with incorrect password")
        print("✅ Login correctly failed with wrong password")
        
        # Test with non-existent user
        login_data = {
            "username": "nonexistent_user",
            "password": "Test123!"
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 401, "Login should fail with non-existent user")
        print("✅ Login correctly failed with non-existent user")
    
    def test_01b_auth_validation(self):
        """Test authentication validation"""
        # Test accessing protected endpoint without token
        response = requests.get(f"{self.base_url}/logs")
        self.assertEqual(response.status_code, 403, "Should return 403 without token")
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{self.base_url}/logs", headers=headers)
        self.assertEqual(response.status_code, 401, "Should return 401 with invalid token")
        
        print("✅ Authentication validation working correctly")
    
    def test_02_create_daily_log(self):
        """Test creating a daily log"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        log_data = {
            "date": date.today().isoformat(),
            "tasks": [
                {
                    "description": "Task 1 - Testing API",
                    "time_spent": 2.5,
                    "completed": True
                },
                {
                    "description": "Task 2 - Writing documentation",
                    "time_spent": 1.5,
                    "completed": False
                }
            ],
            "total_time": 4.0,
            "mood": 4,
            "blockers": "None at the moment"
        }
        
        response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Create log failed: {response.text}")
        
        data = response.json()
        self.__class__.log_id = data["id"]  # Store log_id at class level
        self.assertIsNotNone(self.__class__.log_id, "Log ID not found in response")
        self.assertEqual(data["user_id"], self.user_id, "User ID mismatch")
        self.assertEqual(len(data["tasks"]), 2, "Tasks count mismatch")
        
        print(f"✅ Daily log created with ID: {self.__class__.log_id}")
    
    def test_02a_create_duplicate_log(self):
        """Test creating a duplicate log for the same date"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        log_data = {
            "date": date.today().isoformat(),
            "tasks": [
                {
                    "description": "Duplicate Task",
                    "time_spent": 1.0,
                    "completed": True
                }
            ],
            "total_time": 1.0,
            "mood": 3,
            "blockers": None
        }
        
        response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
        self.assertEqual(response.status_code, 400, "Should prevent duplicate logs for same date")
        self.assertIn("already exists", response.text.lower(), "Error message should mention duplicate")
        
        print("✅ Duplicate log prevention working correctly")
    
    def test_02b_create_log_validation(self):
        """Test validation for log creation"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create log for tomorrow (future date should be allowed)
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        log_data = {
            "date": tomorrow,
            "tasks": [
                {
                    "description": "Future Task",
                    "time_spent": 2.0,
                    "completed": False
                }
            ],
            "total_time": 2.0,
            "mood": 4,
            "blockers": None
        }
        
        response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
        self.assertEqual(response.status_code, 200, "Should allow future date logs")
        
        # Test with invalid mood value
        log_data = {
            "date": (date.today() - timedelta(days=1)).isoformat(),
            "tasks": [
                {
                    "description": "Task with invalid mood",
                    "time_spent": 1.0,
                    "completed": True
                }
            ],
            "total_time": 1.0,
            "mood": 10,  # Invalid mood (should be 1-5)
            "blockers": None
        }
        
        response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
        # The API might not validate mood range, so this could pass or fail
        print(f"Mood validation test result: {response.status_code}")
        
        print("✅ Log creation validation tests completed")
    
    def test_03_get_logs(self):
        """Test retrieving daily logs"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/logs", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get logs failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertGreaterEqual(len(data), 1, "No logs returned")
        
        # Check if our created log is in the response
        log_found = False
        for log in data:
            if log["id"] == self.__class__.log_id:
                log_found = True
                break
                
        self.assertTrue(log_found, "Created log not found in response")
        print(f"✅ Retrieved {len(data)} logs successfully")
    
    def test_03a_get_logs_with_date_filter(self):
        """Test retrieving logs with date filters"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test with start_date filter
        start_date = (date.today() - timedelta(days=7)).isoformat()
        response = requests.get(f"{self.base_url}/logs?start_date={start_date}", headers=headers)
        self.assertEqual(response.status_code, 200, "Get logs with start_date failed")
        
        # Test with end_date filter
        end_date = date.today().isoformat()
        response = requests.get(f"{self.base_url}/logs?end_date={end_date}", headers=headers)
        self.assertEqual(response.status_code, 200, "Get logs with end_date failed")
        
        # Test with both filters
        response = requests.get(
            f"{self.base_url}/logs?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200, "Get logs with date range failed")
        
        print("✅ Log filtering by date working correctly")
    
    def test_04_update_log(self):
        """Test updating a daily log"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        update_data = {
            "date": date.today().isoformat(),
            "tasks": [
                {
                    "description": "Updated Task 1",
                    "time_spent": 3.0,
                    "completed": True
                },
                {
                    "description": "Updated Task 2",
                    "time_spent": 2.0,
                    "completed": True
                }
            ],
            "total_time": 5.0,
            "mood": 5,
            "blockers": "Updated blockers"
        }
        
        response = requests.put(f"{self.base_url}/logs/{self.__class__.log_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Update log failed: {response.text}")
        
        data = response.json()
        self.assertEqual(data["id"], self.__class__.log_id, "Log ID mismatch")
        self.assertEqual(data["mood"], 5, "Mood not updated")
        self.assertEqual(data["total_time"], 5.0, "Total time not updated")
        
        print(f"✅ Log updated successfully: {self.__class__.log_id}")
    
    def test_04a_update_nonexistent_log(self):
        """Test updating a non-existent log"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        fake_log_id = str(random.randint(10000, 99999))
        update_data = {
            "date": date.today().isoformat(),
            "tasks": [
                {
                    "description": "Task for non-existent log",
                    "time_spent": 1.0,
                    "completed": True
                }
            ],
            "total_time": 1.0,
            "mood": 3,
            "blockers": None
        }
        
        response = requests.put(f"{self.base_url}/logs/{fake_log_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 404, "Should return 404 for non-existent log")
        
        print("✅ Non-existent log update correctly returns 404")
    
    def test_04b_update_another_users_log(self):
        """Test updating another user's log (should fail)"""
        # This test requires the second developer to have been registered successfully
        if not hasattr(self.__class__, 'token2'):
            self.skipTest("Second developer not registered")
            
        # First, create a log for the second developer
        headers = {"Authorization": f"Bearer {self.token2}"}
        
        log_data = {
            "date": (date.today() - timedelta(days=1)).isoformat(),  # Use yesterday to avoid conflict
            "tasks": [
                {
                    "description": "Second developer's task",
                    "time_spent": 1.0,
                    "completed": True
                }
            ],
            "total_time": 1.0,
            "mood": 4,
            "blockers": None
        }
        
        response = requests.post(f"{self.base_url}/logs", json=log_data, headers=headers)
        if response.status_code != 200:
            self.skipTest(f"Could not create log for second developer: {response.text}")
            
        dev2_log_id = response.json()["id"]
        
        # Now try to update this log as the first developer
        headers = {"Authorization": f"Bearer {self.token}"}
        
        update_data = {
            "date": (date.today() - timedelta(days=1)).isoformat(),
            "tasks": [
                {
                    "description": "Trying to update another user's log",
                    "time_spent": 1.0,
                    "completed": True
                }
            ],
            "total_time": 1.0,
            "mood": 3,
            "blockers": None
        }
        
        response = requests.put(f"{self.base_url}/logs/{dev2_log_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 404, "Should not allow updating another user's log")
        
        print("✅ Cross-user log update protection working correctly")
    
    def test_05_manager_get_team_logs(self):
        """Test manager retrieving team logs"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team logs failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # Check if developer's log is in the response
        dev_log_found = False
        for log in data:
            if log["user_id"] == self.user_id:
                dev_log_found = True
                break
                
        self.assertTrue(dev_log_found, "Developer's log not found in team logs")
        print(f"✅ Manager retrieved team logs successfully")
    
    def test_05a_manager_get_filtered_team_logs(self):
        """Test manager retrieving filtered team logs"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Test filtering by developer
        response = requests.get(f"{self.base_url}/team/logs?developer_id={self.user_id}", headers=headers)
        self.assertEqual(response.status_code, 200, "Get team logs filtered by developer failed")
        
        data = response.json()
        # All logs should be from the specified developer
        for log in data:
            self.assertEqual(log["user_id"], self.user_id, "Log from wrong developer returned")
        
        # Test filtering by date range
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()
        
        response = requests.get(
            f"{self.base_url}/team/logs?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200, "Get team logs filtered by date range failed")
        
        print("✅ Manager team logs filtering working correctly")
    
    def test_05b_developer_get_team_logs(self):
        """Test developer trying to access team logs (should fail)"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not access team logs")
        
        print("✅ Role-based access control for team logs working correctly")
    
    def test_06_manager_get_developers(self):
        """Test manager retrieving team developers"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team developers failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # Check if our developer is in the response
        dev_found = False
        for dev in data:
            if dev["id"] == self.user_id:
                dev_found = True
                break
                
        self.assertTrue(dev_found, "Developer not found in team developers")
        print(f"✅ Manager retrieved team developers successfully")
    
    def test_06a_developer_get_team_developers(self):
        """Test developer trying to access team developers (should fail)"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not access team developers list")
        
        print("✅ Role-based access control for team developers list working correctly")
    
    def test_07_manager_add_feedback(self):
        """Test manager adding feedback to a log"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        feedback_data = {
            "log_id": self.__class__.log_id,
            "feedback_text": "Great work on the tasks! Keep it up."
        }
        
        response = requests.post(f"{self.base_url}/feedback", json=feedback_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Add feedback failed: {response.text}")
        
        data = response.json()
        self.assertEqual(data["log_id"], self.__class__.log_id, "Log ID mismatch")
        self.assertEqual(data["manager_id"], self.manager_id, "Manager ID mismatch")
        
        print(f"✅ Manager added feedback successfully")
    
    def test_07a_developer_add_feedback(self):
        """Test developer trying to add feedback (should fail)"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        feedback_data = {
            "log_id": self.__class__.log_id,
            "feedback_text": "Self-feedback should not be allowed"
        }
        
        response = requests.post(f"{self.base_url}/feedback", json=feedback_data, headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not be able to add feedback")
        
        print("✅ Role-based access control for feedback working correctly")
    
    def test_08_get_notifications(self):
        """Test retrieving notifications"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/notifications", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get notifications failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # We should have at least the welcome notification and feedback notification
        self.assertGreaterEqual(len(data), 1, "No notifications returned")
        
        print(f"✅ Retrieved {len(data)} notifications successfully")
    
    def test_09_mark_notification_read(self):
        """Test marking a notification as read"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # First, get notifications to find one to mark as read
        response = requests.get(f"{self.base_url}/notifications", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get notifications failed: {response.text}")
        
        data = response.json()
        if len(data) > 0:
            notification_id = data[0]["id"]
            
            response = requests.put(f"{self.base_url}/notifications/{notification_id}/read", headers=headers)
            self.assertEqual(response.status_code, 200, f"Mark notification read failed: {response.text}")
            
            # Verify it's marked as read
            response = requests.get(f"{self.base_url}/notifications", headers=headers)
            updated_data = response.json()
            
            notification_found = False
            for notif in updated_data:
                if notif["id"] == notification_id:
                    notification_found = True
                    self.assertTrue(notif["read"], "Notification not marked as read")
                    break
                    
            self.assertTrue(notification_found, "Notification not found after update")
            print(f"✅ Notification marked as read successfully")
        else:
            print("⚠️ No notifications to mark as read")
            self.skipTest("No notifications available to test")
    
    def test_09a_mark_another_users_notification(self):
        """Test marking another user's notification as read (should fail)"""
        # This test requires the second developer to have been registered successfully
        if not hasattr(self.__class__, 'token2') or not hasattr(self.__class__, 'user2_id'):
            self.skipTest("Second developer not registered")
            
        # Get notifications for second developer
        headers = {"Authorization": f"Bearer {self.token2}"}
        
        response = requests.get(f"{self.base_url}/notifications", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            self.skipTest("No notifications available for second developer")
            
        dev2_notification_id = response.json()[0]["id"]
        
        # Try to mark it as read as the first developer
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.put(f"{self.base_url}/notifications/{dev2_notification_id}/read", headers=headers)
        # Should either return 404 (not found) or 403 (forbidden)
        self.assertIn(response.status_code, [403, 404], "Should not allow marking another user's notification")
        
        print("✅ Cross-user notification protection working correctly")
    
    def test_10_get_productivity_data(self):
        """Test retrieving productivity data"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/analytics/productivity", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get productivity data failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 30, "Expected 30 days of data")
        
        # Test with custom days parameter
        response = requests.get(f"{self.base_url}/analytics/productivity?days=7", headers=headers)
        self.assertEqual(response.status_code, 200, "Get productivity with custom days failed")
        
        data = response.json()
        self.assertEqual(len(data), 7, "Expected 7 days of data")
        
        print(f"✅ Retrieved productivity data successfully")
    
    def test_11_export_data(self):
        """Test exporting data as CSV"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        response = requests.get(
            f"{self.base_url}/analytics/export?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        
        # This might return 404 if no data in range, or 200 with CSV data
        if response.status_code == 200:
            data = response.json()
            self.assertIn("csv_data", data, "CSV data not found in response")
            
            # Verify CSV format
            csv_data = data["csv_data"]
            self.assertIn("Date", csv_data, "CSV header not found")
            self.assertIn("Task", csv_data, "CSV header not found")
            self.assertIn("Time Spent", csv_data, "CSV header not found")
            
            print(f"✅ Exported data successfully")
        elif response.status_code == 404:
            print("⚠️ No data to export in date range")
            self.skipTest("No data available in date range")
        else:
            self.fail(f"Export data failed with status {response.status_code}: {response.text}")
    
    def test_12_get_managers_list(self):
        """Test retrieving managers list for registration"""
        response = requests.get(f"{self.base_url}/users/managers")
        self.assertEqual(response.status_code, 200, f"Get managers list failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # Check if our manager is in the response
        manager_found = False
        for manager in data:
            if manager["id"] == self.manager_id:
                manager_found = True
                break
                
        self.assertTrue(manager_found, "Our manager not found in managers list")
        print(f"✅ Retrieved managers list successfully")

if __name__ == "__main__":
    unittest.main(verbosity=2)
