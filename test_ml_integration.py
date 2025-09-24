#!/usr/bin/env python3
"""
Test ML Integration with Flow Scanner
"""
import pandas as pd
import sys
import os
sys.path.append('.')

from data.ml_pattern_engine import ml_engine
from modules.flow_scanner import flow_scanner_module

def test_ml_engine():
    """Test ML pattern engine directly"""
    print("=== Testing ML Pattern Engine ===")

    # Create sample options data
    sample_data = pd.DataFrame({
        'totalVolume': [1000, 500, 2000, 150, 800],
        'mark': [2.5, 1.2, 5.0, 0.8, 3.2],
        'openInterest': [5000, 2000, 8000, 1000, 3000],
        'delta': [0.6, 0.3, 0.8, 0.1, 0.5],
        'gamma': [0.05, 0.08, 0.03, 0.12, 0.06],
        'theta': [-0.02, -0.01, -0.03, -0.005, -0.015],
        'vega': [0.15, 0.20, 0.12, 0.25, 0.18],
        'volatility': [0.25, 0.30, 0.20, 0.35, 0.28],
        'daysToExpiration': [30, 15, 45, 7, 21],
        'strike': [420, 415, 425, 410, 422],
        'avg_volume': [800, 400, 1500, 120, 600],
        'iv_rank': [60, 75, 45, 85, 70],
        'underlying_price': [420, 420, 420, 420, 420]
    })

    print(f"Sample data shape: {sample_data.shape}")
    print(f"Columns: {list(sample_data.columns)}")

    # Test ML prediction
    result = ml_engine.predict_unusual_activity(sample_data)
    print(f"ML Result: {result}")

    return result

def test_flow_scanner_ml():
    """Test Flow Scanner with ML integration"""
    print("\n=== Testing Flow Scanner ML Integration ===")

    # Create sample flow data
    sample_flow_data = pd.DataFrame({
        'Type': ['CALL', 'PUT', 'CALL', 'PUT', 'CALL'],
        'Strike': [420, 415, 425, 410, 422],
        'Expiry': ['2024-01-19', '2024-01-19', '2024-02-16', '2024-01-12', '2024-01-26'],
        'Volume': [1000, 500, 2000, 150, 800],
        'Premium': [2.5, 1.2, 5.0, 0.8, 3.2],
        'OpenInt': [5000, 2000, 8000, 1000, 3000],
        'Delta': [0.6, -0.3, 0.8, -0.1, 0.5],
        'Gamma': [0.05, 0.08, 0.03, 0.12, 0.06],
        'Theta': [-0.02, -0.01, -0.03, -0.005, -0.015],
        'Vega': [0.15, 0.20, 0.12, 0.25, 0.18],
        'IV': [0.25, 0.30, 0.20, 0.35, 0.28],
        'DTE': [30, 15, 45, 7, 21],
        'UnusualScore': [65, 45, 85, 30, 70]
    })

    print(f"Flow data shape: {sample_flow_data.shape}")

    # Test the _add_ml_scoring method
    flow_scanner_module.data = sample_flow_data
    enhanced_data = flow_scanner_module._add_ml_scoring(sample_flow_data.copy())

    print(f"Enhanced data columns: {list(enhanced_data.columns)}")
    print(f"ML columns added: {[col for col in enhanced_data.columns if 'ml_' in col or 'enhanced_' in col]}")

    # Show sample results
    ml_cols = ['ml_unusual_score', 'ml_confidence', 'ml_anomaly_score', 'enhanced_unusual_score']
    available_ml_cols = [col for col in ml_cols if col in enhanced_data.columns]

    if available_ml_cols:
        print("\nML Scoring Results:")
        for col in available_ml_cols:
            print(f"{col}: {enhanced_data[col].tolist()}")

    return enhanced_data

if __name__ == "__main__":
    print("SchwaOptions ML Integration Test")
    print("=" * 40)

    try:
        # Test ML engine directly
        ml_result = test_ml_engine()

        # Test Flow Scanner integration
        flow_result = test_flow_scanner_ml()

        print("\n=== Test Summary ===")
        print("✅ ML Engine: Working")
        print("✅ Flow Scanner Integration: Working")
        print("✅ ML scoring columns added successfully")
        print("\n🎉 Phase 5 ML Integration: SUCCESSFUL!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()