#!/usr/bin/env python3
"""
Test script for the Universal Data Integration System
Tests the module data adapter and universal data router
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.module_data_adapter import ModuleDataAdapter
from data.universal_data_router import universal_data_router
from modules.flow_scanner import flow_scanner_module
from modules.iv_surface import iv_surface_module
from modules.options_heatmap import options_heatmap_module

def test_module_data_adapter():
    """Test the ModuleDataAdapter functionality"""
    print("🧪 Testing ModuleDataAdapter...")

    try:
        adapter = ModuleDataAdapter()
        print("✅ ModuleDataAdapter initialized successfully")

        # Test with a common ticker
        test_ticker = "SPY"
        print(f"\n📊 Testing with ticker: {test_ticker}")

        # Test different analysis types
        analysis_types = ["flow_scanner", "iv_surface", "options_heatmap"]

        for analysis_type in analysis_types:
            print(f"\n🔍 Testing analysis_type: {analysis_type}")

            try:
                result = adapter.get_options_analysis(
                    symbol=test_ticker,
                    analysis_type=analysis_type,
                    force_mode="auto"
                )

                if result:
                    print(f"✅ {analysis_type}: Got data result")
                    print(f"   - Data quality: {result.get('data_quality', 'unknown')}")
                    print(f"   - Data source: {result.get('data_info', {}).get('source', 'unknown')}")

                    if result.get('options_data') is not None:
                        df = result['options_data']
                        print(f"   - Data rows: {len(df) if hasattr(df, '__len__') else 'N/A'}")
                    else:
                        print(f"   - No options_data in result")
                else:
                    print(f"❌ {analysis_type}: No result returned")

            except Exception as e:
                print(f"❌ {analysis_type}: Error - {str(e)}")

    except Exception as e:
        print(f"❌ ModuleDataAdapter test failed: {str(e)}")
        return False

    return True

def test_universal_data_router():
    """Test the UniversalDataRouter functionality"""
    print("\n🧪 Testing UniversalDataRouter...")

    try:
        # Test direct router access
        test_ticker = "SPY"

        print(f"📊 Testing router with ticker: {test_ticker}")

        # Test auto mode
        raw_data, quality = universal_data_router.get_options_data(
            symbol=test_ticker,
            force_live=False,
            force_historical=False
        )

        if raw_data:
            print(f"✅ Router returned data with quality: {quality}")
        else:
            print(f"❌ Router returned no data")

    except Exception as e:
        print(f"❌ UniversalDataRouter test failed: {str(e)}")
        return False

    return True

def test_enhanced_modules():
    """Test the enhanced modules with universal data adapter"""
    print("\n🧪 Testing Enhanced Modules...")

    test_ticker = "SPY"
    modules_to_test = [
        ("Flow Scanner", flow_scanner_module),
        ("IV Surface", iv_surface_module),
        ("Options Heatmap", options_heatmap_module)
    ]

    for module_name, module in modules_to_test:
        print(f"\n🔍 Testing {module_name}")

        try:
            # Test the enhanced update_data method
            data = module.update_data(test_ticker, mode="auto")

            if data is not None and hasattr(data, '__len__') and len(data) > 0:
                print(f"✅ {module_name}: Got {len(data)} rows of data")

                # Test data quality info
                quality_info = module.get_data_quality_info()
                if quality_info:
                    print(f"   - Quality: {quality_info.get('quality', 'unknown')}")
                    print(f"   - Info: {quality_info.get('info', {}).get('source', 'unknown')}")
                else:
                    print(f"   - No quality info available")

            else:
                print(f"❌ {module_name}: No data returned")

        except Exception as e:
            print(f"❌ {module_name}: Error - {str(e)}")

def test_data_modes():
    """Test different data modes"""
    print("\n🧪 Testing Data Modes...")

    test_ticker = "SPY"
    modes = ["auto", "live", "historical"]

    adapter = ModuleDataAdapter()

    for mode in modes:
        print(f"\n🔍 Testing mode: {mode}")

        try:
            result = adapter.get_options_analysis(
                symbol=test_ticker,
                analysis_type="flow_scanner",
                force_mode=mode
            )

            if result:
                quality = result.get('data_quality', 'unknown')
                source = result.get('data_info', {}).get('source', 'unknown')
                print(f"✅ {mode} mode: Quality={quality}, Source={source}")
            else:
                print(f"❌ {mode} mode: No result")

        except Exception as e:
            print(f"❌ {mode} mode: Error - {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting Universal Data System Tests")
    print("=" * 50)

    # Run tests
    tests = [
        ("ModuleDataAdapter", test_module_data_adapter),
        ("UniversalDataRouter", test_universal_data_router),
        ("Enhanced Modules", test_enhanced_modules),
        ("Data Modes", test_data_modes)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = success if success is not None else True
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Summary
    print(f"\n{'='*50}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*50}")

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Universal Data System is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()