#!/usr/bin/env python3
"""
Direct Schwab authentication handler that processes callback URL programmatically
"""
import schwabdev as schwab
import os
import sys
from urllib.parse import urlparse, parse_qs
from config import API_KEY, API_SECRET

def process_callback_url(callback_url):
    """Extract authorization code from callback URL"""
    try:
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)

        if 'code' in query_params:
            auth_code = query_params['code'][0]
            print(f"✅ Extracted authorization code: {auth_code[:20]}...")
            return auth_code
        else:
            print(f"❌ No authorization code found in URL: {callback_url}")
            return None
    except Exception as e:
        print(f"❌ Error parsing callback URL: {e}")
        return None

def authenticate_with_code():
    """Authenticate using the callback URL you provided"""

    # Your callback URL
    callback_url = "https://127.0.0.1/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.7nKRGNOdHq8K7Rp0E_JHR4WFj24fRCe0bmb3EsqwXz0%40&session=ed160729-398f-4185-b9ae-c585dcd6677e"

    # Extract the authorization code
    auth_code = process_callback_url(callback_url)
    if not auth_code:
        return False

    # Token file path
    tokens_file = os.path.join(os.path.dirname(__file__), 'schwab_tokens.json')

    print(f"Token file path: {tokens_file}")
    print(f"API Key: {API_KEY[:10]}... (masked)")

    try:
        # Create client with your credentials
        client = schwab.Client(
            app_key=API_KEY,
            app_secret=API_SECRET,
            callback_url="https://127.0.0.1",
            tokens_file=tokens_file,
            timeout=30
        )

        # Monkey patch to automatically provide the callback URL
        original_input = __builtins__['input']

        def mock_input(prompt):
            if "paste the address bar url here" in prompt.lower():
                print(f"Auto-providing callback URL: {callback_url}")
                return callback_url
            return original_input(prompt)

        __builtins__['input'] = mock_input

        # This should now work automatically
        print("Attempting authentication...")

        # Try to make a test call which will trigger auth if needed
        response = client.quotes(['SPY'])

        # Restore original input
        __builtins__['input'] = original_input

        if response.ok:
            print("✅ Authentication successful!")
            print("✅ API connection test passed!")
            data = response.json()
            if 'SPY' in data:
                price = data['SPY'].get('lastPrice', 'N/A')
                print(f"✅ SPY Last Price: ${price}")
            return True
        else:
            print(f"❌ API test failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

if __name__ == "__main__":
    success = authenticate_with_code()
    if success:
        print("\n🎉 Ready to run the dashboard!")
        print("Run: source venv/bin/activate && python dash_app.py")
    else:
        print("\n❌ Authentication failed. Check your credentials and callback URL.")