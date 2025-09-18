#!/usr/bin/env python3
"""
Fix Schwab authentication by processing the callback URL
"""
import schwabdev as schwab
import os
from config import API_KEY, API_SECRET

def fix_auth():
    """Process the authorization URL and create proper tokens"""

    # Your authorization callback URL
    callback_url = "https://127.0.0.1/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.7nKRGNOdHq8K7Rp0E_JHR4WFj24fRCe0bmb3EsqwXz0%40&session=ed160729-398f-4185-b9ae-c585dcd6677e"

    # Token file path (same as in schwab_client.py)
    tokens_file = os.path.join(os.path.dirname(__file__), 'schwab_tokens.json')

    print(f"Creating/updating token file: {tokens_file}")
    print(f"Processing callback URL: {callback_url}")

    try:
        # Initialize client and process the callback URL
        client = schwab.Client(
            app_key=API_KEY,
            app_secret=API_SECRET,
            callback_url="https://127.0.0.1",
            tokens_file=tokens_file,
            timeout=30
        )

        # Process the authorization callback URL
        client._process_authorization_callback(callback_url)

        print("✅ Authentication successful!")
        print(f"✅ Tokens saved to: {tokens_file}")

        # Test the connection
        print("\nTesting API connection...")
        response = client.quotes(['SPY'])
        if response.ok:
            print("✅ API connection test successful!")
            data = response.json()
            if 'SPY' in data:
                price = data['SPY'].get('lastPrice', 'N/A')
                print(f"✅ SPY Last Price: ${price}")
        else:
            print(f"❌ API test failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Schwab app callback URL is set to: https://127.0.0.1")
        print("2. Check that API_KEY and API_SECRET are correctly set in .env")
        print("3. The authorization URL should be fresh (not expired)")

if __name__ == "__main__":
    fix_auth()