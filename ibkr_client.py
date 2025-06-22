import os
import pandas as pd
from ibind import IbkrClient

IBKR_GATEWAY_URL = os.environ.get('IBKR_GATEWAY_URL', 'localhost')
ACCOUNT_ID = os.getenv('IBIND_ACCOUNT_ID', 'No account id provided')
PORT = os.getenv('IBIND_PORT', '5001')

class Client:
    def __init__(self):
        self.client = IbkrClient(host=IBKR_GATEWAY_URL, port=PORT)
        self.client.account_id = ACCOUNT_ID

    def get_portfolio_accounts(self):
        self.client.portfolio_accounts()

    def get_account_details(self):
        # Example: fetch account summary
        self.get_portfolio_accounts()
        account_info = self.client.portfolio_account_information().data
        return account_info

    def get_account_ledger(self):
        """Fetch detailed account ledger information"""
        self.get_portfolio_accounts()
        try:
            ledger = self.client.get_ledger().data
            return ledger
        except Exception as e:
            print(f"Error fetching account ledger: {e}")
            return None

    def get_portfolio_summary(self):
        self.get_portfolio_accounts()
        portfolio_summary = self.client.portfolio_summary().data
        return portfolio_summary

    def get_positions(self):
        # Example: fetch open positions
        self.get_portfolio_accounts()
        positions = self.client.positions().data
        return positions

    def get_trades(self, days: str):
        # Example: fetch executions/trades
        self.get_portfolio_accounts()
        trades = self.client.trades(days=days).data
        return trades

    def tickle(self):
        self.client.tickle()

    def get_account_performance(self, period: str):
        self.get_portfolio_accounts()
        account_performance = self.client.account_performance(
            account_ids=[ACCOUNT_ID], period=period).data
        return account_performance

    def get_account_balances(self):
        """Fetch account balances and limits information"""
        self.get_portfolio_accounts()
        try:
            # Get account summary which includes balances
            account_summary = self.client.portfolio_summary().data
            return account_summary
        except Exception as e:
            print(f"Error fetching account balances: {e}")
            return None

# Singleton instance
ibkr_client = Client()

def fetch_ibkr_account_details():
    return ibkr_client.get_account_details()

def fetch_ibkr_portfolio_summary():
    return ibkr_client.get_portfolio_summary()

def fetch_ibkr_account_ledger():
    return ibkr_client.get_account_ledger()

def fetch_ibkr_positions():
    return ibkr_client.get_positions()

def fetch_ibkr_trades(days: str = 7):
    return ibkr_client.get_trades(days=days)

def fetch_ibkr_tickle():
    return ibkr_client.tickle()

def fetch_ibkr_account_performance(period="MTD"):
    if period not in ["1D", "7D", "MTD", "1M", "YTD", "1Y"]:
        raise ValueError("Invalid period")
    return ibkr_client.get_account_performance(period=period)

def fetch_ibkr_account_balances():
    """Fetch account balances and limits information"""
    return ibkr_client.get_account_balances()
