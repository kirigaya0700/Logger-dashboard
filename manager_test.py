import requests
import unittest
from datetime import datetime, date, timedelta
import json

class ManagerFunctionalityTester(unittest.TestCase):
    """Test suite for Manager functionality in DevLog API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests"""
        cls.base_url = "https://985d2939-72f1-42ea-a645-3d477bacf989.preview.emergentagent.com/api"
        
        # Manager credentials from sample data
        cls.manager_username = "sarah_manager"
        cls.manager_password = "Demo123!"
        
        # Developer credentials from sample data
        cls.dev_usernames = ["john_dev", "alice_dev", "bob_dev", "emma_dev"]
        cls.dev_password = "Demo123!"
        
        # Login as manager to get token
        cls.login_manager()
        
        # Login as one developer to get token for comparison
        cls.login_developer()
    
    @classmethod
    def login_manager(cls):
        """Login as manager"""
        login_data = {
            "username": cls.manager_username,
            "password": cls.manager_password
        }
        
        response = requests.post(f"{cls.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Manager login failed: {response.text}")
            return
        
        data = response.json()
        cls.manager_token = data["access_token"]
        cls.manager_id = data["user"]["id"]
        print(f"✅ Manager logged in: {cls.manager_username}")
    
    @classmethod
    def login_developer(cls):
        """Login as a developer"""
        login_data = {
            "username": cls.dev_usernames[0],  # Using first developer
            "password": cls.dev_password
        }
        
        response = requests.post(f"{cls.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Developer login failed: {response.text}")
            return
        
        data = response.json()
        cls.dev_token = data["access_token"]
        cls.dev_id = data["user"]["id"]
        print(f"✅ Developer logged in: {cls.dev_usernames[0]}")
    
    def test_01_manager_login(self):
        """Test manager login functionality"""
        login_data = {
            "username": self.manager_username,
            "password": self.manager_password
        }
        
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Manager login failed: {response.text}")
        
        data = response.json()
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("user", data, "User data not found in response")
        self.assertEqual(data["user"]["username"], self.manager_username, "Username mismatch")
        self.assertEqual(data["user"]["role"], "manager", "Role should be manager")
        
        print(f"✅ Manager login successful for: {self.manager_username}")
    
    def test_02_access_team_developers(self):
        """Test manager access to team developers endpoint"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team developers failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertGreater(len(data), 0, "No developers found under this manager")
        
        # Check if all developers are assigned to this manager
        for dev in data:
            self.assertEqual(dev["manager_id"], self.manager_id, "Developer not assigned to this manager")
            self.assertEqual(dev["role"], "developer", "User is not a developer")
        
        # Check if all sample developers are present
        dev_usernames_found = [dev["username"] for dev in data]
        for username in self.dev_usernames:
            self.assertIn(username, dev_usernames_found, f"Developer {username} not found in team")
        
        print(f"✅ Manager can access team developers: found {len(data)} developers")
    
    def test_03_access_team_logs(self):
        """Test manager access to team logs endpoint"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team logs failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        if len(data) > 0:
            print(f"✅ Manager can access team logs: found {len(data)} logs")
        else:
            print("⚠️ No team logs found, but endpoint is accessible")
    
    def test_04_filter_team_logs_by_date(self):
        """Test filtering team logs by date"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Get logs from the last 30 days
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        response = requests.get(
            f"{self.base_url}/team/logs?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200, f"Get filtered team logs failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # Verify all logs are within the date range
        for log in data:
            log_date = date.fromisoformat(log["date"])
            self.assertGreaterEqual(log_date, date.fromisoformat(start_date), "Log date before start_date")
            self.assertLessEqual(log_date, date.fromisoformat(end_date), "Log date after end_date")
        
        print(f"✅ Manager can filter team logs by date: found {len(data)} logs in date range")
    
    def test_05_filter_team_logs_by_developer(self):
        """Test filtering team logs by developer"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # First get all developers
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, "Get team developers failed")
        
        developers = response.json()
        if len(developers) == 0:
            self.skipTest("No developers found to test filtering")
        
        # Pick the first developer to filter by
        developer_id = developers[0]["id"]
        developer_username = developers[0]["username"]
        
        response = requests.get(f"{self.base_url}/team/logs?developer_id={developer_id}", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team logs filtered by developer failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        
        # Verify all logs are from the specified developer
        for log in data:
            self.assertEqual(log["user_id"], developer_id, "Log from wrong developer returned")
            self.assertEqual(log["user_name"], developer_username, "Username mismatch in log")
        
        print(f"✅ Manager can filter team logs by developer: found {len(data)} logs for {developer_username}")
    
    def test_06_add_feedback_to_log(self):
        """Test adding feedback to a developer log"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # First get team logs to find one to add feedback to
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 200, "Get team logs failed")
        
        logs = response.json()
        if len(logs) == 0:
            self.skipTest("No logs found to add feedback to")
        
        # Pick the first log to add feedback to
        log_id = logs[0]["id"]
        developer_name = logs[0]["user_name"]
        
        feedback_data = {
            "log_id": log_id,
            "feedback_text": f"Great work on this log! Keep up the good work. - Feedback added during testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = requests.post(f"{self.base_url}/feedback", json=feedback_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Add feedback failed: {response.text}")
        
        data = response.json()
        self.assertEqual(data["log_id"], log_id, "Log ID mismatch")
        self.assertEqual(data["manager_id"], self.manager_id, "Manager ID mismatch")
        self.assertEqual(data["feedback_text"], feedback_data["feedback_text"], "Feedback text mismatch")
        
        # Verify feedback appears in the log when retrieved
        response = requests.get(f"{self.base_url}/team/logs?developer_id={logs[0]['user_id']}", headers=headers)
        self.assertEqual(response.status_code, 200, "Get logs after feedback failed")
        
        updated_logs = response.json()
        log_found = False
        for log in updated_logs:
            if log["id"] == log_id:
                log_found = True
                self.assertIsNotNone(log["feedback"], "Feedback not found in log")
                self.assertEqual(log["feedback"], feedback_data["feedback_text"], "Feedback text mismatch")
                break
        
        self.assertTrue(log_found, "Log not found after adding feedback")
        print(f"✅ Manager can add feedback to developer logs: added feedback to {developer_name}'s log")
    
    def test_07_developer_cannot_access_team_endpoints(self):
        """Test that developers cannot access manager-only endpoints"""
        if not hasattr(self, 'dev_token'):
            self.skipTest("Developer login failed, cannot test access restrictions")
        
        headers = {"Authorization": f"Bearer {self.dev_token}"}
        
        # Try to access team developers
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not access team developers list")
        
        # Try to access team logs
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not access team logs")
        
        # Try to add feedback
        feedback_data = {
            "log_id": "some-log-id",
            "feedback_text": "Developers should not be able to add feedback"
        }
        response = requests.post(f"{self.base_url}/feedback", json=feedback_data, headers=headers)
        self.assertEqual(response.status_code, 403, "Developers should not be able to add feedback")
        
        print("✅ Role-based access control prevents developers from accessing manager endpoints")
    
    def test_08_verify_developer_assignment(self):
        """Verify that developers are correctly assigned to the manager"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Get all developers under this manager
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, "Get team developers failed")
        
        developers = response.json()
        self.assertGreater(len(developers), 0, "No developers found under this manager")
        
        # Check if all sample developers are present and assigned to this manager
        dev_usernames_found = [dev["username"] for dev in developers]
        for username in self.dev_usernames:
            self.assertIn(username, dev_usernames_found, f"Developer {username} not found in team")
        
        # Verify each developer has the correct manager_id
        for dev in developers:
            self.assertEqual(dev["manager_id"], self.manager_id, f"Developer {dev['username']} not assigned to this manager")
        
        print(f"✅ All {len(developers)} developers are correctly assigned to manager {self.manager_username}")

if __name__ == "__main__":
    unittest.main(verbosity=2)