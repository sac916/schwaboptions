#!/usr/bin/env python3
"""
Test the integrated authentication system
"""
from data.enhanced_schwab_client import enhanced_schwab_client
from components.auth_modal import create_auth_modal
import json

def test_auth_system():
    """Test all components of the integrated auth system"""
    print("🧪 Testing Integrated Authentication System")
    print("=" * 50)

    # Test 1: Auth status checking
    print("\n1. Testing auth status checking...")
    status = enhanced_schwab_client.get_auth_status()
    print(f"   ✅ Status: {json.dumps(status, indent=2, default=str)}")

    # Test 2: Quick auth check
    print("\n2. Testing quick auth check...")
    is_auth = enhanced_schwab_client.quick_auth_check()
    print(f"   ✅ Quick check result: {is_auth}")

    # Test 3: Generate auth URL (without triggering full flow)
    print("\n3. Testing auth URL generation...")
    try:
        auth_url = enhanced_schwab_client.get_authorization_url()
        print(f"   ✅ Auth URL: {auth_url[:80]}..." if auth_url else "   ❌ Failed to generate URL")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Component creation
    print("\n4. Testing component creation...")
    try:
        modal = create_auth_modal()
        print("   ✅ Auth modal created successfully")
    except Exception as e:
        print(f"   ❌ Modal creation failed: {e}")

    # Test 5: API test (if authenticated)
    print("\n5. Testing API connection...")
    try:
        if status["authenticated"]:
            quotes = enhanced_schwab_client.get_quotes(['SPY'])
            if quotes:
                spy_price = quotes.get('SPY', {}).get('lastPrice', 'N/A')
                print(f"   ✅ API working! SPY Price: ${spy_price}")
            else:
                print("   ❌ API call failed")
        else:
            print("   ⚠️  Skipped (not authenticated)")
    except Exception as e:
        print(f"   ❌ API test error: {e}")

    print(f"\n🎉 Integration test complete!")
    print(f"\n🚀 Ready to run: python integrated_dash_app.py")

if __name__ == "__main__":
    test_auth_system()