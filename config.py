"""
Configuration settings for the Schwab Options Dashboard
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# App Configuration
APP_HOST = "127.0.0.1"
APP_PORT = 8055
DEBUG_MODE = True

# Dashboard Theme
THEME_CONFIG = {
    "background_color": "#0e1117",
    "paper_color": "#1e2130", 
    "text_color": "#ffffff",
    "primary_color": "#00d4aa",
    "secondary_color": "#ff6b6b",
    "accent_color": "#4dabf7"
}

# Module Configuration
MODULES = [
    # Phase 1 - Core (COMPLETED)
    {"id": "options_chain", "name": "Options Chain", "description": "Enhanced options chain analysis"},
    
    # Phase 2 - Essential Visualizations (COMPLETED)
    {"id": "iv_surface", "name": "IV Surface", "description": "Implied volatility term structure"},
    {"id": "options_heatmap", "name": "Options Heatmap", "description": "Visual options chain heatmap"},
    {"id": "flow_scanner", "name": "Flow Scanner", "description": "Live options flow with 100+ parameters"},
    {"id": "strike_analysis", "name": "Strike Analysis", "description": "Option levels by strike with S/R"},
    {"id": "intraday_charts", "name": "Intraday Charts", "description": "Live price charts with options overlay"},
    
    # Phase 3 - Advanced Analytics (IN PROGRESS)
    {"id": "dealer_surfaces", "name": "3D Dealer Surfaces", "description": "Advanced 3D dealer delta/gamma positioning"},
    {"id": "ridgeline", "name": "Ridgeline", "description": "Live ridgeline plots (joy module)"},
    {"id": "skew_analysis", "name": "Skew Analysis", "description": "Options skew term structure"},
    {"id": "implied_prob", "name": "Implied Probabilities", "description": "Market probability charts"},
    
    # Phase 4 - Integrations (FUTURE)
    {"id": "earnings_cal", "name": "Earnings Calendar", "description": "Upcoming earnings events"},
    {"id": "econ_cal", "name": "Economics Calendar", "description": "Economic events calendar"}
]

# Data Update Intervals (in milliseconds)
UPDATE_INTERVALS = {
    "fast": 1000,      # 1 second
    "medium": 5000,    # 5 seconds  
    "slow": 30000      # 30 seconds
}

# Default ticker symbols
DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]