import streamlit as st
import pandas as pd
from datetime import datetime
import schwabdev as schwab
import os
from dotenv import load_dotenv

# --- Schwab API Connection (Slightly modified for Streamlit's caching) ---

# Using Streamlit's cache to prevent re-authenticating on every interaction
@st.cache_resource
def create_schwab_client():
    """Loads credentials and creates an authenticated Schwab client."""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    if not api_key or not api_secret:
        st.error("Error: API_KEY and API_SECRET must be set in a .env file.")
        return None
        
    try:
        client = schwab.Client(api_key, api_secret)
        client.authenticate()
        return client
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None

# --- Data Processing and Feature Engineering ---

def parse_option_chain(json_data):
    """
    Parses the complex JSON from Schwab into a clean pandas DataFrame.
    Also calculates our custom "unusual" metrics.
    """
    contracts = []
    underlying_price = json_data.get('underlying', {}).get('last', 0)

    for date_str, date_map in json_data.get('callExpDateMap', {}).items():
        for strike, strike_list in date_map.items():
            for contract_data in strike_list:
                contract_data['type'] = 'CALL'
                contracts.append(contract_data)

    for date_str, date_map in json_data.get('putExpDateMap', {}).items():
        for strike, strike_list in date_map.items():
            for contract_data in strike_list:
                contract_data['type'] = 'PUT'
                contracts.append(contract_data)
    
    df = pd.DataFrame(contracts)

    # --- Feature Engineering: Adding our "Unusual Whales" metrics ---
    
    # Convert types for calculation
    numeric_cols = ['strikePrice', 'bid', 'ask', 'last', 'mark', 'volume', 'openInterest', 
                    'delta', 'gamma', 'theta', 'vega', 'impliedVolatility']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Calculate Days to Expiration (DTE)
    df['expirationDate'] = pd.to_datetime(df['expirationDate'], unit='ms')
    df['DTE'] = (df['expirationDate'] - datetime.now()).dt.days

    # Calculate Volume / Open Interest Ratio
    df['V/OI'] = (df['volume'] / df['openInterest']).round(2).fillna(0)
    df['V/OI'] = df['V/OI'].replace(float('inf'), 0) # Handle division by zero

    # Calculate Total Premium
    df['Premium'] = (df['volume'] * df['mark'] * 100).astype(int)

    # Calculate Moneyness
    df['Moneyness'] = (underlying_price - df['strikePrice']).round(2)
    df.loc[df['type'] == 'PUT', 'Moneyness'] *= -1

    # --- Final Column Selection and Ordering ---
    
    display_cols = [
        'type', 'strikePrice', 'expirationDate', 'DTE', 'mark', 'volume', 
        'openInterest', 'V/OI', 'Premium', 'impliedVolatility', 'delta', 
        'gamma', 'theta', 'vega', 'Moneyness'
    ]
    df = df[display_cols].rename(columns={
        'type': 'Type', 'strikePrice': 'Strike', 'expirationDate': 'Expiry',
        'mark': 'Mark', 'volume': 'Volume', 'openInterest': 'Open Int',
        'impliedVolatility': 'IV', 'delta': 'Delta', 'gamma': 'Gamma',
        'theta': 'Theta', 'vega': 'Vega'
    })

    # Format expiry date for better readability
    df['Expiry'] = df['Expiry'].dt.strftime('%Y-%m-%d')
    
    return df.sort_values(by='Premium', ascending=False)

# --- Streamlit User Interface ---

st.set_page_config(layout="wide")
st.title('📈 Schwab Options Screener')
st.markdown("An interactive tool to analyze options chains, inspired by Unusual Whales.")

client = create_schwab_client()

if client:
    ticker = st.text_input('Enter a stock ticker symbol (e.g., AAPL, NVDA):', 'SPY').upper()

    if st.button('Fetch Option Chain'):
        with st.spinner(f'Fetching data for {ticker}... This may take a moment.'):
            response = client.get_option_chain(ticker)
            if response.ok:
                option_data = parse_option_chain(response.json())
                st.success(f"Successfully loaded {len(option_data)} contracts for {ticker}.")
                
                st.dataframe(option_data, use_container_width=True, height=600)
                st.info("💡 Tip: Click on column headers like 'Volume', 'Premium', or 'V/OI' to sort and find interesting activity.")
                
                # Store data in session state to avoid re-fetching
                st.session_state['option_data'] = option_data
            else:
                st.error(f"Failed to fetch data: {response.status_code} - {response.text}")
else:
    st.warning("Please configure your .env file with Schwab API credentials.")
