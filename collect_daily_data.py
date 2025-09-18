#!/usr/bin/env python3
"""
Daily Options Data Collection Script
Automatically collect comprehensive options data for historical analysis
"""
import sys
import os
from datetime import date, datetime
import logging
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.historical_collector import historical_collector
from data.enhanced_schwab_client import enhanced_schwab_client
from config import DEFAULT_TICKERS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def collect_today_data(symbols: List[str] = None) -> dict:
    """
    Collect today's options data for all symbols

    Args:
        symbols: List of symbols to collect (defaults to DEFAULT_TICKERS)

    Returns:
        Dictionary with collection results
    """
    if symbols is None:
        symbols = DEFAULT_TICKERS

    today = date.today()
    logger.info(f"Starting daily data collection for {today}")

    results = {
        'date': today.isoformat(),
        'start_time': datetime.now().isoformat(),
        'symbols_requested': len(symbols),
        'symbols_successful': 0,
        'symbols_failed': 0,
        'results': {}
    }

    # Check authentication first
    auth_status = enhanced_schwab_client.get_auth_status()
    if not auth_status.get('authenticated'):
        logger.error("Not authenticated with Schwab API - cannot collect data")
        results['error'] = 'Not authenticated'
        return results

    logger.info(f"Authenticated successfully - collecting data for {len(symbols)} symbols")

    # Collect data for each symbol
    for symbol in symbols:
        try:
            logger.info(f"Collecting data for {symbol}...")

            snapshot = historical_collector.collect_daily_snapshot(symbol, today)

            if snapshot and 'error' not in snapshot:
                results['symbols_successful'] += 1
                results['results'][symbol] = {
                    'status': 'success',
                    'chains_count': len(snapshot.get('options_chains', [])),
                    'unusual_count': len(snapshot.get('unusual_activity', [])),
                    'total_volume': (
                        snapshot.get('daily_stats', {}).get('total_call_volume', 0) +
                        snapshot.get('daily_stats', {}).get('total_put_volume', 0)
                    )
                }
                logger.info(f"✅ {symbol}: {results['results'][symbol]['chains_count']} chains, "
                          f"{results['results'][symbol]['unusual_count']} unusual activities")
            else:
                results['symbols_failed'] += 1
                results['results'][symbol] = {
                    'status': 'failed',
                    'error': snapshot.get('error', 'Unknown error') if snapshot else 'No data returned'
                }
                logger.error(f"❌ {symbol}: {results['results'][symbol]['error']}")

        except Exception as e:
            results['symbols_failed'] += 1
            results['results'][symbol] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ {symbol}: Exception - {str(e)}")

    results['end_time'] = datetime.now().isoformat()
    duration = datetime.fromisoformat(results['end_time']) - datetime.fromisoformat(results['start_time'])
    results['duration_seconds'] = duration.total_seconds()

    logger.info(f"Collection complete: {results['symbols_successful']} successful, "
               f"{results['symbols_failed']} failed in {results['duration_seconds']:.1f}s")

    return results

def create_collection_summary(results: dict):
    """Create a human-readable collection summary"""
    print(f"\n📊 Daily Collection Summary - {results['date']}")
    print("=" * 50)
    print(f"⏱️  Duration: {results['duration_seconds']:.1f} seconds")
    print(f"📈 Successful: {results['symbols_successful']}/{results['symbols_requested']}")
    print(f"❌ Failed: {results['symbols_failed']}/{results['symbols_requested']}")

    if results['symbols_successful'] > 0:
        print(f"\n✅ Successfully collected:")
        for symbol, data in results['results'].items():
            if data['status'] == 'success':
                print(f"   {symbol}: {data['chains_count']} chains, "
                      f"{data['unusual_count']} unusual, "
                      f"{data['total_volume']:,} volume")

    if results['symbols_failed'] > 0:
        print(f"\n❌ Failed symbols:")
        for symbol, data in results['results'].items():
            if data['status'] == 'failed':
                print(f"   {symbol}: {data['error']}")

def main():
    """Main collection function"""
    print("🚀 SchwaOptions Daily Data Collection")

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Collect data
    results = collect_today_data()

    # Show summary
    create_collection_summary(results)

    # Save results log
    import json
    results_file = f"logs/collection_{results['date']}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📁 Results saved to: {results_file}")

    # Return exit code based on success rate
    success_rate = results['symbols_successful'] / results['symbols_requested']
    if success_rate >= 0.8:  # 80% success rate
        print("🎉 Collection successful!")
        return 0
    elif success_rate >= 0.5:  # 50% success rate
        print("⚠️  Collection partial success")
        return 1
    else:
        print("❌ Collection mostly failed")
        return 2

if __name__ == "__main__":
    sys.exit(main())