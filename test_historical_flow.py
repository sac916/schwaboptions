#!/usr/bin/env python3
"""
Test the enhanced Flow Scanner with historical capabilities
"""
import sys
import os
from datetime import date, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.flow_scanner import flow_scanner_module
from data.historical_collector import historical_collector

def test_historical_analysis():
    """Test the historical analysis functionality"""
    print("🧪 Testing Enhanced Flow Scanner")
    print("=" * 40)

    symbol = "SPY"
    timeframe = 7  # 1 week

    print(f"1. Testing historical data availability for {symbol}...")
    available_dates = historical_collector.get_available_dates(symbol)
    print(f"   Available dates: {len(available_dates)}")

    if not available_dates:
        print("   ⚠️  No historical data available - run data collection first")
        print("   💡 To collect data: python collect_daily_data.py")
        return

    print(f"   ✅ Found data from {available_dates[0]} to {available_dates[-1]}")

    print(f"\n2. Testing historical flow analysis...")
    try:
        analysis = flow_scanner_module.analyze_historical_flow(symbol, timeframe)

        if 'error' in analysis:
            print(f"   ❌ Error: {analysis['error']}")
            return

        print(f"   ✅ Analysis completed for {analysis['timeframe']}")
        print(f"   📊 Results:")
        print(f"      - Unusual patterns: {len(analysis.get('unusual_patterns', []))}")
        print(f"      - Position builds: {len(analysis.get('position_builds', []))}")
        print(f"      - Whale activity: {len(analysis.get('whale_activity', []))}")
        print(f"      - Sweep patterns: {len(analysis.get('sweep_patterns', []))}")
        print(f"      - Daily summaries: {len(analysis.get('daily_summary', []))}")

        # Show top patterns
        if analysis.get('unusual_patterns'):
            print(f"\n   🔍 Top unusual patterns:")
            for i, pattern in enumerate(analysis['unusual_patterns'][:3]):
                if 'error' not in pattern:
                    print(f"      {i+1}. {pattern['strike']}{pattern['type'][0]} - "
                          f"{pattern['days_active']} days, "
                          f"{pattern['total_volume']:,} volume")

        if analysis.get('position_builds'):
            print(f"\n   🏗️  Top position builds:")
            for i, build in enumerate(analysis['position_builds'][:3]):
                if 'error' not in build:
                    print(f"      {i+1}. {build['contract']} - "
                          f"{build['build_direction']}, "
                          f"{build['total_oi_change']:+,} OI change")

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return

    print(f"\n✅ Historical Flow Scanner test completed!")

def test_data_collection():
    """Test data collection for a single symbol"""
    print("\n🧪 Testing Data Collection")
    print("=" * 40)

    symbol = "SPY"
    target_date = date.today()

    print(f"Testing data collection for {symbol} on {target_date}...")

    try:
        snapshot = historical_collector.collect_daily_snapshot(symbol, target_date)

        if 'error' in snapshot:
            print(f"❌ Collection failed: {snapshot['error']}")
            return False

        print(f"✅ Collection successful!")
        print(f"   📊 Options chains: {len(snapshot.get('options_chains', []))}")
        print(f"   🔍 Unusual activities: {len(snapshot.get('unusual_activity', []))}")

        stats = snapshot.get('daily_stats', {})
        total_volume = stats.get('total_call_volume', 0) + stats.get('total_put_volume', 0)
        print(f"   📈 Total volume: {total_volume:,}")
        print(f"   📊 Put/Call ratio: {stats.get('put_call_volume_ratio', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ Collection exception: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Historical Options Analysis System")

    # Test data collection first
    collection_success = test_data_collection()

    if collection_success:
        # Test historical analysis
        test_historical_analysis()
    else:
        print("\n⚠️  Data collection failed - historical analysis test skipped")

    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    main()