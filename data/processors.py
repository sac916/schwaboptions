"""
Options data processing and calculations
Migrated and enhanced from original Streamlit app
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OptionsProcessor:
    """Enhanced options data processing with additional metrics"""
    
    @staticmethod
    def parse_option_chain(json_data: Dict[Any, Any]) -> pd.DataFrame:
        """
        Parse Schwab option chain JSON into enhanced DataFrame
        Enhanced version of original parse_option_chain function
        """
        if not json_data:
            return pd.DataFrame()
            
        contracts = []
        underlying_price = json_data.get('underlying', {}).get('last', 0)
        
        # Process calls
        for date_str, date_map in json_data.get('callExpDateMap', {}).items():
            for strike, strike_list in date_map.items():
                for contract_data in strike_list:
                    contract_data['type'] = 'CALL'
                    contract_data['date_str'] = date_str
                    contracts.append(contract_data)
        
        # Process puts  
        for date_str, date_map in json_data.get('putExpDateMap', {}).items():
            for strike, strike_list in date_map.items():
                for contract_data in strike_list:
                    contract_data['type'] = 'PUT'
                    contract_data['date_str'] = date_str
                    contracts.append(contract_data)
        
        if not contracts:
            return pd.DataFrame()
            
        df = pd.DataFrame(contracts)
        
        # Enhanced feature engineering
        df = OptionsProcessor._add_basic_metrics(df, underlying_price)
        df = OptionsProcessor._add_advanced_metrics(df, underlying_price)
        
        return OptionsProcessor._format_output(df)
    
    @staticmethod
    def _add_basic_metrics(df: pd.DataFrame, underlying_price: float) -> pd.DataFrame:
        """Add basic options metrics (from original app)"""
        
        # Map Schwab field names to our expected names
        field_mapping = {
            'totalVolume': 'volume',
            'putCall': 'type'
        }
        
        for schwab_field, our_field in field_mapping.items():
            if schwab_field in df.columns:
                df[our_field] = df[schwab_field]
        
        # Handle IV separately - Schwab returns it as percentage, we need decimal
        if 'volatility' in df.columns:
            df['impliedVolatility'] = pd.to_numeric(df['volatility'], errors='coerce') / 100.0
        
        # Convert types for calculation
        numeric_cols = ['strikePrice', 'bid', 'ask', 'last', 'mark', 'volume', 'openInterest', 
                        'delta', 'gamma', 'theta', 'vega', 'impliedVolatility']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Calculate Days to Expiration (DTE) - handle both ISO and millisecond formats
        try:
            # Try parsing as ISO format first (newer Schwab API format)
            df['expirationDate'] = pd.to_datetime(df['expirationDate'])
        except:
            try:
                # Fallback to milliseconds format (older format)
                df['expirationDate'] = pd.to_datetime(df['expirationDate'], unit='ms')
            except:
                # If both fail, set a default expiration date
                logger.warning("Could not parse expiration dates, using default")
                df['expirationDate'] = pd.to_datetime(datetime.now() + timedelta(days=30))
        
        # Ensure timezone consistency - convert to timezone-naive for calculations
        if df['expirationDate'].dt.tz is not None:
            df['expirationDate'] = df['expirationDate'].dt.tz_localize(None)
        
        df['DTE'] = (df['expirationDate'] - datetime.now()).dt.days
        
        # Volume / Open Interest Ratio
        df['V/OI'] = (df['volume'] / df['openInterest']).round(2).fillna(0)
        df['V/OI'] = df['V/OI'].replace(float('inf'), 0)
        
        # Total Premium
        df['Premium'] = (df['volume'] * df['mark'] * 100).astype(int)
        
        # Moneyness
        df['Moneyness'] = (underlying_price - df['strikePrice']).round(2)
        df.loc[df['type'] == 'PUT', 'Moneyness'] *= -1
        
        return df
    
    @staticmethod
    def _add_advanced_metrics(df: pd.DataFrame, underlying_price: float) -> pd.DataFrame:
        """Add advanced ConvexValue-style metrics"""
        
        # Unusual Activity Score (0-100)
        df['UnusualScore'] = 0
        
        # High V/OI ratio (>5x normal)
        df.loc[df['V/OI'] > 5, 'UnusualScore'] += 25
        
        # High volume relative to average
        avg_volume = df.groupby('type')['volume'].transform('median')
        df.loc[df['volume'] > (avg_volume * 3), 'UnusualScore'] += 25
        
        # Large premium trades
        premium_threshold = df['Premium'].quantile(0.9)
        df.loc[df['Premium'] > premium_threshold, 'UnusualScore'] += 25
        
        # Near-term high IV
        df.loc[(df['DTE'] <= 7) & (df['impliedVolatility'] > 0.5), 'UnusualScore'] += 25
        
        # Flow Direction (simplified)
        df['FlowDirection'] = 'Neutral'
        df.loc[(df['type'] == 'CALL') & (df['volume'] > df['openInterest']), 'FlowDirection'] = 'Bullish'
        df.loc[(df['type'] == 'PUT') & (df['volume'] > df['openInterest']), 'FlowDirection'] = 'Bearish'
        
        # Option Type Classification
        df['OptionType'] = 'ATM'
        df.loc[abs(df['Moneyness']) > underlying_price * 0.05, 'OptionType'] = 'OTM'
        df.loc[abs(df['Moneyness']) < underlying_price * 0.02, 'OptionType'] = 'ITM'
        
        # Bid-Ask Spread
        df['BidAskSpread'] = (df['ask'] - df['bid']).round(3)
        df['SpreadPct'] = ((df['BidAskSpread'] / df['mark']) * 100).round(2)
        
        return df
    
    @staticmethod
    def _format_output(df: pd.DataFrame) -> pd.DataFrame:
        """Format DataFrame for display"""
        
        display_cols = [
            'type', 'strikePrice', 'expirationDate', 'DTE', 'mark', 'volume', 
            'openInterest', 'V/OI', 'Premium', 'impliedVolatility', 'delta', 
            'gamma', 'theta', 'vega', 'Moneyness', 'UnusualScore', 'FlowDirection',
            'OptionType', 'BidAskSpread', 'SpreadPct'
        ]
        
        # Only keep columns that exist
        available_cols = [col for col in display_cols if col in df.columns]
        df = df[available_cols]
        
        # Rename columns for display
        rename_map = {
            'type': 'Type', 
            'strikePrice': 'Strike', 
            'expirationDate': 'Expiry',
            'mark': 'Mark', 
            'volume': 'Volume', 
            'openInterest': 'Open Int',
            'impliedVolatility': 'IV', 
            'delta': 'Delta', 
            'gamma': 'Gamma',
            'theta': 'Theta', 
            'vega': 'Vega',
            'BidAskSpread': 'Bid-Ask',
            'SpreadPct': 'Spread%'
        }
        
        df = df.rename(columns=rename_map)
        
        # Format expiry date
        if 'Expiry' in df.columns:
            df['Expiry'] = pd.to_datetime(df['Expiry']).dt.strftime('%Y-%m-%d')
        
        # Sort by unusual activity
        sort_column = 'UnusualScore' if 'UnusualScore' in df.columns else 'Premium'
        return df.sort_values(by=sort_column, ascending=False)

    @staticmethod
    def calculate_iv_surface(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate implied volatility surface data"""
        if df.empty:
            return {}
            
        # Group by expiration and strike for IV surface
        surface_data = df.groupby(['Expiry', 'Strike']).agg({
            'IV': 'first',
            'Volume': 'sum',
            'Type': 'first'
        }).reset_index()
        
        return {
            'strikes': surface_data['Strike'].unique(),
            'expirations': surface_data['Expiry'].unique(), 
            'iv_values': surface_data['IV'].values,
            'volumes': surface_data['Volume'].values
        }
    
    @staticmethod
    def detect_unusual_flow(df: pd.DataFrame, threshold: int = 50) -> pd.DataFrame:
        """Filter for unusual options activity"""
        if 'UnusualScore' not in df.columns:
            return df.head(0)  # Return empty with same columns
            
        return df[df['UnusualScore'] >= threshold].copy()