from ibkr_client import fetch_ibkr_account_details, fetch_ibkr_account_balances, fetch_ibkr_account_ledger
from app import parse_account_status_data

def test_account_status():
    print("=== ACCOUNT STATUS TEST ===\n")

    # Test account details
    print("1. Testing Account Details:")
    try:
        account_details = fetch_ibkr_account_details()
        if account_details:
            print(f"   Account ID: {account_details.get('accountId', 'N/A')}")
            print(f"   Name: {account_details.get('displayName', 'N/A')}")
            print(f"   Type: {account_details.get('type', 'N/A')}")
            print(f"   Currency: {account_details.get('currency', 'N/A')}")
        else:
            print("   No account details available")
    except Exception as e:
        print(f"   Error fetching account details: {e}")

    print("\n" + "="*50)

    # Test account balances
    print("2. Testing Account Balances:")
    try:
        account_balances = fetch_ibkr_account_balances()
        if account_balances:
            print(f"   Balance data type: {type(account_balances)}")
            print(f"   Balance keys: {list(account_balances.keys()) if isinstance(account_balances, dict) else 'Not a dict'}")

            if isinstance(account_balances, dict):
                for currency, data in account_balances.items():
                    print(f"\n   {currency} Balance Data:")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            print(f"     {key}: {value}")
                    else:
                        print(f"     Raw data: {data}")
        else:
            print("   No account balances available")
    except Exception as e:
        print(f"   Error fetching account balances: {e}")

    print("\n" + "="*50)

    # Test account ledger
    print("3. Testing Account Ledger:")
    try:
        account_ledger = fetch_ibkr_account_ledger()
        if account_ledger:
            print(f"   Ledger data type: {type(account_ledger)}")
            print(f"   Ledger keys: {list(account_ledger.keys()) if isinstance(account_ledger, dict) else 'Not a dict'}")

            if isinstance(account_ledger, dict):
                for currency, data in account_ledger.items():
                    print(f"\n   {currency} Ledger Data:")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            print(f"     {key}: {value}")
                    else:
                        print(f"     Raw data: {data}")
        else:
            print("   No account ledger available")
    except Exception as e:
        print(f"   Error fetching account ledger: {e}")

    print("\n" + "="*50)

    # Test parsed account status
    print("4. Testing Parsed Account Status:")
    try:
        account_details = fetch_ibkr_account_details()
        account_balances = fetch_ibkr_account_balances()
        account_ledger = fetch_ibkr_account_ledger()

        status_data = parse_account_status_data(account_details, account_balances, account_ledger)

        print(f"   Connection Status: {status_data.get('connection_status', 'Unknown')}")
        print(f"   Account Info: {status_data.get('account_info', {})}")
        print(f"   Balance Currencies: {list(status_data.get('balances', {}).keys())}")

        for currency, balance in status_data.get('balances', {}).items():
            print(f"\n   {currency} Parsed Balance:")
            for key, value in balance.items():
                print(f"     {key}: {value}")

    except Exception as e:
        print(f"   Error parsing account status: {e}")

if __name__ == "__main__":
    test_account_status()
