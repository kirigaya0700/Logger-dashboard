import requests
import unittest
from datetime import datetime, date, timedelta
import json

class DevLogManagerFunctionalityTester(unittest.TestCase):
    """Comprehensive test suite for Manager functionality in DevLog API"""
    
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
        
        # Login as all developers to get their IDs
        cls.dev_tokens = {}
        cls.dev_ids = {}
        for username in cls.dev_usernames:
            cls.login_developer(username)
    
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
    def login_developer(cls, username):
        """Login as a specific developer"""
        login_data = {
            "username": username,
            "password": cls.dev_password
        }
        
        response = requests.post(f"{cls.base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Developer login failed for {username}: {response.text}")
            return
        
        data = response.json()
        cls.dev_tokens[username] = data["access_token"]
        cls.dev_ids[username] = data["user"]["id"]
        print(f"✅ Developer logged in: {username}")
    
    def test_01_manager_login(self):
        """Test manager login with provided credentials"""
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
        
        print(f"✅ Manager login successful with credentials: {self.manager_username}/Demo123!")
    
    def test_02_access_team_developers(self):
        """Test manager access to team developers endpoint"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team developers failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertGreaterEqual(len(data), 4, "Not all sample developers found")
        
        # Check if all sample developers are present
        dev_usernames_found = [dev["username"] for dev in data]
        for username in self.dev_usernames:
            self.assertIn(username, dev_usernames_found, f"Developer {username} not found in team")
        
        print(f"✅ Manager can access /api/team/developers endpoint: found {len(data)} developers")
        
        # Print all developers for verification
        print("Developers under manager:")
        for dev in data:
            print(f"  - {dev['username']} (ID: {dev['id']})")
    
    def test_03_access_team_logs(self):
        """Test manager access to team logs endpoint"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get team logs failed: {response.text}")
        
        data = response.json()
        self.assertIsInstance(data, list, "Response is not a list")
        self.assertGreater(len(data), 0, "No team logs found")
        
        print(f"✅ Manager can access /api/team/logs endpoint: found {len(data)} logs")
        
        # Print sample logs for verification
        print("Sample team logs:")
        for i, log in enumerate(data[:3]):  # Show first 3 logs
            print(f"  - Log {i+1}: {log['date']} by {log['user_name']} ({log['total_time']} hours, {len(log['tasks'])} tasks)")
    
    def test_04_filter_team_logs_by_date(self):
        """Test filtering team logs by date"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Get logs from the last 7 days
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()
        
        response = requests.get(
            f"{self.base_url}/team/logs?start_date={start_date}&end_date={end_date}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200, f"Get filtered team logs by date failed: {response.text}")
        
        data_with_date_filter = response.json()
        self.assertIsInstance(data_with_date_filter, list, "Response is not a list")
        
        # Get all logs for comparison
        response = requests.get(f"{self.base_url}/team/logs", headers=headers)
        self.assertEqual(response.status_code, 200, "Get all team logs failed")
        all_logs = response.json()
        
        # Verify filtering works (filtered logs should be fewer than or equal to all logs)
        self.assertLessEqual(len(data_with_date_filter), len(all_logs), "Date filtering not working correctly")
        
        # Verify all logs are within the date range
        for log in data_with_date_filter:
            log_date = date.fromisoformat(log["date"])
            self.assertGreaterEqual(log_date, date.fromisoformat(start_date), "Log date before start_date")
            self.assertLessEqual(log_date, date.fromisoformat(end_date), "Log date after end_date")
        
        print(f"✅ Manager can filter team logs by date: found {len(data_with_date_filter)} logs in date range {start_date} to {end_date}")
    
    def test_05_filter_team_logs_by_developer(self):
        """Test filtering team logs by developer_id"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Test for each developer
        for username in self.dev_usernames:
            if username not in self.dev_ids:
                print(f"⚠️ Skipping filter test for {username} - login failed")
                continue
                
            developer_id = self.dev_ids[username]
            
            response = requests.get(f"{self.base_url}/team/logs?developer_id={developer_id}", headers=headers)
            self.assertEqual(response.status_code, 200, f"Get team logs filtered by developer {username} failed: {response.text}")
            
            data = response.json()
            self.assertIsInstance(data, list, "Response is not a list")
            
            # Verify all logs are from the specified developer
            for log in data:
                self.assertEqual(log["user_id"], developer_id, f"Log from wrong developer returned for {username}")
                self.assertEqual(log["user_name"], username, f"Username mismatch in log for {username}")
            
            print(f"✅ Manager can filter team logs by developer_id: found {len(data)} logs for {username}")
    
    def test_06_add_feedback_to_developer_logs(self):
        """Test adding feedback to developer logs"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Get logs for each developer and add feedback to one log per developer
        for username in self.dev_usernames:
            if username not in self.dev_ids:
                print(f"⚠️ Skipping feedback test for {username} - login failed")
                continue
                
            developer_id = self.dev_ids[username]
            
            # Get logs for this developer
            response = requests.get(f"{self.base_url}/team/logs?developer_id={developer_id}", headers=headers)
            self.assertEqual(response.status_code, 200, f"Get logs for {username} failed")
            
            logs = response.json()
            if len(logs) == 0:
                print(f"⚠️ No logs found for {username}, skipping feedback test")
                continue
            
            # Add feedback to the first log
            log_id = logs[0]["id"]
            log_date = logs[0]["date"]
            
            feedback_data = {
                "log_id": log_id,
                "feedback_text": f"Great work on {log_date}, {username}! Your productivity is impressive. Keep it up! - Feedback added during testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
            response = requests.post(f"{self.base_url}/feedback", json=feedback_data, headers=headers)
            self.assertEqual(response.status_code, 200, f"Add feedback to {username}'s log failed: {response.text}")
            
            data = response.json()
            self.assertEqual(data["log_id"], log_id, f"Log ID mismatch for {username}'s feedback")
            self.assertEqual(data["manager_id"], self.manager_id, f"Manager ID mismatch for {username}'s feedback")
            self.assertEqual(data["feedback_text"], feedback_data["feedback_text"], f"Feedback text mismatch for {username}")
            
            # Verify feedback appears in the log when retrieved
            response = requests.get(f"{self.base_url}/team/logs?developer_id={developer_id}", headers=headers)
            self.assertEqual(response.status_code, 200, f"Get logs after feedback for {username} failed")
            
            updated_logs = response.json()
            log_found = False
            for log in updated_logs:
                if log["id"] == log_id:
                    log_found = True
                    self.assertIsNotNone(log["feedback"], f"Feedback not found in {username}'s log")
                    self.assertEqual(log["feedback"], feedback_data["feedback_text"], f"Feedback text mismatch in {username}'s log")
                    break
            
            self.assertTrue(log_found, f"Log not found after adding feedback for {username}")
            print(f"✅ Manager can add feedback to {username}'s log")
    
    def test_07_verify_developer_assignment(self):
        """Verify that developers are correctly assigned to the manager"""
        headers = {"Authorization": f"Bearer {self.manager_token}"}
        
        # Get all developers under this manager
        response = requests.get(f"{self.base_url}/team/developers", headers=headers)
        self.assertEqual(response.status_code, 200, "Get team developers failed")
        
        developers = response.json()
        self.assertGreaterEqual(len(developers), 4, "Not all sample developers found")
        
        # Check if all sample developers are present and assigned to this manager
        dev_usernames_found = [dev["username"] for dev in developers]
        for username in self.dev_usernames:
            self.assertIn(username, dev_usernames_found, f"Developer {username} not found in team")
        
        # Verify each developer has the correct manager_id
        for dev in developers:
            if dev["username"] in self.dev_usernames:
                self.assertEqual(dev["manager_id"], self.manager_id, f"Developer {dev['username']} not assigned to this manager")
                self.assertEqual(dev["role"], "developer", f"User {dev['username']} is not a developer")
        
        print(f"✅ All developers are correctly assigned to manager {self.manager_username}")
        
        # Print assignment details
        print("Developer assignments:")
        for dev in developers:
            if dev["username"] in self.dev_usernames:
                print(f"  - {dev['username']} is assigned to manager {self.manager_username} (ID: {dev['manager_id']})")

if __name__ == "__main__":
    unittest.main(verbosity=2)