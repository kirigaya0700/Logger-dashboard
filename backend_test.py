import requests
import unittest
import random
import string
from datetime import datetime, date, timedelta

class DevLogAPITester(unittest.TestCase):
    """Test suite for DevLog API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        cls.base_url = "https://036767ed-f0d6-4494-8214-45adc8d0656a.preview.emergentagent.com/api"
        
        # Generate unique usernames to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        cls.dev_username = f"dev_test_{timestamp}_{random_suffix}"
        cls.manager_username = f"mgr_test_{timestamp}_{random_suffix}"
        
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
    
    def test_10_get_productivity_data(self):
        """Test retrieving productivity data"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{self.base_url}/analytics/productivity", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get productivity data failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertEqual(len(data), 30, "Expected 30 days of data")
        
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
            print(f"✅ Exported data successfully")
        elif response.status_code == 404:
            print("⚠️ No data to export in date range")
            self.skipTest("No data available in date range")
        else:
            self.fail(f"Export data failed with status {response.status_code}: {response.text}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
