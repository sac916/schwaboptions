#!/usr/bin/env python3
"""
Non-interactive authentication fix for SchwaOptions
Handles the EOF input error by mocking the input function
"""
import schwabdev as schwab
import os
import sys
import json
from urllib.parse import urlparse, parse_qs
from config import API_KEY, API_SECRET
import builtins

def create_non_interactive_client(callback_url):
    """Create a schwab client without interactive input prompts"""

    # Mock the input function to automatically provide the callback URL
    original_input = builtins.input

    def mock_input(prompt=""):
        # Look for the callback URL prompt and auto-respond
        if "paste" in prompt.lower() or "url" in prompt.lower() or "address" in prompt.lower():
            print(f"Auto-providing callback URL: {callback_url}")
            return callback_url
        # For any other prompts, return empty string to avoid hanging
        return ""

    # Replace input function
    builtins.input = mock_input

    try:
        tokens_file = os.path.join(os.path.dirname(__file__), 'schwab_tokens.json')

        # Remove old token file if it exists
        if os.path.exists(tokens_file):
            os.remove(tokens_file)
            print("Removed old token file")

        # Create client with mocked input
        client = schwab.Client(
            app_key=API_KEY,
            app_secret=API_SECRET,
            callback_url="https://127.0.0.1",
            tokens_file=tokens_file,
            timeout=30
        )

        # Test the connection
        print("Testing API connection...")
        response = client.quotes(['SPY'])

        if response.ok:
            data = response.json()
            spy_price = data.get('SPY', {}).get('lastPrice', 'N/A')
            print(f"✅ Authentication successful! SPY: ${spy_price}")
            return client, True
        else:
            print(f"❌ API test failed: {response.status_code}")
            return None, False

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None, False

    finally:
        # Always restore original input function
        builtins.input = original_input

def process_callback_authentication(callback_url):
    """Process callback URL for authentication"""
    if not callback_url or not callback_url.startswith("https://127.0.0.1"):
        return {"success": False, "message": "Invalid callback URL format"}

    # Extract the authorization code for verification
    try:
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)

        if 'code' not in query_params:
            return {"success": False, "message": "No authorization code found in URL"}

        auth_code = query_params['code'][0]
        print(f"Found authorization code: {auth_code[:20]}...")

    except Exception as e:
        return {"success": False, "message": f"Error parsing callback URL: {e}"}

    # Create client with non-interactive method
    client, success = create_non_interactive_client(callback_url)

    if success:
        return {
            "success": True,
            "message": "Authentication successful! API connection verified.",
            "client": client
        }
    else:
        return {
            "success": False,
            "message": "Authentication failed during token creation or API test"
        }

if __name__ == "__main__":
    # Test with a sample callback URL (replace with actual)
    test_url = input("Enter callback URL: ")
    result = process_callback_authentication(test_url)

    if result["success"]:
        print("🎉 Authentication fixed! The client is ready.")
    else:
        print(f"❌ Failed: {result['message']}")