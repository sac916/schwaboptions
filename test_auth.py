#!/usr/bin/env python3
"""
Test script to verify Schwab API authentication
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from data.schwab_client import schwab_client
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_authentication():
    """Test Schwab API authentication"""
    print("🔐 Testing Schwab API Authentication...")
    print("=" * 50)
    
    # Test authentication
    if schwab_client.authenticate():
        print("✅ Authentication successful!")
        
        # Test a simple API call
        print("\n📊 Testing API call (SPY quote)...")
        quotes = schwab_client.get_quotes(['SPY'])
        
        if quotes:
            print("✅ API call successful!")
            print(f"📈 SPY data received: {len(quotes)} items")
            return True
        else:
            print("❌ API call failed")
            return False
    else:
        print("❌ Authentication failed")
        print("\n🔍 Troubleshooting steps:")
        print("1. Check your .env file has correct API_KEY and API_SECRET")
        print("2. Verify your Schwab app callback URL is set to: https://127.0.0.1")
        print("3. Make sure your Schwab app is approved and active")
        return False

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)