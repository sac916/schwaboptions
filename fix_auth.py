#!/usr/bin/env python3
"""
Proper Schwab authentication using schwabdev library
"""
import os
import sys
from schwabdev import Client

def main():
    """Create proper schwab authentication"""
    print("🔧 Fixing Schwab Authentication...")

    # Load API credentials from .env
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing API_KEY or API_SECRET in .env file")
        return False

    print(f"✅ API Key loaded: {api_key[:10]}...")
    print(f"✅ API Secret loaded: {api_secret[:10]}...")

    try:
        # Create schwab client - this will handle authentication
        print("\n🔐 Creating Schwab client...")
        client = Client(api_key, api_secret, callback_url="https://127.0.0.1")

        print("✅ Client created successfully!")
        print("📁 Token file should be created automatically")

        # Test with a simple API call
        print("\n🧪 Testing API connection...")
        result = client.market_hours(["option"])

        if result:
            print("✅ API test successful!")
            print("🎉 Authentication is working!")
            return True
        else:
            print("❌ API test failed")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Ready to start dashboard!")
        print("Run: python dash_app.py")
    else:
        print("\n💥 Authentication failed")
        sys.exit(1)