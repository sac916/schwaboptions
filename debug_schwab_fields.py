#!/usr/bin/env python3
"""
Debug script to see exactly what fields Schwab API returns
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from data.schwab_client import schwab_client
import json

def debug_schwab_fields():
    """Debug what fields Schwab actually returns"""
    print("🔍 Debugging Schwab API field mapping...")
    print("=" * 60)
    
    # Authenticate
    if not schwab_client.authenticate():
        print("❌ Authentication failed")
        return False
    
    # Get option chain data
    data = schwab_client.get_option_chain(
        symbol="TSLA",
        contractType="ALL",
        strikeCount=5,  # Just 5 strikes to keep output manageable
        includeUnderlyingQuote=True,
        range="NTM",
        daysToExpiration=30
    )
    
    if not data:
        print("❌ No data returned")
        return False
    
    print("✅ Data received! Analyzing structure...")
    print(f"📊 Top-level keys: {list(data.keys())}")
    
    # Look at call data structure
    call_dates = data.get('callExpDateMap', {})
    if call_dates:
        first_date = list(call_dates.keys())[0]
        first_strike_data = call_dates[first_date]
        first_strike = list(first_strike_data.keys())[0]
        first_contract = first_strike_data[first_strike][0]
        
        print(f"\n📈 CALL contract fields:")
        for key, value in first_contract.items():
            print(f"  {key}: {value} ({type(value).__name__})")
    
    # Look at put data structure  
    put_dates = data.get('putExpDateMap', {})
    if put_dates:
        first_date = list(put_dates.keys())[0]
        first_strike_data = put_dates[first_date]
        first_strike = list(first_strike_data.keys())[0]
        first_contract = first_strike_data[first_strike][0]
        
        print(f"\n📉 PUT contract fields:")
        for key, value in first_contract.items():
            print(f"  {key}: {value} ({type(value).__name__})")
    
    # Look at underlying data
    underlying = data.get('underlying', {})
    if underlying:
        print(f"\n📊 UNDERLYING fields:")
        for key, value in underlying.items():
            print(f"  {key}: {value} ({type(value).__name__})")
    
    return True

if __name__ == "__main__":
    debug_schwab_fields()