from ibkr_client import fetch_ibkr_account_performance
import json

def test_account_performance():
    periods = ["1D", "7D", "MTD", "1M", "YTD", "1Y"]

    for period in periods:
        print(f"\n{'='*50}")
        print(f"ACCOUNT PERFORMANCE - {period}")
        print(f"{'='*50}")

        try:
            performance = fetch_ibkr_account_performance(period=period)
            print(f"Raw output type: {type(performance)}")
            print(f"Raw output:")
            print(json.dumps(performance, indent=2, default=str))

            # If it's a list, show first item
            if isinstance(performance, list) and performance:
                print(f"\nFirst item structure:")
                print(json.dumps(performance[0], indent=2, default=str))

        except Exception as e:
            print(f"Error fetching {period} performance: {e}")

if __name__ == "__main__":
    test_account_performance()
