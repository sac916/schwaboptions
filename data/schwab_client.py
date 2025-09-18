"""
Enhanced Schwab API client for real-time options data with OAuth callback handling
"""
import schwabdev as schwab
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import os
from config import API_KEY, API_SECRET

logger = logging.getLogger(__name__)

class SchwabClient:
    """Enhanced Schwab API client with caching and error handling"""
    
    def __init__(self):
        self.client = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with Schwab API using OAuth flow with callback handling"""
        try:
            if not API_KEY or not API_SECRET:
                logger.error("API credentials not found in environment")
                return False
            
            # Token storage path
            tokens_file = os.path.join(os.path.dirname(__file__), '..', 'schwab_tokens.json')
            
            # Use OAuth callback URL without port (prevents login loops per Reddit solution)
            callback_url = "https://127.0.0.1"
            
            # Initialize client with manual OAuth callback handling (more reliable)
            self.client = schwab.Client(
                app_key=API_KEY,
                app_secret=API_SECRET,
                callback_url=callback_url,
                tokens_file=tokens_file,
                capture_callback=False,  # Disable auto-capture to avoid loops
                timeout=10
            )
            
            # This will handle the OAuth flow automatically
            # If token exists and is valid, it will use it
            # If not, it will prompt for authentication
            self._authenticated = True
            logger.info("Successfully authenticated with Schwab API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            logger.error("Make sure your Schwab app callback URL is set to: https://127.0.0.1")
            self._authenticated = False
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._authenticated and self.client is not None
    
    def get_option_chain(self, symbol: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """
        Get option chain for a symbol
        
        Args:
            symbol: Stock ticker symbol
            **kwargs: Additional parameters for API call
            
        Returns:
            Option chain data or None if error
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return None
                
        try:
            response = self.client.option_chains(symbol, **kwargs)  # Fixed method name
            logger.info(f"Option chain response status: {response.status_code}")
            
            if response.ok:
                data = response.json()
                logger.info(f"Option chain data keys: {list(data.keys()) if data else 'None'}")
                return data
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: list) -> Optional[Dict[Any, Any]]:
        """Get real-time quotes for multiple symbols"""
        if not self.is_authenticated():
            if not self.authenticate():
                return None
                
        try:
            response = self.client.quotes(symbols)  # Fixed method name
            if response.ok:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return None

# Global client instance
schwab_client = SchwabClient()