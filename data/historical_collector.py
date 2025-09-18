"""
Historical Options Data Collector - Comprehensive data storage and analysis
"""
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import logging

from .enhanced_schwab_client import enhanced_schwab_client

logger = logging.getLogger(__name__)

class HistoricalOptionsCollector:
    """Collect and store comprehensive historical options data"""

    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'historical')
        self.ensure_directories()

    def ensure_directories(self):
        """Create necessary directory structure"""
        directories = [
            'daily_options_snapshots',
            'unusual_activity',
            'position_evolution',
            'market_summary'
        ]

        for dir_name in directories:
            dir_path = os.path.join(self.base_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)

    def collect_daily_snapshot(self, symbol: str, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Collect comprehensive daily options snapshot for a symbol

        Args:
            symbol: Stock ticker symbol
            target_date: Date for snapshot (defaults to today)

        Returns:
            Dictionary containing complete options data
        """
        if target_date is None:
            target_date = date.today()

        try:
            logger.info(f"Collecting daily snapshot for {symbol} on {target_date}")

            # Get comprehensive options chain
            options_data = enhanced_schwab_client.get_option_chain(symbol)

            if not options_data:
                logger.error(f"No options data retrieved for {symbol}")
                return {}

            # Get current stock quote
            quotes = enhanced_schwab_client.get_quotes([symbol])
            underlying_price = None
            if quotes and symbol in quotes:
                underlying_price = quotes[symbol].get('lastPrice')

            # Process and structure the data
            snapshot = {
                'date': target_date.isoformat(),
                'symbol': symbol,
                'underlying_price': underlying_price,
                'timestamp': datetime.now().isoformat(),
                'options_chains': self._process_options_chains(options_data),
                'daily_stats': self._calculate_daily_stats(options_data),
                'unusual_activity': self._detect_unusual_activity(options_data)
            }

            # Save to file
            self._save_snapshot(symbol, target_date, snapshot)

            logger.info(f"Successfully collected snapshot for {symbol}: {len(snapshot.get('options_chains', []))} expirations")
            return snapshot

        except Exception as e:
            logger.error(f"Error collecting snapshot for {symbol}: {e}")
            return {}

    def _process_options_chains(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process raw options data into structured format"""
        processed_chains = []

        try:
            # Handle different possible data structures from Schwab API
            if 'callExpDateMap' in raw_data or 'putExpDateMap' in raw_data:
                call_map = raw_data.get('callExpDateMap', {})
                put_map = raw_data.get('putExpDateMap', {})

                # Get all unique expiration dates
                all_expirations = set(call_map.keys()) | set(put_map.keys())

                for expiry in all_expirations:
                    expiry_data = {
                        'expiry': expiry,
                        'calls': self._process_options_by_strike(call_map.get(expiry, {})),
                        'puts': self._process_options_by_strike(put_map.get(expiry, {}))
                    }
                    processed_chains.append(expiry_data)

        except Exception as e:
            logger.error(f"Error processing options chains: {e}")

        return processed_chains

    def _process_options_by_strike(self, strike_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process options data for a specific expiry by strikes"""
        options = []

        for strike_price, strike_info in strike_data.items():
            if isinstance(strike_info, list) and len(strike_info) > 0:
                option_info = strike_info[0]  # Take first item if it's a list

                option_data = {
                    'strike': float(strike_price),
                    'last_price': option_info.get('last', 0),
                    'bid': option_info.get('bid', 0),
                    'ask': option_info.get('ask', 0),
                    'volume': option_info.get('totalVolume', 0),
                    'open_interest': option_info.get('openInterest', 0),
                    'iv': option_info.get('volatility', 0),
                    'delta': option_info.get('delta', 0),
                    'gamma': option_info.get('gamma', 0),
                    'theta': option_info.get('theta', 0),
                    'vega': option_info.get('vega', 0),
                    'intrinsic_value': option_info.get('intrinsicValue', 0),
                    'time_value': option_info.get('timeValue', 0),
                    'in_the_money': option_info.get('inTheMoney', False)
                }

                # Calculate unusual activity score
                option_data['unusual_score'] = self._calculate_unusual_score(option_data)

                options.append(option_data)

        return sorted(options, key=lambda x: x['strike'])

    def _calculate_unusual_score(self, option_data: Dict[str, Any]) -> float:
        """Calculate unusual activity score for an option"""
        try:
            volume = option_data.get('volume', 0)
            oi = option_data.get('open_interest', 1)  # Avoid division by zero

            # Simple scoring algorithm (can be enhanced)
            volume_score = min(volume / 1000, 5)  # Cap at 5
            oi_ratio_score = min(volume / oi if oi > 0 else 0, 3)  # Cap at 3

            return round(volume_score + oi_ratio_score, 2)

        except:
            return 0.0

    def _calculate_daily_stats(self, options_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate daily market statistics"""
        stats = {
            'total_call_volume': 0,
            'total_put_volume': 0,
            'total_call_oi': 0,
            'total_put_oi': 0,
            'put_call_volume_ratio': 0,
            'put_call_oi_ratio': 0,
            'most_active_strikes': [],
            'highest_iv_options': [],
            'unusual_activity_count': 0
        }

        try:
            call_map = options_data.get('callExpDateMap', {})
            put_map = options_data.get('putExpDateMap', {})

            # Calculate totals
            for expiry_data in call_map.values():
                for strike_data in expiry_data.values():
                    if isinstance(strike_data, list) and len(strike_data) > 0:
                        option = strike_data[0]
                        stats['total_call_volume'] += option.get('totalVolume', 0)
                        stats['total_call_oi'] += option.get('openInterest', 0)

            for expiry_data in put_map.values():
                for strike_data in expiry_data.values():
                    if isinstance(strike_data, list) and len(strike_data) > 0:
                        option = strike_data[0]
                        stats['total_put_volume'] += option.get('totalVolume', 0)
                        stats['total_put_oi'] += option.get('openInterest', 0)

            # Calculate ratios
            if stats['total_call_volume'] > 0:
                stats['put_call_volume_ratio'] = round(stats['total_put_volume'] / stats['total_call_volume'], 3)

            if stats['total_call_oi'] > 0:
                stats['put_call_oi_ratio'] = round(stats['total_put_oi'] / stats['total_call_oi'], 3)

        except Exception as e:
            logger.error(f"Error calculating daily stats: {e}")

        return stats

    def _detect_unusual_activity(self, options_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect unusual options activity"""
        unusual_flows = []

        try:
            # Define thresholds for unusual activity
            min_volume = 1000
            min_unusual_score = 3.0

            call_map = options_data.get('callExpDateMap', {})
            put_map = options_data.get('putExpDateMap', {})

            # Check calls
            for expiry, strikes in call_map.items():
                for strike, strike_data in strikes.items():
                    if isinstance(strike_data, list) and len(strike_data) > 0:
                        option = strike_data[0]
                        volume = option.get('totalVolume', 0)

                        if volume >= min_volume:
                            unusual_score = self._calculate_unusual_score({
                                'volume': volume,
                                'open_interest': option.get('openInterest', 0)
                            })

                            if unusual_score >= min_unusual_score:
                                unusual_flows.append({
                                    'type': 'CALL',
                                    'strike': float(strike),
                                    'expiry': expiry,
                                    'volume': volume,
                                    'open_interest': option.get('openInterest', 0),
                                    'last_price': option.get('last', 0),
                                    'unusual_score': unusual_score
                                })

            # Check puts (similar logic)
            for expiry, strikes in put_map.items():
                for strike, strike_data in strikes.items():
                    if isinstance(strike_data, list) and len(strike_data) > 0:
                        option = strike_data[0]
                        volume = option.get('totalVolume', 0)

                        if volume >= min_volume:
                            unusual_score = self._calculate_unusual_score({
                                'volume': volume,
                                'open_interest': option.get('openInterest', 0)
                            })

                            if unusual_score >= min_unusual_score:
                                unusual_flows.append({
                                    'type': 'PUT',
                                    'strike': float(strike),
                                    'expiry': expiry,
                                    'volume': volume,
                                    'open_interest': option.get('openInterest', 0),
                                    'last_price': option.get('last', 0),
                                    'unusual_score': unusual_score
                                })

            # Sort by unusual score
            unusual_flows.sort(key=lambda x: x['unusual_score'], reverse=True)

        except Exception as e:
            logger.error(f"Error detecting unusual activity: {e}")

        return unusual_flows[:50]  # Return top 50 unusual activities

    def _save_snapshot(self, symbol: str, target_date: date, snapshot: Dict[str, Any]):
        """Save snapshot to file"""
        try:
            # Create symbol directory
            symbol_dir = os.path.join(self.base_path, 'daily_options_snapshots', symbol)
            os.makedirs(symbol_dir, exist_ok=True)

            # Save main snapshot
            filename = f"{target_date.isoformat()}.json"
            filepath = os.path.join(symbol_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=2, default=str)

            # Save unusual activity separately
            if snapshot.get('unusual_activity'):
                unusual_filename = f"{target_date.isoformat()}_unusual.json"
                unusual_filepath = os.path.join(self.base_path, 'unusual_activity', unusual_filename)

                unusual_data = {
                    'date': target_date.isoformat(),
                    'symbol': symbol,
                    'unusual_flows': snapshot['unusual_activity']
                }

                with open(unusual_filepath, 'w') as f:
                    json.dump(unusual_data, f, indent=2, default=str)

            logger.info(f"Saved snapshot to {filepath}")

        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

    def collect_multiple_symbols(self, symbols: List[str], target_date: Optional[date] = None) -> Dict[str, Any]:
        """Collect snapshots for multiple symbols"""
        results = {}

        for symbol in symbols:
            try:
                snapshot = self.collect_daily_snapshot(symbol, target_date)
                results[symbol] = snapshot
                logger.info(f"Completed {symbol}")
            except Exception as e:
                logger.error(f"Failed to collect {symbol}: {e}")
                results[symbol] = None

        return results

    def load_historical_snapshot(self, symbol: str, target_date: date) -> Optional[Dict[str, Any]]:
        """Load a historical snapshot from storage"""
        try:
            filepath = os.path.join(
                self.base_path,
                'daily_options_snapshots',
                symbol,
                f"{target_date.isoformat()}.json"
            )

            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)

        except Exception as e:
            logger.error(f"Error loading snapshot for {symbol} on {target_date}: {e}")

        return None

    def get_available_dates(self, symbol: str) -> List[date]:
        """Get list of available dates for a symbol"""
        try:
            symbol_dir = os.path.join(self.base_path, 'daily_options_snapshots', symbol)
            if not os.path.exists(symbol_dir):
                return []

            dates = []
            for filename in os.listdir(symbol_dir):
                if filename.endswith('.json'):
                    date_str = filename.replace('.json', '')
                    try:
                        dates.append(date.fromisoformat(date_str))
                    except ValueError:
                        continue

            return sorted(dates, reverse=True)

        except Exception as e:
            logger.error(f"Error getting available dates for {symbol}: {e}")
            return []

# Global collector instance
historical_collector = HistoricalOptionsCollector()