from ibkr_client import fetch_ibkr_account_details, fetch_ibkr_account_ledger, fetch_ibkr_portfolio_summary, fetch_ibkr_positions, fetch_ibkr_trades, fetch_ibkr_account_performance
import pandas as pd


def print_section(title):
    print("\n" + "=" * 40)
    print(title)
    print("=" * 40)


def main():
    # Test account details
    print_section("Account Details")
    try:
        account = fetch_ibkr_account_details()
        # print(account)
        df = pd.DataFrame([{
            'Account ID': account['accountId'],
            'Name': account['displayName'],
            'Type': account['type'],
        }])
        print(df)
    except Exception as e:
        print(f"Error fetching account details: {e}")

    # Test account ledger
    print_section("Account Ledger")
    try:
        ledger = fetch_ibkr_account_ledger()
        print(ledger)
        for currency, subledger in ledger.items():
            print(f'\t Ledger currency: {currency}')
            print(f'\t cash balance: {subledger["cashbalance"]}')
            print(f'\t net liquidation value: {subledger["netliquidationvalue"]}')
            print(f'\t stock market value: {subledger["stockmarketvalue"]}')
            print()

    except Exception as e:
        print(f"Error fetching account details: {e}")


    # print_section("Account Summary")
    # try:
    #     summary = fetch_ibkr_portfolio_summary()
    #     print(summary)
    #     df = pd.DataFrame(summary)
    #     print(df)
    # except Exception as e:
    #     print(f"Error fetching account summary: {e}")

    # print_section("Account Performance")
    # try:
    #     performance = fetch_ibkr_account_performance()
    #     print(performance)
    #     # df = pd.DataFrame(performance)
    #     # print(df)
    # except Exception as e:
        # print(f"Error fetching account performance: {e}")

    # Test positions
    # print_section("Open Positions")
    # try:
    #     positions = fetch_ibkr_positions()
    #     print(positions)
    #     df = pd.DataFrame(positions)
    #     print(df)
    #     if positions:
            # print(positions)
            # df = pd.DataFrame([{
            #     'Type': positions['putOrCall'],
            #     'Symbol': positions['ticker'],
            #     'Description': positions['fullName'],
            #     'Expiration': positions['expiry'],
            #     'Strike': positions['strike'],
            #     'Premium': positions['avgPrice'],
            #     'Quantity': positions['position'],
            # }])
    #         positions_list = []
    #         for position in positions:
    #             positions_list.append({
    #                 'Type': position['putOrCall'],
    #                 'Symbol': position['ticker'],
    #                 'Description': position['fullName'],
    #                 'Expiration': position['expiry'],
    #                 'Strike': position['strike'],
    #                 'Premium': position['avgPrice'],
    #                 'Quantity': position['position'],
    #                 'Price': position['avgPrice'],
    #                 'Amount': position['avgCost'],
    #             })
    #         print(positions_list)
    #         df = pd.DataFrame(positions_list)
    #         print(df)
    #     else:
    #         print("No open positions or empty DataFrame.")
    # except Exception as e:
    #     print(f"Error fetching positions: {e}")

    # # Test trades
    # print_section("Trades/Executions")
    # try:
    #     trades = fetch_ibkr_trades(days="7")
    #     # print(trades)
    #     df = pd.DataFrame(trades)
    #     print(df.iloc[6])
    # except Exception as e:
    #     print(f"Error fetching trades: {e}")


if __name__ == "__main__":
    main()
