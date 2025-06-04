from flask import Flask, render_template, request
import pandas as pd
import os
import glob
from datetime import datetime

app = Flask(__name__)

def calculate_trading_analytics(transactions_df):
    """Calculate various trading analytics from the transactions data."""
    analytics = {}

    # Convert date strings to datetime
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'], format='%Y%m%d')

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

def calculate_option_summary(transactions_df):
    """Calculate summary statistics for option transactions based on their type."""
    summary = {
        'total_transactions': len(transactions_df),
        'total_premium': 0,
        'total_fees': transactions_df['Fee'].sum(),
        'net_pnl': 0,
        'open_positions': 0,
        'closed_positions': 0
    }

    # Group by trade identifier (symbol + expiration + strike + type)
    transactions_df['Trade_Group'] = transactions_df.apply(
        lambda row: f"{row['Symbol']}_{row['Description'].split()[1]}_{row['Description'].split()[2]}_{row['Description'].split()[-1]}",
        axis=1
    )

    # Calculate summary by trade group
    trade_groups = transactions_df.groupby('Trade_Group')
    for group_name, group in trade_groups:
        group = group.sort_values('Date')
        first_trade = group.iloc[0]
        last_trade = group.iloc[-1]

        # Calculate premium based on trade direction
        if first_trade['Action'] == 'BUYTOOPEN':
            entry_premium = first_trade['Amount']  # Positive (cost to buy)
            entry_fee = first_trade['Fee']  # Fee for entry
            if len(group) > 1:  # Closed position
                exit_premium = -last_trade['Amount']  # Negative (value received from sell)
                exit_fee = last_trade['Fee']  # Fee for exit
                trade_pnl = exit_premium - entry_premium - entry_fee - exit_fee
                summary['net_pnl'] += trade_pnl
                summary['closed_positions'] += 1
            else:  # Open position
                summary['net_pnl'] -= (entry_premium + entry_fee)
                summary['open_positions'] += 1
        else:  # SELLTOOPEN
            entry_premium = -first_trade['Amount']  # Positive (value received from sell)
            entry_fee = first_trade['Fee']  # Fee for entry
            if len(group) > 1:  # Closed position
                exit_premium = last_trade['Amount']  # Positive (cost to buy back)
                exit_fee = last_trade['Fee']  # Fee for exit
                trade_pnl = entry_premium - exit_premium - entry_fee - exit_fee
                summary['net_pnl'] += trade_pnl
                summary['closed_positions'] += 1
            else:  # Open position
                summary['net_pnl'] += (entry_premium - entry_fee)
                summary['open_positions'] += 1

    return summary

def calculate_option_positions_summary(positions_df):
    """Calculate summary statistics for current option positions."""
    summary = {
        'total_positions': len(positions_df),
        'total_value': 0,
        'long_positions': 0,
        'short_positions': 0,
        'total_fees': 0  # Fees for open positions
    }

    for _, position in positions_df.iterrows():
        quantity = position['Quantity']
        amount = position['Amount']
        fee = position['Fee'] if 'Fee' in position else 0

        # For long positions (positive quantity), amount is negative (cost)
        # For short positions (negative quantity), amount is negative (credit)
        if quantity > 0:  # Long position
            summary['total_value'] -= amount  # Subtract cost (amount is negative)
            summary['long_positions'] += 1
        else:  # Short position
            summary['total_value'] -= amount  # Subtract credit (amount is negative, so this adds the credit)
            summary['short_positions'] += 1

        summary['total_fees'] += fee

    return summary

def get_available_data_files():
    """Get list of available .tlg files in the data directory."""
    return [os.path.basename(f) for f in glob.glob('data/*.tlg')]

def parse_trading_data(filename='trading_data.tlg'):
    """Parse trading data from the specified file."""
    # Read the trading data file
    with open(os.path.join('data', filename), 'r') as file:
        lines = file.readlines()

    # Helper function to extract expiration date from option symbol
    def extract_expiration_date(description):
        try:
            # Split the description and look for the date part (e.g., "04APR25")
            parts = description.split()
            for part in parts:
                if len(part) == 7 and part[0:2].isdigit() and part[2:5].isalpha() and part[5:].isdigit():
                    # Convert to datetime and format
                    from datetime import datetime
                    date = datetime.strptime(part, '%d%b%y')
                    return date.strftime('%Y-%m-%d')
        except:
            return None
        return None

    # Helper function to extract strike price from option symbol
    def extract_strike_price(description):
        try:
            # Split the description and look for the strike price (e.g., "175" in "GOOG 04APR25 175 P")
            parts = description.split()
            for i, part in enumerate(parts):
                if i > 0 and part.replace('.', '').isdigit():  # Check if it's a number (including decimals)
                    return float(part)
        except:
            return None
        return None

    # Helper function to extract option type (P or C)
    def extract_option_type(description):
        try:
            return description.split()[-1]  # Last part is P or C
        except:
            return None

    # Parse different sections
    sections = {}
    current_section = None
    current_data = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line in ['ACCOUNT_INFORMATION', 'STOCK_TRANSACTIONS', 'OPTION_TRANSACTIONS',
                   'STOCK_POSITIONS', 'OPTION_POSITIONS', 'EOF']:
            if current_section:
                sections[current_section] = current_data
            current_section = line
            current_data = []
        else:
            current_data.append(line)

    # Convert sections to DataFrames
    dfs = {}

    # Parse account information
    if 'ACCOUNT_INFORMATION' in sections and sections['ACCOUNT_INFORMATION']:
        account_info = sections['ACCOUNT_INFORMATION'][0].split('|')
        if len(account_info) >= 5:  # Make sure we have enough fields
            dfs['account_info'] = pd.DataFrame([{
                'Account ID': account_info[1],
                'Name': account_info[2],
                'Type': account_info[3],
                'Address': ' '.join(account_info[4:])  # Join remaining fields as address
            }])

    # Parse transactions and positions
    for section in ['STOCK_TRANSACTIONS', 'OPTION_TRANSACTIONS', 'STOCK_POSITIONS', 'OPTION_POSITIONS']:
        if section in sections and sections[section]:
            # Get headers based on section type
            if section == 'STOCK_TRANSACTIONS':
                headers = ['Type', 'ID', 'Symbol', 'Description', 'Exchange', 'Action', 'Status',
                          'Date', 'Time', 'Currency', 'Quantity', 'Multiplier', 'Price', 'Amount', 'Fee']
            elif section == 'OPTION_TRANSACTIONS':
                headers = ['Type', 'ID', 'Symbol', 'Description', 'Exchange', 'Action', 'Status',
                          'Date', 'Time', 'Currency', 'Quantity', 'Multiplier', 'Price', 'Amount', 'Fee']
            elif section == 'STOCK_POSITIONS':
                headers = ['Type', 'Account', 'Symbol', 'Description', 'Currency', 'Empty', 'Time', 'Quantity',
                          'Multiplier', 'Price', 'Amount']
            else:  # OPTION_POSITIONS
                headers = ['Type', 'Account', 'Symbol', 'Description', 'Currency', 'Empty', 'Time', 'Quantity', 'Shares',
                           'Premium', 'Amount']

            # Convert to DataFrame
            data = [line.split('|') for line in sections[section]]
            # Ensure all rows have the same number of columns as headers
            data = [row[:len(headers)] if len(row) > len(headers) else row + [''] * (len(headers) - len(row)) for row in data]
            df = pd.DataFrame(data, columns=headers)

            # Convert numeric columns to float
            numeric_columns = ['Quantity', 'Multiplier',
                               'Price', 'Amount', 'Shares', 'Premium', 'Fee']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Add expiration date and strike price for options
            if section in ['OPTION_TRANSACTIONS', 'OPTION_POSITIONS']:
                df['Expiration'] = df['Description'].apply(extract_expiration_date)
                df['Strike'] = df['Description'].apply(extract_strike_price)
                df['Type'] = df['Description'].apply(extract_option_type)

                # For positions, calculate the total premium (price * multiplier)
                # if section == 'OPTION_POSITIONS':
                #     df['Price'] = df['Price'] * df['Multiplier']  # Multiply by 100 to get total premium

            dfs[section.lower()] = df

    # After creating all DataFrames, calculate analytics and summaries
    if 'option_transactions' in dfs:
        dfs['trading_analytics'] = calculate_trading_analytics(dfs['option_transactions'])
        dfs['option_summary'] = calculate_option_summary(dfs['option_transactions'])

    if 'option_positions' in dfs:
        dfs['option_positions_summary'] = calculate_option_positions_summary(dfs['option_positions'])

    return dfs

@app.route('/')
def index():
    # Get the requested file from query parameters, default to first available file
    available_files = get_available_data_files()
    if not available_files:
        return render_template('index.html', error="No data files found in data directory")

    requested_file = request.args.get('data_file')
    if requested_file and requested_file in available_files:
        selected_file = requested_file
    else:
        selected_file = available_files[0]  # Default to first file if none selected or invalid

    # Parse the selected file
    trading_data = parse_trading_data(selected_file)

    # Add the list of available files to the template context
    trading_data['available_files'] = available_files
    trading_data['selected_file'] = selected_file

    return render_template('index.html', data=trading_data)

if __name__ == '__main__':
    # Use 0.0.0.0 to make the server externally visible
    app.run(host='0.0.0.0', port=5000, debug=True)
