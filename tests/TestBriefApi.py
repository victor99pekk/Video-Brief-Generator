import os
import sys
import json
import requests
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import the Flask app and dependencies
from web.web import app, generate_brief

class TestBriefAPI(unittest.TestCase):
    """Test cases for the brief generation API endpoints"""
    
    def setUp(self):
        """Set up test client and other test variables"""
        self.app = app.test_client()
        self.app.testing = True
        
    def test_health_endpoint(self):
        """Test that the health endpoint returns status ok"""
        response = self.app.get('/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
    
    @patch('web.web.generate_brief')
    def test_get_brief_endpoint_success(self, mock_generate_brief):
        """Test successful brief generation with mocked function"""
        # Set up mock return value
        mock_generate_brief.return_value = "This is a test brief for Billie jean"
        
        # Send request to the endpoint
        response = self.app.post(
            '/get-brief',
            data=json.dumps({
                'song': 'billie jean', 
                'artist': 'micheal jackson'
            }),
            content_type='application/json'
        )
        
        # Parse response
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertIn('brief', data)
        self.assertEqual(data['brief'], "This is a test brief for Billie jean")
        
    def test_get_brief_missing_data(self):
        """Test brief generation with missing data"""
        # Test with empty JSON
        response = self.app.post(
            '/get-brief',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)  # API returns 400 for empty data
        self.assertEqual(data['error'], "No data provided")
        
        # Test with missing fields but not empty JSON
        response = self.app.post(
            '/get-brief',
            data=json.dumps({'song': 'billie jean'}),  # Only include song
            content_type='application/json'
        )
        
        # This should reach generate_brief which handles missing fields
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)  # Should be 200 for partial data
        self.assertIn('brief', data)
        self.assertEqual(data['brief'], "Please provide both song and artist")
    
    def test_get_brief_invalid_json(self):
        """Test brief generation with invalid JSON"""
        response = self.app.post(
            '/get-brief',
            data="This is not JSON",
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', data)


class TestLiveAPI(unittest.TestCase):
    """Integration tests against the running API server"""
    
    @classmethod
    def setUpClass(cls):
        """Check if API server is running before tests"""
        try:
            response = requests.get('http://localhost:8080/health')
            if response.status_code != 200:
                raise Exception(f"API server returned status code {response.status_code}")
            print("API server is running, proceeding with live tests")
            cls.server_running = True
        except requests.exceptions.ConnectionError:
            print("Warning: API server does not appear to be running, skipping live tests")
            cls.server_running = False
    
    def test_live_health_endpoint(self):
        """Test the live health endpoint"""
        if not self.__class__.server_running:
            self.skipTest("API server not running")
            
        response = requests.get('http://localhost:8080/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
    
    def test_live_brief_endpoint(self):
        """Test the live brief endpoint with real data"""
        if not self.__class__.server_running:
            self.skipTest("API server not running")
            
        data = {'song': 'billie jean', 'artist': 'micheal jackson'}
        response = requests.post(
            'http://localhost:8080/get-brief',
            json=data
        )
        
        # We expect a 200 response with a brief
        self.assertEqual(response.status_code, 200)
        self.assertIn('brief', response.json())
        
        # Print the response for debugging
        print(f"Live API response: {response.json()}")


if __name__ == '__main__':
    unittest.main()