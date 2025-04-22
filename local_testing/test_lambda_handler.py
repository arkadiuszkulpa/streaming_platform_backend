import unittest
import json
import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.lambda_handler import lambda_handler  # Import the Lambda handler from the root directory

class TestLambdaHandler(unittest.TestCase):
    def test_get_movie_info(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_movie_info"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Movie info fetched successfully", response["body"])

    def test_search_movies(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "search_movies"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Movies searched successfully", response["body"])

    def test_update_user_settings(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "update_user_settings"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("User settings updated successfully", response["body"])

    def test_get_homepage_data(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_homepage_data"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Homepage data fetched successfully", response["body"])

    def test_invalid_action(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "invalid_action"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid action", response["body"])

    def test_invalid_path(self):
        event = {
            "rawPath": "/invalid_path",
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"action": "get_movie_info"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("Not Found", response["body"])

    def test_invalid_http_method(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "GET"}},
            "body": json.dumps({"action": "get_movie_info"})
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 404)
        self.assertIn("Not Found", response["body"])

    def test_malformed_request_body(self):
        event = {
            "rawPath": "/api",
            "requestContext": {"http": {"method": "POST"}},
            "body": "invalid_json"
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("error", response["body"])

if __name__ == "__main__":
    unittest.main()
