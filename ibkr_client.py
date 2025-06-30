import urllib3
import os
import pandas as pd
from ibind import IbkrClient

IBKR_GATEWAY_URL = os.environ.get('IBKR_GATEWAY_URL', 'localhost')
ACCOUNT_ID = os.getenv('IBKR_ACCOUNT_ID', 'No account id provided')
PORT = os.getenv('IBKR_GATEWAY_PORT', '5001')

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Client:
    def __init__(self):
        self.client = IbkrClient(host=IBKR_GATEWAY_URL, port=PORT)
        self.client.account_id = ACCOUNT_ID

    def initialize_brokerage_session(self):
        self.client.initialize_brokerage_session()

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

    def get_live_marketdata_snapshot(self, conid, fields=[]):
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
    """Fetch real-time stock price for a given symbol using available ibind methods"""
    try:
        print(f"Fetching stock price for {symbol}...")
        # Make session to ensure proper session state
        ibkr_client.client.make_session()
        # Use stock_conid_by_symbol to get the contract ID
        conid_result = ibkr_client.client.stock_conid_by_symbol(symbol)
        if not conid_result.data or symbol not in conid_result.data:
            print(f"Symbol {symbol} not found in IBKR search")
            return None
        conid = str(conid_result.data[symbol])
        print(f"Found contract for {symbol} with conid: {conid}")
        # Try simpler field codes - just last price
        fields = "31"  # Last price only
        quote_result = ibkr_client.client.live_marketdata_snapshot([conid], fields=fields)
        print(f"Quote result: {quote_result.data}")
        if not quote_result.data:
            print(f"No market data available for {symbol}")
            return None
        quote = quote_result.data[0]
        # Try to get the last price (field '31')
        current_price = quote.get('31')
        print(f"Current price: {current_price}")
        # Remove 'C' prefix if present in current_price - when market is closed for example
        if current_price and isinstance(current_price, str) and current_price.startswith('C'):
            print(f"Removing 'C' prefix from price: {current_price}")
            current_price = current_price[1:]
        if current_price is not None:
            print(f"Successfully fetched stock price for {symbol}: ${current_price}")
        else:
            print(f"Could not extract price from quote data for {symbol}")
        return current_price
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None

def fetch_vix_price():
    """Fetch real-time VIX price using the correct contract ID"""
    try:
        print("Fetching VIX price...")
        # Make session to ensure proper session state
        ibkr_client.initialize_brokerage_session()

        # VIX contract ID - this is the standard VIX index contract
        vix_conid = "13455763"  # VIX index contract ID

        # Try different field codes for indices
        # 31 = Last price, 84 = Last size, 86 = High, 87 = Low, 88 = Open
        fields = "31,84,86"
        quote_result = ibkr_client.client.live_marketdata_snapshot([vix_conid], fields=fields)
        print(f"VIX quote result: {quote_result.data}")

        if not quote_result.data:
            print("No market data available for VIX")
            return None

        quote = quote_result.data[0]

        # Try different price fields in order of preference
        price_fields = ['31', '88', '86']  # Last price, Open, High
        current_price = None

        for field in price_fields:
            current_price = quote.get(field)
            if current_price is not None and current_price != '':
                print(f"VIX price from field {field}: {current_price}")
                break

        if current_price is None:
            print("No price data found in any field")
            return None

        # Remove 'C' prefix if present (when market is closed)
        if isinstance(current_price, str) and current_price.startswith('C'):
            print(f"Removing 'C' prefix from VIX price: {current_price}")
            current_price = current_price[1:]

        if current_price is not None:
            print(f"Successfully fetched VIX price: ${current_price}")
        else:
            print("Could not extract VIX price from quote data")

        return current_price
    except Exception as e:
        print(f"Error fetching VIX price: {e}")
        return None

def fetch_index_price(symbol):
    """Fetch real-time index price for common indices"""
    try:
        print(f"Fetching index price for {symbol}...")
        # Make session to ensure proper session state
        ibkr_client.client.make_session()

        # Common index contract IDs
        index_conids = {
            'VIX': '13455763',    # VIX volatility index (updated)
            'SPX': '332',         # S&P 500 index
            'NDX': '370',         # NASDAQ-100 index
            'RUT': '1386',        # Russell 2000 index
            'DJX': '169',         # Dow Jones Industrial Average
            'VIX1D': '13455763',  # VIX (updated)
        }

        if symbol.upper() not in index_conids:
            print(f"Index {symbol} not supported. Supported indices: {list(index_conids.keys())}")
            return None

        conid = index_conids[symbol.upper()]
        print(f"Using contract ID for {symbol}: {conid}")

        # Try different field codes for indices
        fields = "31,84,86,87,88"  # Last price, Last size, High, Low, Open
        quote_result = ibkr_client.client.live_marketdata_snapshot([conid], fields=fields)
        print(f"Index quote result: {quote_result.data}")

        if not quote_result.data:
            print(f"No market data available for {symbol}")
            return None

        quote = quote_result.data[0]

        # Try different price fields in order of preference
        price_fields = ['31', '88', '86']  # Last price, Open, High
        current_price = None

        for field in price_fields:
            current_price = quote.get(field)
            if current_price is not None and current_price != '':
                print(f"{symbol} price from field {field}: {current_price}")
                break

        if current_price is None:
            print(f"No price data found in any field for {symbol}")
            return None

        # Remove 'C' prefix if present (when market is closed)
        if isinstance(current_price, str) and current_price.startswith('C'):
            print(f"Removing 'C' prefix from {symbol} price: {current_price}")
            current_price = current_price[1:]

        if current_price is not None:
            print(f"Successfully fetched {symbol} price: ${current_price}")
        else:
            print(f"Could not extract {symbol} price from quote data")

        return current_price
    except Exception as e:
        print(f"Error fetching {symbol} price: {e}")
        return None
