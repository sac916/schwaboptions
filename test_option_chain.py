#!/usr/bin/env python3
"""
Test script to debug option chain API calls
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from data.schwab_client import schwab_client
import logging

# Set up logging to see debug info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_option_chain():
    """Test option chain API call with debug info"""
    print("🔐 Testing Option Chain API...")
    print("=" * 50)
    
    # Authenticate
    if not schwab_client.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Authentication successful!")
    
    # Test option chain with limited parameters to avoid overflow
    print("\n📊 Testing TSLA option chain with limited parameters...")
    
    try:
        # Use parameters to limit data and avoid overflow
        data = schwab_client.get_option_chain(
            symbol="TSLA",
            contractType="ALL",  # Get both calls and puts
            strikeCount=10,      # Limit to 10 strikes around current price
            includeUnderlyingQuote=True,
            range="NTM",         # Near the money options only
            daysToExpiration=30  # Options expiring within 30 days
        )
        
        if data:
            print("✅ Option chain data received!")
            print(f"📈 Data keys: {list(data.keys())}")
            
            # Check if we have option data
            if 'callExpDateMap' in data or 'putExpDateMap' in data:
                call_count = len(data.get('callExpDateMap', {}))
                put_count = len(data.get('putExpDateMap', {}))
                print(f"📊 Call expirations: {call_count}")
                print(f"📊 Put expirations: {put_count}")
                
                # Check underlying data
                if 'underlying' in data:
                    underlying = data['underlying']
                    print(f"📈 Underlying price: {underlying.get('last', 'N/A')}")
                
                return True
            else:
                print("⚠️ No option data in response")
                print(f"Response: {data}")
                return False
        else:
            print("❌ No data returned from API")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_option_chain()
    sys.exit(0 if success else 1)