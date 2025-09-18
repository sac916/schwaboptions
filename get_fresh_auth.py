#!/usr/bin/env python3
"""
Get a fresh authorization URL and guide through the process
"""
import schwabdev as schwab
import os
from config import API_KEY, API_SECRET

def get_auth_url():
    """Generate a fresh authorization URL"""

    print("=== Schwab API Fresh Authentication ===")
    print()
    print("❌ The previous authorization code has expired (they expire within 30 seconds).")
    print("🔄 Let's get a fresh one.")
    print()

    # Token file path
    tokens_file = os.path.join(os.path.dirname(__file__), 'schwab_tokens.json')

    print(f"📁 Token file: {tokens_file}")
    print(f"🔑 Using API Key: {API_KEY[:10]}...")
    print(f"🌐 Callback URL: https://127.0.0.1")
    print()

    # Remove old token file if it exists
    if os.path.exists(tokens_file):
        os.remove(tokens_file)
        print(f"🗑️  Removed old token file")

    print("📋 INSTRUCTIONS:")
    print("1. The script will show you a fresh authorization URL")
    print("2. Open that URL in your browser")
    print("3. Log in to Schwab and authorize the app")
    print("4. Copy the ENTIRE URL from your browser's address bar")
    print("5. Paste it when prompted (you have 30 seconds!)")
    print()

    try:
        # This will generate a fresh authorization URL and prompt for input
        client = schwab.Client(
            app_key=API_KEY,
            app_secret=API_SECRET,
            callback_url="https://127.0.0.1",
            tokens_file=tokens_file
        )

        # If we get here, authentication was successful
        print("✅ Authentication successful!")

        # Test the connection
        print("🧪 Testing API connection...")
        response = client.quotes(['SPY'])

        if response.ok:
            print("✅ API connection test PASSED!")
            data = response.json()
            if 'SPY' in data:
                price = data['SPY'].get('lastPrice', 'N/A')
                print(f"📈 SPY Last Price: ${price}")
            print()
            print("🎉 Ready to run the dashboard!")
            print("🚀 Run: python dash_app.py")
        else:
            print(f"❌ API test failed: {response.status_code}")

    except KeyboardInterrupt:
        print("\n❌ Authentication cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("- Make sure your Schwab app callback URL is exactly: https://127.0.0.1")
        print("- Check your API_KEY and API_SECRET in the .env file")
        print("- Make sure you paste the complete URL within 30 seconds")

if __name__ == "__main__":
    get_auth_url()