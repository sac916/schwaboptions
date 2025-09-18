#!/usr/bin/env python3
"""
Simple script to fix Schwab authentication
"""
import sys
import os
sys.path.append('.')

from data.schwab_client import schwab_client

def authenticate():
    """Authenticate with Schwab API"""
    print("Starting Schwab authentication...")

    # This will prompt for OAuth URL
    print("You'll need to paste your OAuth URL when prompted.")

    try:
        # Test a simple API call to trigger authentication
        result = schwab_client.get_option_chain(
            symbol="SPY",
            contractType="ALL",
            strikeCount=5,
            includeUnderlyingQuote=True,
            range="ALL",
            daysToExpiration=30
        )

        if result:
            print("✅ Authentication successful!")
            print("✅ Token file created successfully!")
            return True
        else:
            print("❌ Authentication failed - no data returned")
            return False

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

if __name__ == "__main__":
    success = authenticate()
    if success:
        print("\n🎉 Ready to start dashboard!")
        print("Run: python dash_app.py")
    else:
        print("\n💥 Authentication failed. Try again.")