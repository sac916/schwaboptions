#!/usr/bin/env python3
"""
Debug IV values from Schwab API
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from data.schwab_client import schwab_client
from data.processors import OptionsProcessor

def debug_iv_values():
    """Debug IV values to see what's wrong"""
    print("🔍 Debugging IV values from Schwab API...")
    print("=" * 60)
    
    # Authenticate
    if not schwab_client.authenticate():
        print("❌ Authentication failed")
        return False
    
    # Get raw data
    raw_data = schwab_client.get_option_chain(
        symbol="TSLA",
        contractType="ALL",
        strikeCount=10,  # Just a few for debugging
        includeUnderlyingQuote=True,
        range="NTM",
        daysToExpiration=30
    )
    
    if not raw_data:
        print("❌ No raw data")
        return False
    
    print("✅ Raw data received")
    
    # Look at first few contracts to see raw IV values
    call_dates = raw_data.get('callExpDateMap', {})
    if call_dates:
        first_date = list(call_dates.keys())[0]
        first_strike_data = call_dates[first_date]
        first_strike = list(first_strike_data.keys())[0]
        contracts = first_strike_data[first_strike]
        
        print(f"\n📊 RAW IV VALUES from first few contracts:")
        for i, contract in enumerate(contracts[:3]):
            iv_raw = contract.get('volatility', 'N/A')  # Schwab calls it 'volatility'
            print(f"  Contract {i+1}: volatility = {iv_raw} ({type(iv_raw)})")
    
    # Process data and see what happens
    df = OptionsProcessor.parse_option_chain(raw_data)
    if not df.empty:
        print(f"\n📈 PROCESSED IV VALUES:")
        iv_values = df['IV'].head(10)
        for i, iv in enumerate(iv_values):
            print(f"  Row {i+1}: IV = {iv:.4f} ({iv:.2%})")
        
        print(f"\n📊 IV STATISTICS:")
        print(f"  Min IV: {df['IV'].min():.4f} ({df['IV'].min():.2%})")
        print(f"  Max IV: {df['IV'].max():.4f} ({df['IV'].max():.2%})")  
        print(f"  Avg IV: {df['IV'].mean():.4f} ({df['IV'].mean():.2%})")
        print(f"  Median IV: {df['IV'].median():.4f} ({df['IV'].median():.2%})")
        
        return True
    else:
        print("❌ No processed data")
        return False

if __name__ == "__main__":
    debug_iv_values()