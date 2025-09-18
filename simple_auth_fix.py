#!/usr/bin/env python3
"""
Simple approach: manually input the callback URL when prompted
"""
import schwabdev as schwab
import os
from config import API_KEY, API_SECRET

def main():
    """Run authentication with manual URL input"""

    # Token file path
    tokens_file = os.path.join(os.path.dirname(__file__), 'schwab_tokens.json')

    print("=== Schwab API Authentication ===")
    print(f"Token file: {tokens_file}")
    print(f"Callback URL should be: https://127.0.0.1")
    print()
    print("Your authorization URL to paste when prompted:")
    print("https://127.0.0.1/?code=C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.7nKRGNOdHq8K7Rp0E_JHR4WFj24fRCe0bmb3EsqwXz0%40&session=ed160729-398f-4185-b9ae-c585dcd6677e")
    print()

    try:
        # Create client - this will prompt for the URL
        client = schwab.Client(
            app_key=API_KEY,
            app_secret=API_SECRET,
            callback_url="https://127.0.0.1",
            tokens_file=tokens_file
        )

        print("Testing API connection...")
        response = client.quotes(['SPY'])

        if response.ok:
            print("✅ Success! API connection working!")
            data = response.json()
            if 'SPY' in data:
                price = data['SPY'].get('lastPrice', 'N/A')
                print(f"SPY Price: ${price}")
        else:
            print(f"❌ API test failed: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()