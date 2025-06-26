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
        results = self.client.portfolio_accounts().data
        print(f"Portfolio accounts: {results}")

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

    def get_conid_by_symbol(self, symbol):
        self.get_portfolio_accounts()
        conid = self.client.stock_conid_by_symbol(symbol).data[symbol]
        return conid

    def get_live_marketdata_snapshot(self, conid, fields=['31', '84', '86']):
        self.get_portfolio_accounts()
        quote_result = self.client.live_marketdata_snapshot([conid], fields=fields).data
        return quote_result

    def get_marketdata_history_by_conids(self, conids):
        self.get_portfolio_accounts()
        history_result = self.client.marketdata_history_by_conids(conids).data
        return history_result

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

def fetch_stock_price(symbol):
    """Fetch real-time stock price for a given symbol using latest ibind methods"""
    try:
        print(f"Fetching stock price for {symbol}...")
        # Get the contract ID for the symbol
        conid = ibkr_client.get_conid_by_symbol(symbol)
        # print(f"Conid result: {conid}")
        if not conid:
            print(f"Symbol {symbol} not found in IBKR search")
            return None
        print(f"Found contract for {symbol} with conid: {conid}")
        # Get live market data snapshot
        quote_result = ibkr_client.get_live_marketdata_snapshot(str(conid))
        print(f"Quote result: {quote_result}")
        # quote_result = ibkr_client.get_marketdata_history_by_conids([conid])
        print(f"Quote result: {quote_result}")
        if not quote_result:
            print(f"No market data available for {symbol}")
            return None
        quote = quote_result[0]
        # Try to get the last price (field '31'), or fallback to bid/ask
        current_price = quote.get('31')
        if current_price is None:
            current_price = quote.get('84')
            if current_price is None:
                current_price = quote.get('86')
        print(f"Current price: {current_price}")
        # Remove 'C' prefix if present in current_price - when market is closed for example
        if current_price and current_price.startswith('C'):
            print(f"Current price: {current_price}")
            current_price = current_price[1:]
        if current_price is not None:
            print(f"Successfully fetched stock price for {symbol}: ${current_price}")
        else:
            print(f"Could not extract price from quote data for {symbol}")
        return current_price
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None
