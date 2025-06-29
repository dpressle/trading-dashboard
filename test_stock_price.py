#!/usr/bin/env python3
"""
Test script to verify stock price fetching functionality
"""

from ibkr_client import fetch_stock_price

def test_stock_prices():
    """Test fetching stock prices for common symbols"""
    test_symbols = ['HIMS']

    print("Testing stock price fetching...")
    print("=" * 50)

    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        try:
            price = fetch_stock_price(symbol)
            if price is not None:
                # Convert string price to float for formatting
                price_float = float(price) if isinstance(price, str) else price
                print(f"  ✓ {symbol}: ${price_float:.2f}")
            else:
                print(f"  ✗ {symbol}: No price available")
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {e}")

    print("\n" + "=" * 50)
    print("Stock price test completed!")

if __name__ == "__main__":
    test_stock_prices()
