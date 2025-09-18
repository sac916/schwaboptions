"""
Enhanced Schwab API client with web-friendly authentication flow
"""
import schwabdev as schwab
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging
import os
import json
from config import API_KEY, API_SECRET

logger = logging.getLogger(__name__)

class WebFriendlySchwabClient:
    """Enhanced Schwab API client with seamless web-based authentication"""

    def __init__(self):
        self.client = None
        self._authenticated = False
        self._auth_url = None
        self._token_expires = None
        self._last_check = None

    def get_tokens_file_path(self) -> str:
        """Get the path to the tokens file"""
        return os.path.join(os.path.dirname(__file__), '..', 'schwab_tokens.json')

    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status with detailed info"""
        tokens_file = self.get_tokens_file_path()

        status = {
            "authenticated": False,
            "token_exists": False,
            "token_expires": None,
            "expires_in_seconds": None,
            "needs_refresh": False,
            "error": None
        }

        try:
            # Check if token file exists
            if os.path.exists(tokens_file):
                status["token_exists"] = True

                # Try to read token info
                with open(tokens_file, 'r') as f:
                    token_data = json.load(f)

                if "access_token_issued" in token_data:
                    issued_time = datetime.fromisoformat(token_data["access_token_issued"].replace('Z', '+00:00'))
                    expires_in = token_data.get("token_dictionary", {}).get("expires_in", 1800)
                    expiry_time = issued_time + timedelta(seconds=expires_in)

                    status["token_expires"] = expiry_time.isoformat()
                    status["expires_in_seconds"] = (expiry_time - datetime.now(expiry_time.tzinfo)).total_seconds()

                    # Consider authenticated if token expires in more than 5 minutes
                    if status["expires_in_seconds"] > 300:
                        status["authenticated"] = True
                    else:
                        status["needs_refresh"] = True

        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Error checking auth status: {e}")

        return status

    def get_authorization_url(self) -> str:
        """Generate a fresh authorization URL without triggering the full OAuth flow"""
        try:
            if not API_KEY or not API_SECRET:
                raise ValueError("API credentials not found in environment")

            # Build the authorization URL manually
            base_url = "https://api.schwabapi.com/v1/oauth/authorize"
            callback_url = "https://127.0.0.1"

            auth_url = f"{base_url}?client_id={API_KEY}&redirect_uri={callback_url}"
            self._auth_url = auth_url

            logger.info("Generated fresh authorization URL")
            return auth_url

        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return None

    def process_callback_url(self, callback_url: str) -> Dict[str, Any]:
        """Process the callback URL and create tokens"""
        result = {
            "success": False,
            "message": "",
            "authenticated": False
        }

        try:
            if not callback_url or not callback_url.startswith("https://127.0.0.1"):
                result["message"] = "Invalid callback URL format"
                return result

            tokens_file = self.get_tokens_file_path()

            # Remove old token file if it exists
            if os.path.exists(tokens_file):
                os.remove(tokens_file)

            # Create a temporary client to process the callback
            temp_client = schwab.Client(
                app_key=API_KEY,
                app_secret=API_SECRET,
                callback_url="https://127.0.0.1",
                tokens_file=tokens_file,
                timeout=30
            )

            # Process the authorization callback
            temp_client._process_authorization_callback(callback_url)

            # Test the connection
            test_response = temp_client.quotes(['SPY'])
            if test_response.ok:
                self.client = temp_client
                self._authenticated = True
                result["success"] = True
                result["authenticated"] = True
                result["message"] = "Authentication successful! API connection verified."
                logger.info("Successfully processed callback URL and verified API connection")
            else:
                result["message"] = f"Token created but API test failed: {test_response.status_code}"

        except Exception as e:
            logger.error(f"Error processing callback URL: {e}")
            result["message"] = f"Authentication failed: {str(e)}"

        return result

    def quick_auth_check(self) -> bool:
        """Quick check if we're authenticated (uses cached status)"""
        now = datetime.now()

        # Only check every 30 seconds to avoid overhead
        if self._last_check and (now - self._last_check).seconds < 30:
            return self._authenticated

        status = self.get_auth_status()
        self._authenticated = status["authenticated"]
        self._last_check = now

        return self._authenticated

    def ensure_authenticated(self) -> bool:
        """Ensure client is authenticated, try to initialize if needed"""
        if self._authenticated and self.client:
            return True

        # Check if we have valid tokens
        status = self.get_auth_status()
        if not status["authenticated"]:
            return False

        # Try to initialize client with existing tokens
        try:
            tokens_file = self.get_tokens_file_path()
            self.client = schwab.Client(
                app_key=API_KEY,
                app_secret=API_SECRET,
                callback_url="https://127.0.0.1",
                tokens_file=tokens_file,
                timeout=10
            )
            self._authenticated = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            self._authenticated = False
            return False

    def get_option_chain(self, symbol: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Get option chain for a symbol"""
        if not self.ensure_authenticated():
            return None

        try:
            response = self.client.option_chains(symbol, **kwargs)
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
        if not self.ensure_authenticated():
            return None

        try:
            response = self.client.quotes(symbols)
            if response.ok:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")
            return None

# Global client instance
enhanced_schwab_client = WebFriendlySchwabClient()