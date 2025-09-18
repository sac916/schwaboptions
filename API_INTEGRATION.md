# Schwab API Integration Guide

## 📡 **API Overview**

**API Provider**: Charles Schwab
**Library**: `schwabdev==2.5.1`
**Authentication**: OAuth 2.0 with seamless web-based flow
**Data Type**: Real-time & historical options market data
**Rate Limits**: 120 calls per minute (standard tier)
**Status**: ✅ **Phase 3 Complete** - Enhanced client with historical analysis system  

---

## 🔑 **Authentication Setup**

### **Requirements**:
1. **Schwab Developer Account** - Register at developer.schwab.com
2. **API Application** - Create new app in Schwab developer portal
3. **API Credentials** - Obtain API Key and Secret

### **Environment Configuration**:
```bash
# Create .env file in project root
API_KEY=your_schwab_api_key_here
API_SECRET=your_schwab_api_secret_here
```

### **Enhanced Authentication Flow** (Phase 3):
```python
# NEW: Seamless web-based authentication (data/enhanced_schwab_client.py)
from data.enhanced_schwab_client import enhanced_schwab_client

# Check authentication status
status = enhanced_schwab_client.get_auth_status()
print(f"Authenticated: {status['authenticated']}")

# Get authorization URL for web-based login
auth_url = enhanced_schwab_client.get_authorization_url()
print(f"Login at: {auth_url}")

# Process callback after user completes OAuth
success = enhanced_schwab_client.process_callback_url(callback_url)
```

---

## 📊 **Data Sources & Endpoints**

### **Primary Endpoints Used**:
- **`get_option_chain(symbol)`** - Complete options chain data (real-time)
- **Historical Data Collection** - Daily snapshot automation (Phase 3)
- **`get_quotes(symbols)`** - Real-time stock quotes for underlying prices

### **Data Retrieved**:
```json
{
  "underlying": {
    "symbol": "SPY",
    "last": 445.67,
    "mark": 445.68
  },
  "callExpDateMap": {
    "2024-01-19:7": {
      "440.0": [{
        "strikePrice": 440.0,
        "bid": 6.15,
        "ask": 6.25,
        "last": 6.20,
        "mark": 6.20,
        "volume": 1250,
        "openInterest": 3420,
        "delta": 0.6543,
        "gamma": 0.0234,
        "theta": -0.1234,
        "vega": 0.4567,
        "impliedVolatility": 0.2345,
        "expirationDate": 1705708800000
      }]
    }
  },
  "putExpDateMap": { /* Similar structure for puts */ }
}
```

### **Additional Endpoints Available** (not currently used):
- `get_quotes(symbols)` - Real-time stock quotes
- `get_price_history(symbol, **kwargs)` - Historical price data
- `get_market_hours(markets)` - Market hours and holidays

---

## ⚙️ **Client Implementation**

### **Enhanced Client Features** (`data/enhanced_schwab_client.py`) - Phase 3:

```python
class EnhancedSchwabClient:
    """Phase 3: Web-friendly Schwab API client with seamless authentication"""

    def get_auth_status(self) -> Dict[str, Any]:
        """Get detailed authentication status with expiry info"""

    def get_authorization_url(self) -> str:
        """Get OAuth authorization URL for web-based login"""

    def process_callback_url(self, callback_url: str) -> bool:
        """Process OAuth callback and complete authentication"""

    def get_option_chain(self, symbol: str) -> Optional[Dict]:
        """Get option chain with enhanced error handling"""

    def get_quotes(self, symbols: List[str]) -> Optional[Dict]:
        """Get real-time quotes for underlying prices"""
```

### **Phase 3 Key Features**:
- **Seamless Web Authentication** - No terminal windows or manual token management
- **Real-time Auth Status** - Live authentication monitoring with expiry warnings
- **Historical Data Integration** - Automated daily snapshot collection
- **Enhanced Error Handling** - Comprehensive exception management with recovery
- **Connection Monitoring** - Real-time API status tracking with UI integration
- **Rate Limit Management** - Built-in request throttling with intelligent backoff

---

## 🔄 **Data Processing Pipeline**

### **Phase 3 Processing Flow**:
```
Schwab API → Raw JSON → OptionsProcessor → Enhanced DataFrame → Visualizations
                    ↓
            Historical Collector → Daily Snapshots → Time-Series Analysis
                    ↓
            Pattern Recognition → Position Evolution → Multi-Day Analysis
```

### **OptionsProcessor Features** (`data/processors.py`):

#### **Basic Metrics Calculation**:
- **Days to Expiration (DTE)** - Calendar days until option expiry
- **Volume/OI Ratio** - Trading volume vs open interest
- **Total Premium** - Volume × Mark × 100 (total dollar volume)
- **Moneyness** - Distance from strike to underlying price

#### **Advanced Metrics (100+ Parameters)**:
- **Unusual Activity Score** - Multi-factor unusual activity detection
- **Flow Direction** - Bullish/Bearish/Neutral classification
- **Liquidity Score** - Based on bid-ask spread and volume
- **Support/Resistance Score** - Strike-level S/R strength

### **Data Enhancement Process**:
```python
def parse_option_chain(json_data: Dict) -> pd.DataFrame:
    # 1. Extract calls and puts from nested JSON
    # 2. Flatten into DataFrame structure
    # 3. Calculate basic metrics (DTE, V/OI, Premium, Moneyness)
    # 4. Calculate advanced metrics (Unusual Score, Flow Direction)
    # 5. Format for visualization
    # 6. Sort by unusual activity score
    return enhanced_dataframe
```

---

## ⚡ **Real-time Data Management**

### **Update Intervals**:
- **Fast Updates**: 1 second (for active trading)
- **Medium Updates**: 5 seconds (for monitoring)
- **Slow Updates**: 30 seconds (for background analysis)

### **Phase 3 Data Management**:
- **Client-side Caching** - Prevent redundant API calls
- **Session State** - Maintain data across user interactions
- **Historical Database** - Comprehensive daily snapshot storage (JSON-based)
- **Time-Series Analysis** - Multi-day pattern recognition and position tracking
- **Live/Historical Toggle** - Smart mode switching based on market conditions

### **Data Freshness Indicators**:
```python
# Status tracking in UI
{
    "api_status": "Connected/Disconnected",
    "last_update": "HH:MM:SS timestamp",
    "data_count": "Number of contracts loaded",
    "update_interval": "Current refresh rate"
}
```

---

## 🚦 **Rate Limiting & Performance**

### **Schwab API Limits**:
- **Standard Tier**: 120 calls per minute
- **Premium Tier**: Higher limits available (contact Schwab)
- **Burst Capacity**: Short-term higher rates allowed

### **Our Rate Management**:
- **Request Throttling** - Built-in delays between calls
- **Intelligent Caching** - Avoid redundant requests
- **Batch Processing** - Group multiple operations when possible
- **Error Backoff** - Exponential backoff on rate limit errors

### **Performance Optimizations**:
- **Data Compression** - Efficient DataFrame storage
- **Selective Updates** - Only update changed data
- **Background Processing** - Non-blocking API calls
- **Connection Pooling** - Reuse HTTP connections

---

## 🛡️ **Error Handling & Resilience**

### **Common Error Scenarios**:

#### **Authentication Errors**:
- **Invalid Credentials** - Check API_KEY/API_SECRET
- **Token Expiration** - Automatic re-authentication
- **Permission Denied** - Verify account permissions

#### **API Errors**:
- **Rate Limit Exceeded** - Automatic backoff and retry
- **Invalid Symbol** - User-friendly error messages
- **Market Closed** - Graceful degradation with cached data
- **Network Timeouts** - Retry logic with exponential backoff

#### **Data Errors**:
- **Malformed Response** - Defensive parsing with fallbacks
- **Missing Fields** - Default values and validation
- **Empty Option Chain** - Handle symbols with no options

### **Error Recovery Strategies**:
```python
def get_option_chain_with_retry(symbol: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return self.client.get_option_chain(symbol)
        except RateLimitError:
            time.sleep(2 ** attempt)  # Exponential backoff
        except NetworkError:
            time.sleep(1)
        except AuthenticationError:
            self.authenticate()  # Re-authenticate and retry
    return None  # Failed after all retries
```

---

## 📈 **Market Data Quality**

### **Data Accuracy**:
- **Real-time Quotes** - Live market data during trading hours
- **Options Chains** - Complete strike/expiration matrix
- **Greeks Calculation** - Schwab's proprietary models
- **Volume/OI Data** - Real-time trading activity

### **Market Hours Impact**:
- **Trading Hours** (9:30 AM - 4:00 PM ET): Full real-time data
- **Extended Hours** (4:00 AM - 9:30 AM, 4:00 PM - 8:00 PM ET): Limited data
- **After Hours**: Last known values with staleness indicators
- **Weekends/Holidays**: Cached data with clear timestamps

### **Data Validation**:
- **Sanity Checks** - Validate price ranges and relationships
- **Consistency Verification** - Cross-reference related fields
- **Outlier Detection** - Flag suspicious data points
- **Staleness Monitoring** - Track data age and freshness

---

## 🔧 **Configuration & Customization**

### **Configuration Options** (`config.py`):
```python
# API Configuration
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Update Intervals
UPDATE_INTERVALS = {
    "fast": 1000,      # 1 second
    "medium": 5000,    # 5 seconds  
    "slow": 30000      # 30 seconds
}

# Default Parameters
DEFAULT_TICKERS = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA"]
```

### **Module-Specific Settings**:
- **Options Chain**: Volume filters, unusual activity thresholds
- **IV Surface**: Historical data retention, surface resolution
- **Flow Scanner**: Parameter weights, alert thresholds
- **Intraday Charts**: Update frequency, chart history length

---

## 🧪 **Testing & Validation**

### **API Testing**:
```python
# Test API connectivity
def test_api_connection():
    client = SchwabClient()
    assert client.authenticate() == True
    assert client.is_authenticated() == True

# Test data retrieval
def test_option_chain_retrieval():
    client = SchwabClient()
    data = client.get_option_chain("SPY")
    assert data is not None
    assert 'callExpDateMap' in data
    assert 'putExpDateMap' in data
```

### **Data Quality Validation**:
- **Schema Validation** - Ensure expected fields are present
- **Range Checks** - Validate numeric ranges (0 < IV < 5, etc.)
- **Relationship Checks** - Bid ≤ Mark ≤ Ask consistency
- **Historical Comparison** - Flag dramatic changes from previous values

### **Performance Testing**:
- **Response Time Monitoring** - Track API response latency
- **Throughput Testing** - Multiple concurrent requests
- **Memory Usage** - Monitor memory consumption with large datasets
- **Error Rate Tracking** - Monitor API error frequencies

---

## 🚀 **Future Enhancements**

### **Planned API Improvements**:

#### **WebSocket Integration**:
- **Real-time Streaming** - Replace polling with push updates
- **Lower Latency** - Reduce data delays for active trading
- **Bandwidth Efficiency** - Only send changed data

#### **Multi-Symbol Support**:
- **Batch Requests** - Request multiple symbols simultaneously
- **Portfolio Tracking** - Monitor personal positions
- **Watchlist Management** - Track favorite symbols

#### **✅ Historical Data Integration (Phase 3 Complete)**:
- **Daily Snapshot System** - Automated comprehensive data collection (`collect_daily_data.py`)
- **Time-Series Database** - JSON-based storage with pattern recognition
- **Position Evolution Tracking** - ConvexValue-style gamma evolution analysis
- **Multi-Day Flow Analysis** - Unusual Whales-style flow tracking
- **Pattern Recognition** - Whale activity, sweep patterns, position builds
- **Historical Collector** - Complete system in `data/historical_collector.py`

#### **Advanced Analytics**:
- **Real-time Greeks** - Calculate Greeks from live prices
- **Implied Forward Curves** - Extract market expectations
- **Cross-Asset Analysis** - Correlations with underlying movements

---

## 📋 **Troubleshooting Guide**

### **Common Issues & Solutions**:

#### **Authentication Problems**:
```bash
# Issue: "API credentials not found"
# Solution: Check .env file exists and has correct format
cat .env
# Should show:
# API_KEY=your_key_here
# API_SECRET=your_secret_here
```

#### **No Data Returned**:
```python
# Issue: Empty or None response from API
# Possible causes:
1. Invalid ticker symbol (use uppercase: 'SPY' not 'spy')
2. Symbol has no options (try major ETFs/stocks)
3. Market closed (try during trading hours)
4. API rate limit exceeded (wait and retry)
```

#### **Performance Issues**:
```python
# Issue: Slow loading or timeouts
# Solutions:
1. Reduce update frequency (use 'slow' interval)
2. Filter for specific strikes/expirations
3. Clear browser cache and restart application
4. Check network connectivity
```

#### **Data Quality Issues**:
```python
# Issue: Suspicious or missing data
# Solutions:
1. Refresh data during active trading hours
2. Compare with other data sources
3. Check Schwab API status page
4. Verify symbol has active options market
```

---

## 📚 **Additional Resources**

### **Schwab Developer Resources**:
- **Developer Portal**: https://developer.schwab.com/
- **API Documentation**: Full endpoint reference and examples
- **Rate Limit Guidelines**: Current limits and upgrade options
- **Status Page**: Real-time API health monitoring

### **schwabdev Library**:
- **GitHub Repository**: Source code and issue tracking
- **PyPI Package**: Installation and version information
- **Documentation**: Library-specific usage examples

### **Phase 3 Implementation**:
- **enhanced_schwab_client.py**: Seamless web-based authentication client
- **historical_collector.py**: Comprehensive daily snapshot collection system
- **processors.py**: Data transformation pipeline with historical analysis
- **config.py**: API configuration and settings
- **collect_daily_data.py**: Automated data collection script
- **schwab_client.py**: Legacy client (Phase 1-2 compatibility)

---

**📅 Last Updated**: September 16, 2025
**📍 API Version**: schwabdev 2.5.1
**🔗 Schwab API**: Real-time + historical market data
**⚡ Status**: ✅ **Phase 3 Complete** - Production-ready with 11 advanced modules

---

## 🎉 **Phase 3 Integration Complete**

### **Enhanced Authentication System**:
- ✅ **Seamless Web-Based OAuth** - No terminal complexity
- ✅ **Real-time Status Monitoring** - Live auth status with expiry warnings
- ✅ **Integrated UI Components** - Authentication modal and status indicators

### **Historical Data Infrastructure**:
- ✅ **Daily Snapshot Collection** - Automated comprehensive data gathering
- ✅ **Time-Series Analysis Engine** - Multi-day pattern recognition
- ✅ **Position Evolution Tracking** - ConvexValue-style analysis
- ✅ **Multi-Day Flow Analysis** - Unusual Whales-style tracking

### **Advanced Analytics Capabilities**:
- ✅ **Pattern Recognition** - Whale activity, sweep patterns, position builds
- ✅ **Unusual Activity Detection** - Multi-timeframe analysis
- ✅ **Historical Context** - Meaningful analysis during low-volume periods
- ✅ **Live/Historical Integration** - Smart mode switching in all modules

**Ready for Phase 4**: Advanced AI Integration & Machine Learning Pattern Recognition