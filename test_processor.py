#!/usr/bin/env python3
"""
Test the options processor standalone
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from data.schwab_client import schwab_client
from data.processors import OptionsProcessor

def test_processor():
    """Test the processor works correctly"""
    print("🧪 Testing Options Processor...")
    print("=" * 50)
    
    # Authenticate
    if not schwab_client.authenticate():
        print("❌ Authentication failed")
        return False
    
    # Get raw data
    raw_data = schwab_client.get_option_chain(
        symbol="TSLA",
        contractType="ALL",
        strikeCount=5,
        includeUnderlyingQuote=True,
        range="NTM",
        daysToExpiration=30
    )
    
    if not raw_data:
        print("❌ No raw data")
        return False
        
    print("✅ Raw data received")
    
    # Test processor
    try:
        df = OptionsProcessor.parse_option_chain(raw_data)
        print(f"✅ Processor success! {len(df)} rows processed")
        print(f"📊 Columns: {list(df.columns)}")
        return True
    except Exception as e:
        import traceback
        print(f"❌ Processor failed: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_processor()