from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import threading
import time
from datetime import datetime, timedelta
from ibkr_client import fetch_ibkr_account_details, fetch_ibkr_positions, fetch_ibkr_tickle, fetch_ibkr_account_performance, fetch_ibkr_account_ledger

app = Flask(__name__)

# IBKR Gateway configuration
IBKR_GATEWAY_URL = os.environ.get('IBKR_GATEWAY_URL', 'localhost')
IBKR_GATEWAY_PORT = os.environ.get('IBIND_PORT', '5001')
IBKR_GATEWAY_LOGIN_URL = f"https://{IBKR_GATEWAY_URL}:{IBKR_GATEWAY_PORT}"

# Initialize connection status
connection_status = {
    'connected': False,
    'last_check': None,
    'error_message': None,
    'retry_count': 0,
    'tickle_enabled': True  # Add flag to control tickle behavior
}

# Try initial connection check
print(f"DEBUG: Initializing connection status...")
try:
    account_details = fetch_ibkr_account_details()
    if account_details:
        connection_status['connected'] = True
        connection_status['error_message'] = None
        connection_status['last_check'] = datetime.now()
        print(f"DEBUG: Initial connection successful")
    else:
        print(f"DEBUG: Initial connection failed - no account details")
except Exception as e:
    print(f"DEBUG: Initial connection failed with exception: {e}")
    connection_status['error_message'] = str(e)
    connection_status['last_check'] = datetime.now()

def tickle_worker():
    """Background worker to keep IBKR connection alive"""
    consecutive_failures = 0
    max_consecutive_failures = 5  # Stop tickling after 5 consecutive failures

    while True:
        try:
            # Check if tickle is enabled
            if not connection_status.get('tickle_enabled', True):
                print(f"DEBUG: Tickle disabled due to persistent connection issues")
                time.sleep(60)  # Wait 60 seconds before checking again
                continue

            print(f"DEBUG: Sending IBKR tickle at {datetime.now()}")
            fetch_ibkr_tickle()
            print(f"IBKR tickle sent at {datetime.now()}")

            # Update connection status on successful tickle
            connection_status['connected'] = True
            connection_status['error_message'] = None
            connection_status['retry_count'] = 0
            consecutive_failures = 0  # Reset failure counter
            print(f"DEBUG: Tickle successful - connection status updated")

        except Exception as e:
            consecutive_failures += 1
            print(f"Error sending IBKR tickle: {e}")
            connection_status['connected'] = False
            connection_status['error_message'] = str(e)
            connection_status['retry_count'] += 1
            print(f"DEBUG: Tickle failed - connection status set to disconnected (failure #{consecutive_failures})")

            # Disable tickle if too many consecutive failures
            if consecutive_failures >= max_consecutive_failures:
                connection_status['tickle_enabled'] = False
                print(f"DEBUG: Disabling tickle due to {consecutive_failures} consecutive failures")

        time.sleep(60)  # Wait 60 seconds

# Start the tickle worker thread
tickle_thread = threading.Thread(target=tickle_worker, daemon=True)
tickle_thread.start()

def check_ibkr_connection():
    """Check if IBKR connection is working by making a simple API call"""
    try:
        print(f"DEBUG: Attempting to check IBKR connection at {datetime.now()}")
        # Try to fetch account details as a connection test
        account_details = fetch_ibkr_account_details()
        print(f"DEBUG: fetch_ibkr_account_details returned: {account_details}")

        if account_details:
            connection_status['connected'] = True
            connection_status['error_message'] = None
            connection_status['retry_count'] = 0
            connection_status['tickle_enabled'] = True  # Re-enable tickle on successful connection
            connection_status['last_check'] = datetime.now()
            print(f"DEBUG: Connection successful - account details found, tickle re-enabled")
            return True
        else:
            connection_status['connected'] = False
            connection_status['error_message'] = "No account details received"
            print(f"DEBUG: Connection failed - no account details received")
            return False
    except Exception as e:
        connection_status['connected'] = False
        connection_status['error_message'] = str(e)
        connection_status['retry_count'] += 1
        connection_status['last_check'] = datetime.now()
        print(f"DEBUG: Connection failed with exception: {e}")
        return False

def safe_ibkr_call(func, *args, **kwargs):
    """Safely call IBKR functions with proper error handling"""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        error_msg = str(e)

        # Check for specific IBKR error types
        if "401" in error_msg or "Unauthorized" in error_msg:
            connection_status['connected'] = False
            connection_status['error_message'] = "IBKR session expired. Please re-authenticate in IBKR Gateway."
        elif "ExternalBrokerError" in error_msg:
            connection_status['connected'] = False
            connection_status['error_message'] = "IBKR Gateway connection error. Check if Gateway is running."
        elif "Connection" in error_msg or "timeout" in error_msg.lower():
            connection_status['connected'] = False
            connection_status['error_message'] = "Network connection issue. Check IBKR Gateway connectivity."
        elif "404" in error_msg:
            connection_status['error_message'] = f"IBKR API endpoint not found: {error_msg}"
        elif "500" in error_msg:
            connection_status['error_message'] = f"IBKR server error: {error_msg}"
        else:
            connection_status['error_message'] = f"IBKR API Error: {error_msg}"

        connection_status['retry_count'] += 1
        connection_status['last_check'] = datetime.now()
        return None, error_msg

# def calculate_trading_analytics(transactions_df, start_date=None, end_date=None):
    """Calculate various trading analytics from the transactions data."""
    analytics = {}

    # Convert date strings to datetime
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'], format='%Y%m%d')

    # Apply date filtering if provided
    if start_date:
        start_date = pd.to_datetime(start_date)
        transactions_df = transactions_df[transactions_df['Date'] >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date)
        transactions_df = transactions_df[transactions_df['Date'] <= end_date]

    # Return empty analytics if no data after filtering
    if transactions_df.empty:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl': 0,
            'max_profit': 0,
            'max_loss': 0,
            'max_drawdown': 0,
            'avg_drawdown': 0,
            'return_volatility': 0,
            'sharpe_ratio': 0,
            'type_stats': {},
            'best_trades': [],
            'worst_trades': [],
            'avg_holding_period': 0,
            'holding_period_stats': {}
        }

    # Group trades by symbol, expiration, strike, and type
    transactions_df['Trade_Group'] = transactions_df.apply(
        lambda row: f"{row['Symbol']}_{row['Description'].split()[1]}_{row['Description'].split()[2]}_{row['Description'].split()[-1]}",
        axis=1
    )

    # Calculate trade outcomes
    trade_groups = transactions_df.groupby('Trade_Group')
    completed_trades = []
    daily_returns = []  # For calculating risk metrics

    for group_name, group in trade_groups:
        if len(group) >= 2:  # Only consider trades that have been closed
            # Sort by date to ensure proper order
            group = group.sort_values('Date')
            first_trade = group.iloc[0]
            last_trade = group.iloc[-1]

            # Calculate profit/loss based on trade direction including fees
            if first_trade['Action'] == 'BUYTOOPEN':
                entry_amount = first_trade['Amount']  # This is positive (cost to buy)
                entry_fee = first_trade['Fee']
                exit_amount = -last_trade['Amount']   # This is negative (value received from sell)
                exit_fee = last_trade['Fee']
                pnl = exit_amount - entry_amount - entry_fee - exit_fee
            else:  # SELLTOOPEN
                entry_amount = -first_trade['Amount']  # This is positive (value received from sell)
                entry_fee = first_trade['Fee']
                exit_amount = last_trade['Amount']     # This is positive (cost to buy back)
                exit_fee = last_trade['Fee']
                pnl = entry_amount - exit_amount - entry_fee - exit_fee

            # Determine if it was a winning trade
            is_win = pnl > 0

            # Calculate daily return for risk metrics
            days_held = (last_trade['Date'] - first_trade['Date']).days
            if days_held > 0:
                daily_return = pnl / (abs(entry_amount) * days_held)  # Simple daily return
                daily_returns.append({
                    'date': last_trade['Date'],
                    'return': daily_return
                })

            completed_trades.append({
                'Symbol': first_trade['Symbol'],
                'Description': first_trade['Description'],
                'Entry_Date': first_trade['Date'],
                'Exit_Date': last_trade['Date'],
                'Entry_Amount': entry_amount,
                'Exit_Amount': exit_amount,
                'PnL': pnl,
                'Is_Win': is_win,
                'Type': first_trade['Description'].split()[-1],  # P or C
                'Days_Held': days_held
            })

    if completed_trades:
        trades_df = pd.DataFrame(completed_trades)
        returns_df = pd.DataFrame(daily_returns)

        # Calculate overall statistics
        analytics['total_trades'] = len(trades_df)
        analytics['winning_trades'] = len(trades_df[trades_df['Is_Win']])
        analytics['losing_trades'] = len(trades_df[~trades_df['Is_Win']])
        analytics['win_rate'] = (analytics['winning_trades'] / analytics['total_trades'] * 100) if analytics['total_trades'] > 0 else 0

        # Profit/Loss statistics
        analytics['total_pnl'] = trades_df['PnL'].sum()
        analytics['avg_pnl'] = trades_df['PnL'].mean()
        analytics['max_profit'] = trades_df['PnL'].max()
        analytics['max_loss'] = trades_df['PnL'].min()

        # Risk Metrics
        if not returns_df.empty:
            # Calculate cumulative returns for drawdown
            returns_df = returns_df.sort_values('date')
            returns_df['cumulative_return'] = (1 + returns_df['return']).cumprod()
            returns_df['rolling_max'] = returns_df['cumulative_return'].cummax()
            returns_df['drawdown'] = (returns_df['cumulative_return'] - returns_df['rolling_max']) / returns_df['rolling_max']

            # Max and Average Drawdown
            analytics['max_drawdown'] = abs(returns_df['drawdown'].min()) * analytics['total_pnl']
            analytics['avg_drawdown'] = abs(returns_df['drawdown'].mean()) * analytics['total_pnl']

            # Return Volatility (annualized)
            analytics['return_volatility'] = returns_df['return'].std() * (252 ** 0.5) * 100  # Annualized volatility as percentage

            # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
            avg_daily_return = returns_df['return'].mean()
            daily_volatility = returns_df['return'].std()
            if daily_volatility != 0:
                sharpe_ratio = (avg_daily_return / daily_volatility) * (252 ** 0.5)  # Annualized Sharpe ratio
                analytics['sharpe_ratio'] = sharpe_ratio
            else:
                analytics['sharpe_ratio'] = 0
        else:
            # Set default values if no returns data
            analytics['max_drawdown'] = 0
            analytics['avg_drawdown'] = 0
            analytics['return_volatility'] = 0
            analytics['sharpe_ratio'] = 0

        # Statistics by option type
        type_stats = trades_df.groupby('Type').agg({
            'PnL': ['count', 'sum', 'mean'],
            'Is_Win': 'mean'
        }).round(2)
        type_stats.columns = ['Count', 'Total_PnL', 'Avg_PnL', 'Win_Rate']
        type_stats['Win_Rate'] = type_stats['Win_Rate'] * 100
        analytics['type_stats'] = type_stats.to_dict('index')

        # Best and worst trades
        analytics['best_trades'] = trades_df.nlargest(3, 'PnL')[['Symbol', 'Description', 'PnL', 'Days_Held']].to_dict('records')
        analytics['worst_trades'] = trades_df.nsmallest(3, 'PnL')[['Symbol', 'Description', 'PnL', 'Days_Held']].to_dict('records')

        # Average holding period
        analytics['avg_holding_period'] = trades_df['Days_Held'].mean()

        # Success rate by holding period
        trades_df['Holding_Period_Category'] = pd.cut(
            trades_df['Days_Held'],
            bins=[0, 7, 14, 30, 90, float('inf')],
            labels=['<1 week', '1-2 weeks', '2-4 weeks', '1-3 months', '>3 months']
        )
        holding_period_stats = trades_df.groupby('Holding_Period_Category').agg({
            'PnL': ['count', 'mean', 'sum'],
            'Is_Win': 'mean'
        }).round(2)
        holding_period_stats.columns = ['Count', 'Avg_PnL', 'Total_PnL', 'Win_Rate']
        holding_period_stats['Win_Rate'] = holding_period_stats['Win_Rate'] * 100
        analytics['holding_period_stats'] = holding_period_stats.to_dict('index')

    return analytics

# def calculate_option_summary(transactions_df, start_date=None, end_date=None):
#     """Calculate summary statistics for option transactions based on their type."""
#     # Apply date filtering if provided
#     if start_date or end_date:
#         # Ensure Date column is datetime
#         if 'Date' not in transactions_df.columns or not pd.api.types.is_datetime64_any_dtype(transactions_df['Date']):
#             transactions_df['Date'] = pd.to_datetime(transactions_df['Date'], format='%Y%m%d')

#         if start_date:
#             start_date = pd.to_datetime(start_date)
#             transactions_df = transactions_df[transactions_df['Date'] >= start_date]

#         if end_date:
#             end_date = pd.to_datetime(end_date)
#             transactions_df = transactions_df[transactions_df['Date'] <= end_date]

#     summary = {
#         'total_transactions': len(transactions_df),
#         'total_premium': 0,
#         'total_fees': transactions_df['Fee'].sum() if not transactions_df.empty else 0,
#         'net_pnl': 0,
#         'open_positions': 0,
#         'closed_positions': 0
#     }

#     # Return early if no transactions after filtering
#     if transactions_df.empty:
#         return summary

#     # Group by trade identifier (symbol + expiration + strike + type)
#     transactions_df['Trade_Group'] = transactions_df.apply(
#         lambda row: f"{row['Symbol']}_{row['Description'].split()[1]}_{row['Description'].split()[2]}_{row['Description'].split()[-1]}",
#         axis=1
#     )

#     # Calculate summary by trade group
#     trade_groups = transactions_df.groupby('Trade_Group')
#     for group_name, group in trade_groups:
#         group = group.sort_values('Date')
#         first_trade = group.iloc[0]
#         last_trade = group.iloc[-1]

#         # Calculate premium based on trade direction
#         if first_trade['Action'] == 'BUYTOOPEN':
#             entry_premium = first_trade['Amount']  # Positive (cost to buy)
#             entry_fee = first_trade['Fee']  # Fee for entry
#             if len(group) > 1:  # Closed position
#                 exit_premium = -last_trade['Amount']  # Negative (value received from sell)
#                 exit_fee = last_trade['Fee']  # Fee for exit
#                 trade_pnl = exit_premium - entry_premium - entry_fee - exit_fee
#                 summary['net_pnl'] += trade_pnl
#                 summary['closed_positions'] += 1
#             else:  # Open position
#                 summary['net_pnl'] -= (entry_premium + entry_fee)
#                 summary['open_positions'] += 1
#         else:  # SELLTOOPEN
#             entry_premium = -first_trade['Amount']  # Positive (value received from sell)
#             entry_fee = first_trade['Fee']  # Fee for entry
#             if len(group) > 1:  # Closed position
#                 exit_premium = last_trade['Amount']  # Positive (cost to buy back)
#                 exit_fee = last_trade['Fee']  # Fee for exit
#                 trade_pnl = entry_premium - exit_premium - entry_fee - exit_fee
#                 summary['net_pnl'] += trade_pnl
#                 summary['closed_positions'] += 1
#             else:  # Open position
#                 summary['net_pnl'] += (entry_premium - entry_fee)
#                 summary['open_positions'] += 1

#     return summary

# def calculate_option_positions_summary(positions_df):
#     """Calculate summary statistics for current option positions."""
#     summary = {
#         'total_positions': len(positions_df),
#         'total_value': 0,
#         'long_positions': 0,
#         'short_positions': 0,
#         'total_fees': 0  # Fees for open positions
#     }

#     for _, position in positions_df.iterrows():
#         quantity = position['Quantity']
#         amount = position['Amount']
#         fee = position['Fee'] if 'Fee' in position else 0

#         # For long positions (positive quantity), amount is negative (cost)
#         # For short positions (negative quantity), amount is negative (credit)
#         if quantity > 0:  # Long position
#             summary['total_value'] -= amount  # Subtract cost (amount is negative)
#             summary['long_positions'] += 1
#         else:  # Short position
#             summary['total_value'] -= amount  # Subtract credit (amount is negative, so this adds the credit)
#             summary['short_positions'] += 1

#         summary['total_fees'] += fee

#     return summary

# def calculate_expiration_alerts(positions_df):
#     """Calculate alerts for upcoming option expirations."""
#     if positions_df is None or positions_df.empty:
#         return []

#     alerts = []
#     today = datetime.now()

#     # Filter for option positions only
#     option_positions = positions_df[positions_df['Type'].isin(['P', 'C'])]

#     for _, position in option_positions.iterrows():
#         try:
#             # Extract expiration date from description
#             desc_parts = position['Description'].split()
#             if len(desc_parts) >= 2:
#                 exp_date_str = desc_parts[1]  # e.g., "04APR25"
#                 exp_date = datetime.strptime(exp_date_str, '%d%b%y')

#                 # Calculate days until expiration
#                 days_to_exp = (exp_date - today).days

#                 # Only include positions that haven't expired
#                 if days_to_exp >= 0:
#                     # Calculate alert level
#                     if days_to_exp <= 3:
#                         alert_level = 'danger'
#                     elif days_to_exp <= 7:
#                         alert_level = 'warning'
#                     else:
#                         alert_level = 'info'

#                     alerts.append({
#                         'symbol': position['Symbol'],
#                         'description': position['Description'],
#                         'expiration_date': exp_date.strftime('%Y-%m-%d'),
#                         'days_to_expiration': days_to_exp,
#                         'quantity': position['Quantity'],
#                         'strike': position['Strike'],
#                         'type': position['Type'],
#                         'premium': position['Premium'],
#                         'alert_level': alert_level
#                     })
#         except (ValueError, IndexError):
#             continue

#     # Sort alerts by days to expiration
#     alerts.sort(key=lambda x: x['days_to_expiration'])
#     return alerts

# def apply_date_filter(trading_data, start_date=None, end_date=None):
#     """Apply date filtering to the trading data and recalculate analytics."""
#     if not start_date and not end_date:
#         return trading_data

#     # Filter option transactions if they exist
#     if 'option_transactions' in trading_data:
#         original_transactions = trading_data['option_transactions'].copy()

#         # Ensure Date column is datetime
#         if 'Date' in original_transactions.columns:
#             original_transactions['Date'] = pd.to_datetime(original_transactions['Date'], format='%Y%m%d')

#             # Apply date filtering
#             if start_date:
#                 start_date_dt = pd.to_datetime(start_date)
#                 original_transactions = original_transactions[original_transactions['Date'] >= start_date_dt]

#             if end_date:
#                 end_date_dt = pd.to_datetime(end_date)
#                 original_transactions = original_transactions[original_transactions['Date'] <= end_date_dt]

#             # Update the filtered data
#             trading_data['option_transactions'] = original_transactions

#             # Recalculate analytics with filtered data
#             trading_data['trading_analytics'] = calculate_trading_analytics(original_transactions, start_date, end_date)
#             trading_data['option_summary'] = calculate_option_summary(original_transactions, start_date, end_date)

#     # Filter stock transactions if they exist
#     if 'stock_transactions' in trading_data:
#         original_stock_transactions = trading_data['stock_transactions'].copy()

#         # Ensure Date column is datetime
#         if 'Date' in original_stock_transactions.columns:
#             original_stock_transactions['Date'] = pd.to_datetime(original_stock_transactions['Date'], format='%Y%m%d')

#             # Apply date filtering
#             if start_date:
#                 start_date_dt = pd.to_datetime(start_date)
#                 original_stock_transactions = original_stock_transactions[original_stock_transactions['Date'] >= start_date_dt]

#             if end_date:
#                 end_date_dt = pd.to_datetime(end_date)
#                 original_stock_transactions = original_stock_transactions[original_stock_transactions['Date'] <= end_date_dt]

#             # Update the filtered data
#             trading_data['stock_transactions'] = original_stock_transactions

#     return trading_data

# def get_available_data_files():
#     """Get list of available .tlg files in the data directory."""
#     return [os.path.basename(f) for f in glob.glob('data/*.tlg')]

# def parse_trading_data(filename):
#     """Parse trading data from the specified file."""
#     # Read the trading data file
#     with open(os.path.join('data', filename), 'r') as file:
#         lines = file.readlines()

#     # Helper function to extract expiration date from option symbol
#     def extract_expiration_date(description):
#         try:
#             # Split the description and look for the date part (e.g., "04APR25")
#             parts = description.split()
#             for part in parts:
#                 if len(part) == 7 and part[0:2].isdigit() and part[2:5].isalpha() and part[5:].isdigit():
#                     # Convert to datetime and format
#                     from datetime import datetime
#                     date = datetime.strptime(part, '%d%b%y')
#                     return date.strftime('%Y-%m-%d')
#         except:
#             return None
#         return None

#     # Helper function to extract strike price from option symbol
#     def extract_strike_price(description):
#         try:
#             # Split the description and look for the strike price (e.g., "175" in "GOOG 04APR25 175 P")
#             parts = description.split()
#             for i, part in enumerate(parts):
#                 if i > 0 and part.replace('.', '').isdigit():  # Check if it's a number (including decimals)
#                     return float(part)
#         except:
#             return None
#         return None

#     # Helper function to extract option type (P or C)
#     def extract_option_type(description):
#         try:
#             return description.split()[-1]  # Last part is P or C
#         except:
#             return None

#     # Parse different sections
#     sections = {}
#     current_section = None
#     current_data = []

#     for line in lines:
#         line = line.strip()
#         if not line:
#             continue

#         if line in ['ACCOUNT_INFORMATION', 'STOCK_TRANSACTIONS', 'OPTION_TRANSACTIONS',
#                    'STOCK_POSITIONS', 'OPTION_POSITIONS', 'EOF']:
#             if current_section:
#                 sections[current_section] = current_data
#             current_section = line
#             current_data = []
#         else:
#             current_data.append(line)

#     # Convert sections to DataFrames
#     dfs = {}

#     # Parse account information
#     if 'ACCOUNT_INFORMATION' in sections and sections['ACCOUNT_INFORMATION']:
#         account_info = sections['ACCOUNT_INFORMATION'][0].split('|')
#         if len(account_info) >= 5:  # Make sure we have enough fields
#             dfs['account_info'] = pd.DataFrame([{
#                 'Account ID': account_info[1],
#                 'Name': account_info[2],
#                 'Type': account_info[3],
#                 'Address': ' '.join(account_info[4:])  # Join remaining fields as address
#             }])

#     # Parse transactions and positions
#     for section in ['STOCK_TRANSACTIONS', 'OPTION_TRANSACTIONS', 'STOCK_POSITIONS', 'OPTION_POSITIONS']:
#         if section in sections and sections[section]:
#             # Get headers based on section type
#             if section == 'STOCK_TRANSACTIONS':
#                 headers = ['Type', 'ID', 'Symbol', 'Description', 'Exchange', 'Action', 'Status',
#                           'Date', 'Time', 'Currency', 'Quantity', 'Multiplier', 'Price', 'Amount', 'Fee']
#             elif section == 'OPTION_TRANSACTIONS':
#                 headers = ['Type', 'ID', 'Symbol', 'Description', 'Exchange', 'Action', 'Status',
#                           'Date', 'Time', 'Currency', 'Quantity', 'Multiplier', 'Price', 'Amount', 'Fee']
#             elif section == 'STOCK_POSITIONS':
#                 headers = ['Type', 'Account', 'Symbol', 'Description', 'Currency', 'Empty', 'Time', 'Quantity',
#                           'Multiplier', 'Price', 'Amount']
#             else:  # OPTION_POSITIONS
#                 headers = ['Type', 'Account', 'Symbol', 'Description', 'Currency', 'Empty', 'Time', 'Quantity', 'Shares',
#                            'Premium', 'Amount']

#             # Convert to DataFrame
#             data = [line.split('|') for line in sections[section]]
#             # Ensure all rows have the same number of columns as headers
#             data = [row[:len(headers)] if len(row) > len(headers) else row + [''] * (len(headers) - len(row)) for row in data]
#             df = pd.DataFrame(data, columns=headers)

#             # Convert numeric columns to float
#             numeric_columns = ['Quantity', 'Multiplier',
#                                'Price', 'Amount', 'Shares', 'Premium', 'Fee']
#             for col in numeric_columns:
#                 if col in df.columns:
#                     df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

#             # Add expiration date and strike price for options
#             if section in ['OPTION_TRANSACTIONS', 'OPTION_POSITIONS']:
#                 df['Expiration'] = df['Description'].apply(extract_expiration_date)
#                 df['Strike'] = df['Description'].apply(extract_strike_price)
#                 df['Type'] = df['Description'].apply(extract_option_type)

#                 # For positions, calculate the total premium (price * multiplier)
#                 # if section == 'OPTION_POSITIONS':
#                 #     df['Price'] = df['Price'] * df['Multiplier']  # Multiply by 100 to get total premium

#             dfs[section.lower()] = df

#         # After creating all DataFrames, calculate analytics and summaries
#     if 'option_transactions' in dfs:
#         dfs['trading_analytics'] = calculate_trading_analytics(dfs['option_transactions'])
#         dfs['option_summary'] = calculate_option_summary(dfs['option_transactions'])

#     if 'option_positions' in dfs:
#         dfs['option_positions_summary'] = calculate_option_positions_summary(dfs['option_positions'])
#         # Add expiration alerts
#         dfs['expiration_alerts'] = calculate_expiration_alerts(dfs['option_positions'])

#     return dfs

# def aggregate_complex_option_trades(option_transactions):
    """
    Aggregate option transactions into complex (multi-leg) trades.
    Returns a list of complex trades, each with legs and summary metrics.
    """
    if option_transactions is None or option_transactions.empty:
        return []

    # Ensure Date is datetime
    option_transactions = option_transactions.copy()
    option_transactions['Date'] = pd.to_datetime(option_transactions['Date'], format='%Y%m%d', errors='coerce')

    # Group by Symbol and Expiration to find related trades
    grouped = option_transactions.groupby(['Symbol', 'Expiration'])

    complex_trades = []

    for (symbol, expiration), group in grouped:
        if len(group) < 2:
            continue  # Need at least 2 legs for a complex trade
        # Sort by date
        group = group.sort_values('Date')
        # Classify type (very basic)
        types = set(group['Type'])
        strikes = set(group['Strike'])
        trade_type = 'Custom'
        if len(group) == 2:
            if len(types) == 1 and len(strikes) == 2:
                trade_type = 'Vertical Spread'
            elif len(types) == 2 and len(strikes) == 1:
                trade_type = 'Straddle'
            elif len(types) == 2 and len(strikes) == 2:
                trade_type = 'Strangle'
        elif len(group) == 4:
            trade_type = 'Iron Condor'
        # Aggregate metrics
        net_amount = group['Amount'].sum()
        net_fees = group['Fee'].sum() if 'Fee' in group.columns else 0
        open_date = group['Date'].min()
        close_date = group['Date'].max()
        summary = {
            'Symbol': symbol,
            'Expiration': expiration,
            'Open_Date': open_date,
            'Close_Date': close_date,
            'Num_Legs': len(group),
            'Trade_Type': trade_type,
            'Net_Amount': net_amount,
            'Net_Fees': net_fees,
            'Legs': group.to_dict('records'),
        }
        complex_trades.append(summary)
    # Sort by open date descending
    complex_trades = sorted(complex_trades, key=lambda x: x['Open_Date'], reverse=True)
    return complex_trades

def parse_performance_data(performance_data):
    """Parse IBKR performance data into a clean format for display"""
    if not performance_data:
        return {}

    try:
        # Extract NAV data
        nav_data = performance_data.get('nav', {}).get('data', [])
        if nav_data:
            nav_info = nav_data[0]
            current_nav = nav_info.get('navs', [0])[0] if nav_info.get('navs') else 0
            start_nav = nav_info.get('startNAV', {}).get('val', 0)
            nav_change = current_nav - start_nav
            nav_change_pct = (nav_change / start_nav * 100) if start_nav != 0 else 0
        else:
            current_nav = start_nav = nav_change = nav_change_pct = 0

        # Extract returns data
        returns_data = performance_data.get('cps', {}).get('data', [])
        if returns_data:
            returns = returns_data[0].get('returns', [0])[0] if returns_data[0].get('returns') else 0
            returns_pct = returns * 100
        else:
            returns = returns_pct = 0

        # Extract dates
        start_date = performance_data.get('nav', {}).get('data', [{}])[0].get('start', '')
        end_date = performance_data.get('nav', {}).get('data', [{}])[0].get('end', '')

        return {
            'current_nav': current_nav,
            'start_nav': start_nav,
            'nav_change': nav_change,
            'nav_change_pct': nav_change_pct,
            'returns': returns,
            'returns_pct': returns_pct,
            'start_date': start_date,
            'end_date': end_date,
            'currency': performance_data.get('nav', {}).get('data', [{}])[0].get('baseCurrency', 'USD')
        }
    except Exception as e:
        print(f"Error parsing performance data: {e}")
        return {}

def get_ibkr_data():
    dfs = {}

    print(f"DEBUG: get_ibkr_data called at {datetime.now()}")
    print(f"DEBUG: Current connection status: {connection_status}")

    # Check connection status first
    if not connection_status['connected']:
        print(f"DEBUG: Connection not connected, attempting to reconnect")
        # Try to reconnect
        check_ibkr_connection()
    else:
        print(f"DEBUG: Connection already connected")

    # Initialize with connection status
    dfs['connection_status'] = {
        'connected': connection_status['connected'],
        'error_message': connection_status['error_message'],
        'last_check': connection_status['last_check'].isoformat() if connection_status['last_check'] else None,
        'retry_count': connection_status['retry_count'],
        'gateway_url': IBKR_GATEWAY_LOGIN_URL
    }

    # If not connected, return minimal data with error info
    if not connection_status['connected']:
        dfs['account_status'] = {
            'connection_status': 'Disconnected',
            'error_message': connection_status['error_message'],
            'balances': {}
        }
        dfs['performance'] = {}
        dfs['positions'] = pd.DataFrame()
        dfs['position_analytics'] = calculate_position_analytics(pd.DataFrame())
        dfs['put_analysis'] = calculate_put_annualized_returns(pd.DataFrame())
        return dfs

    # Fetch account details safely
    account_details, error = safe_ibkr_call(fetch_ibkr_account_details)
    if error:
        print(f"Error fetching account details: {error}")
        account_details = None

    # Parse account information
    status_data = {
        'connection_status': 'Connected' if account_details else 'Disconnected',
        'balances': {}
    }

    # Parse account details
    if account_details:
        dfs['account_info'] = {
            'account_id': account_details.get('accountId', ''),
            'name': account_details.get('displayName', ''),
            'type': account_details.get('type', ''),
            'currency': account_details.get('currency', 'USD')
        }
    else:
        dfs['account_info'] = {}

    # Get account status and balances safely
    account_ledger, error = safe_ibkr_call(fetch_ibkr_account_ledger)
    if error:
        print(f"Error fetching account ledger: {error}")
        account_ledger = {}

    # Parse account ledger (if available)
    if account_ledger:
        for currency, subledger in account_ledger.items():
            if currency not in ['USD']:
                continue
            status_data['balances'][currency] = {
                'ledger_balance': subledger.get('cashbalance', 0),
                'settled_balance': subledger.get('netliquidationvalue', 0),
                'pending_balance': subledger.get('stockmarketvalue', 0)
            }

    dfs['account_status'] = status_data

    # Get account performance for different periods safely
    performance_data = {}
    periods = ["1D", "7D", "MTD", "YTD"]
    for period in periods:
        try:
            perf, error = safe_ibkr_call(fetch_ibkr_account_performance, period=period)
            if error:
                print(f"Error fetching {period} performance: {error}")
                performance_data[period] = {}
            else:
                performance_data[period] = parse_performance_data(perf)
        except Exception as e:
            print(f"Error fetching {period} performance: {e}")
            performance_data[period] = {}

    dfs['performance'] = performance_data

    # Get positions safely
    positions, error = safe_ibkr_call(fetch_ibkr_positions)
    if error:
        print(f"Error fetching positions: {error}")
        positions = []

    if positions and len(positions) > 0:  # Check if list is not empty
        # Keep all original IBKR fields - no field renaming
        df = pd.DataFrame(positions)

        # Convert numeric columns to float where appropriate
        numeric_columns = ['position', 'mktPrice', 'mktValue', 'avgCost', 'avgPrice',
                          'realizedPnl', 'unrealizedPnl', 'multiplier', 'strike']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        dfs['positions'] = df

        # Calculate position analytics using original field names
        dfs['position_analytics'] = calculate_position_analytics(df)

        # Calculate put annualized returns using original field names
        dfs['put_analysis'] = calculate_put_annualized_returns(df)
    else:
        # Return empty DataFrames and analytics when no positions
        dfs['positions'] = pd.DataFrame()
        dfs['position_analytics'] = calculate_position_analytics(pd.DataFrame())
        dfs['put_analysis'] = calculate_put_annualized_returns(pd.DataFrame())

    return dfs

def calculate_position_analytics(positions_df):
    """Calculate analytics for open positions including P&L, cost basis, etc."""
    if positions_df.empty:
        return {
            'total_positions': 0,
            'total_value': 0,
            'total_cost': 0,
            'unrealized_pnl': 0,
            'unrealized_pnl_pct': 0,
            'long_positions': 0,
            'short_positions': 0,
            'option_positions': 0,
            'stock_positions': 0,
            'largest_position': None,
            'most_profitable': None,
            'least_profitable': None,
            'positions_by_type': {},
            'risk_metrics': {
                'largest_loss': 0,
                'largest_gain': 0,
                'avg_position_size': 0
            }
        }

    analytics = {
        'total_positions': len(positions_df),
        'total_value': 0,
        'total_cost': 0,
        'unrealized_pnl': 0,
        'unrealized_pnl_pct': 0,
        'long_positions': 0,
        'short_positions': 0,
        'option_positions': 0,
        'stock_positions': 0,
        'largest_position': None,
        'most_profitable': None,
        'least_profitable': None,
        'positions_by_type': {},
        'risk_metrics': {
            'largest_loss': 0,
            'largest_gain': 0,
            'avg_position_size': 0
        }
    }

    # Calculate metrics for each position using original IBKR field names
    for _, position in positions_df.iterrows():
        quantity = position.get('position', 0)
        current_price = position.get('mktPrice', 0)
        cost_basis = position.get('avgCost', 0)  # Original IBKR field
        position_type = position.get('putOrCall', '')  # Original IBKR field
        asset_class = position.get('assetClass', '')  # Original IBKR field
        unrealized_pnl = position.get('unrealizedPnl', 0)  # Original IBKR field
        mkt_value = position.get('mktValue', 0)  # Original IBKR field

        # Calculate position value
        position_value = abs(mkt_value) if mkt_value != 0 else abs(quantity) * current_price

        # Update totals
        analytics['total_value'] += position_value
        analytics['total_cost'] += abs(cost_basis)
        analytics['unrealized_pnl'] += unrealized_pnl

        # Count position types
        if quantity > 0:
            analytics['long_positions'] += 1
        else:
            analytics['short_positions'] += 1

        if asset_class == 'OPT':
            analytics['option_positions'] += 1
        else:
            analytics['stock_positions'] += 1

        # Track largest position by value
        if not analytics['largest_position'] or position_value > analytics['largest_position']['value']:
            analytics['largest_position'] = {
                'symbol': position.get('ticker', ''),
                'value': position_value,
                'quantity': quantity,
                'type': position_type
            }

        # Track most/least profitable positions
        if not analytics['most_profitable'] or unrealized_pnl > analytics['most_profitable']['pnl']:
            analytics['most_profitable'] = {
                'symbol': position.get('ticker', ''),
                'pnl': unrealized_pnl,
                'pnl_pct': (unrealized_pnl / abs(cost_basis) * 100) if cost_basis != 0 else 0
            }

        if not analytics['least_profitable'] or unrealized_pnl < analytics['least_profitable']['pnl']:
            analytics['least_profitable'] = {
                'symbol': position.get('ticker', ''),
                'pnl': unrealized_pnl,
                'pnl_pct': (unrealized_pnl / abs(cost_basis) * 100) if cost_basis != 0 else 0
            }

        # Update risk metrics
        if unrealized_pnl > analytics['risk_metrics']['largest_gain']:
            analytics['risk_metrics']['largest_gain'] = unrealized_pnl
        if unrealized_pnl < analytics['risk_metrics']['largest_loss']:
            analytics['risk_metrics']['largest_loss'] = unrealized_pnl

    # Calculate percentage P&L
    if analytics['total_cost'] > 0:
        analytics['unrealized_pnl_pct'] = (analytics['unrealized_pnl'] / analytics['total_cost']) * 100

    # Calculate average position size
    if analytics['total_positions'] > 0:
        analytics['risk_metrics']['avg_position_size'] = analytics['total_value'] / analytics['total_positions']

    # Group positions by type
    for _, position in positions_df.iterrows():
        position_type = position.get('putOrCall', 'STOCK')  # STOCK if putOrCall is None
        if position_type not in analytics['positions_by_type']:
            analytics['positions_by_type'][position_type] = {
                'count': 0,
                'total_value': 0,
                'total_pnl': 0
            }

        quantity = position.get('position', 0)
        current_price = position.get('mktPrice', 0)
        cost_basis = position.get('avgCost', 0)
        position_value = abs(quantity) * current_price
        unrealized_pnl = position.get('unrealizedPnl', 0)

        analytics['positions_by_type'][position_type]['count'] += 1
        analytics['positions_by_type'][position_type]['total_value'] += position_value
        analytics['positions_by_type'][position_type]['total_pnl'] += unrealized_pnl

    return analytics

def calculate_put_annualized_returns(positions_df):
    """Calculate annualized returns for put positions and identify those to close (< 12%)"""
    if positions_df.empty:
        return {
            'put_positions': [],
            'positions_to_close': [],
            'total_collateral_tied': 0,
            'avg_annualized_return': 0
        }

    put_positions = []
    positions_to_close = []
    total_collateral = 0

    for _, position in positions_df.iterrows():
        position_type = position.get('putOrCall', '')  # Original IBKR field
        asset_class = position.get('assetClass', '')  # Original IBKR field

        # Only process put positions
        if position_type != 'P' or asset_class != 'OPT':
            continue

        symbol = position.get('ticker', '')  # Original IBKR field
        quantity = position.get('position', 0)  # Original IBKR field
        premium = position.get('avgPrice', 0)  # Original IBKR field - premium received
        mkt_value = position.get('mktValue', 0)  # Original IBKR field - current market value
        expiration = position.get('expiry', '')  # Original IBKR field
        description = position.get('fullName', '')  # Original IBKR field
        strike = position.get('strike', 0)  # Original IBKR field

        # Skip if missing critical data
        if not all([premium, mkt_value, strike, expiration, quantity]):
            continue

        try:
            # Convert date format from YYYYMMDD to YYYY-MM-DD
            if len(expiration) == 8:  # YYYYMMDD format
                exp_date = datetime.strptime(expiration, '%Y%m%d')
            else:
                exp_date = datetime.strptime(expiration, '%Y-%m-%d')

            days_left = (exp_date - datetime.now()).days + 1

            if days_left <= 0:
                continue  # Skip expired positions

            # Calculate collateral (strike price * 100 * quantity for puts)
            collateral_per_contract = strike * 100
            total_collateral_for_position = abs(quantity) * collateral_per_contract
            total_collateral += total_collateral_for_position

            # Use IBKR's unrealizedPnl for correct P&L (this is total for all contracts)
            unrealized_pnl = position.get('unrealizedPnl', 0)

            # Calculate per-contract values for consistent calculation
            premium_per_contract = premium  # avgPrice is already per contract
            mkt_value_per_contract = abs(mkt_value) / abs(quantity) if quantity != 0 else 0
            unrealized_pnl_per_contract = unrealized_pnl / abs(quantity) if quantity != 0 else 0

            # Calculate annualized return per contract
            # Formula: (Market Value per contract / Collateral per contract) * (365 / Days Left) * 100
            if collateral_per_contract > 0 and days_left > 0:
                annualized_return = (mkt_value_per_contract / collateral_per_contract) * (365 / days_left) * 100
            else:
                annualized_return = 0

            put_position = {
                'symbol': symbol,
                'quantity': quantity,
                'strike': strike,
                'premium': premium_per_contract,
                'mkt_value': mkt_value_per_contract,  # Per contract
                'current_pnl': unrealized_pnl_per_contract,
                'expiration': exp_date.strftime('%Y-%m-%d'),
                'days_left': days_left,
                'collateral': collateral_per_contract,
                'annualized_return': annualized_return,
                'should_close': annualized_return < 12
            }

            put_positions.append(put_position)

            # Add to close list if return < 12%
            if annualized_return < 12:
                positions_to_close.append(put_position)

        except Exception as e:
            print(f"Error calculating return for {symbol}: {e}")
            continue

    # Calculate average annualized return
    avg_return = 0
    if put_positions:
        avg_return = sum(p['annualized_return'] for p in put_positions) / len(put_positions)

    return {
        'put_positions': put_positions,
        'positions_to_close': positions_to_close,
        'total_collateral_tied': total_collateral,
        'avg_annualized_return': avg_return
    }


@app.route('/')
def index():
    try:
        trading_data = get_ibkr_data()
        return render_template('index.html', data=trading_data)
    except Exception as e:
        # Log the error and return a user-friendly error page
        print(f"Error in main route: {e}")
        error_data = {
            'connection_status': {
                'connected': False,
                'error_message': f"Dashboard Error: {str(e)}",
                'last_check': datetime.now().isoformat(),
                'retry_count': 0,
                'gateway_url': IBKR_GATEWAY_LOGIN_URL
            },
            'account_status': {
                'connection_status': 'Error',
                'error_message': str(e),
                'balances': {}
            },
            'performance': {},
            'positions': pd.DataFrame(),
            'position_analytics': calculate_position_analytics(pd.DataFrame()),
            'put_analysis': calculate_put_annualized_returns(pd.DataFrame())
        }
        return render_template('index.html', data=error_data)

@app.route('/api/connection-status')
def api_connection_status():
    """API endpoint to check connection status"""
    return jsonify(connection_status)

@app.route('/api/reconnect')
def api_reconnect():
    """API endpoint to attempt reconnection"""
    try:
        success = check_ibkr_connection()
        return jsonify({
            'success': success,
            'connected': connection_status['connected'],
            'error_message': connection_status['error_message'],
            'retry_count': connection_status['retry_count']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh-data', methods=['GET', 'POST'])
def api_refresh_data():
    """API endpoint to refresh all data"""
    try:
        trading_data = get_ibkr_data()
        return jsonify({
            'success': True,
            'data': trading_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug-connection')
def api_debug_connection():
    """Debug endpoint to check connection details"""
    try:
        # Test direct connection
        account_details = fetch_ibkr_account_details()
        tickle_result = None
        try:
            fetch_ibkr_tickle()
            tickle_result = "Success"
        except Exception as e:
            tickle_result = f"Failed: {str(e)}"

        return jsonify({
            'connection_status': connection_status,
            'gateway_url': IBKR_GATEWAY_LOGIN_URL,
            'direct_account_details': account_details is not None,
            'tickle_result': tickle_result,
            'environment': {
                'IBKR_GATEWAY_URL': os.environ.get('IBKR_GATEWAY_URL', 'Not set'),
                'IBIND_PORT': os.environ.get('IBIND_PORT', 'Not set'),
                'IBIND_ACCOUNT_ID': os.environ.get('IBIND_ACCOUNT_ID', 'Not set')
            }
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/tickle-control', methods=['POST'])
def api_tickle_control():
    """API endpoint to control tickle behavior"""
    try:
        data = request.get_json()
        action = data.get('action')

        if action == 'enable':
            connection_status['tickle_enabled'] = True
            return jsonify({'success': True, 'message': 'Tickle enabled'})
        elif action == 'disable':
            connection_status['tickle_enabled'] = False
            return jsonify({'success': True, 'message': 'Tickle disabled'})
        elif action == 'status':
            return jsonify({
                'success': True,
                'tickle_enabled': connection_status.get('tickle_enabled', True),
                'connected': connection_status.get('connected', False),
                'retry_count': connection_status.get('retry_count', 0)
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Use 0.0.0.0 to make the server externally visible
    app.run(host='0.0.0.0', port=5000, debug=True)
