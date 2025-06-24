from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import threading
import time
from datetime import datetime, timedelta
from ibkr_client import fetch_ibkr_account_details, fetch_ibkr_positions, fetch_ibkr_tickle, fetch_ibkr_account_performance, fetch_ibkr_account_ledger
import math
from scipy.stats import norm

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

def calculate_black_scholes_greeks(S, K, T, r, sigma, option_type='put'):
    """
    Calculate Black-Scholes option Greeks for puts
    S: Current stock price (estimated from strike and premium)
    K: Strike price
    T: Time to expiration in years
    r: Risk-free rate (assume 0.05 for simplicity)
    sigma: Implied volatility (estimated)
    option_type: 'put' or 'call'
    """
    try:
        # Estimate current stock price from strike and premium relationship
        # For puts: if premium is high relative to strike, stock is likely lower
        # Rough estimate: S = K - premium * 2 (for ATM puts)
        if S <= 0:
            S = K - premium * 2  # Rough estimate for stock price

        # Estimate implied volatility from premium
        # For puts: higher premium = higher implied vol
        if sigma <= 0:
            # Rough estimate: sigma = premium / (K * sqrt(T)) * 2
            sigma = max(0.1, min(1.0, premium / (K * math.sqrt(T)) * 2))

        # Ensure reasonable bounds
        sigma = max(0.1, min(1.0, sigma))  # Between 10% and 100%
        T = max(0.01, T)  # At least 1 day

        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)

        if option_type == 'put':
            # Put option Greeks
            delta = norm.cdf(d1) - 1
            gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) -
                    r * K * math.exp(-r*T) * norm.cdf(-d2)) / 365  # Daily theta
            vega = S * math.sqrt(T) * norm.pdf(d1) / 100  # Per 1% change in vol

            # Probability of profit (stock above strike at expiration)
            prob_profit = 1 - norm.cdf(d2)
        else:
            # Call option Greeks (for completeness)
            delta = norm.cdf(d1)
            gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) +
                    r * K * math.exp(-r*T) * norm.cdf(d2)) / 365
            vega = S * math.sqrt(T) * norm.pdf(d1) / 100
            prob_profit = norm.cdf(d2)

        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'prob_profit': prob_profit,
            'implied_vol': sigma
        }
    except Exception as e:
        # Return default values if calculation fails
        return {
            'delta': -0.5,
            'gamma': 0.01,
            'theta': -0.1,
            'vega': 0.1,
            'prob_profit': 0.5,
            'implied_vol': 0.3
        }

def calculate_stress_scenarios(position_data, greeks):
    """
    Calculate P&L under different stress scenarios
    """
    scenarios = {}

    # Base position data
    quantity = position_data['quantity']
    current_pnl = position_data['current_pnl']
    collateral = position_data['collateral']

    # Scenario 1: Stock drops 10%
    stock_drop_10 = {
        'description': 'Stock drops 10%',
        'pnl_change': greeks['delta'] * -0.10 * collateral / 100,  # Delta * price change * position size
        'new_pnl': current_pnl + (greeks['delta'] * -0.10 * collateral / 100),
        'risk_level': 'High' if abs(greeks['delta']) > 0.7 else 'Medium'
    }

    # Scenario 2: Stock drops 20%
    stock_drop_20 = {
        'description': 'Stock drops 20%',
        'pnl_change': greeks['delta'] * -0.20 * collateral / 100,
        'new_pnl': current_pnl + (greeks['delta'] * -0.20 * collateral / 100),
        'risk_level': 'High'
    }

    # Scenario 3: Volatility increases 50%
    vol_increase_50 = {
        'description': 'Volatility +50%',
        'pnl_change': greeks['vega'] * 0.50 * 100,  # Vega * vol change * 100 (for percentage)
        'new_pnl': current_pnl + (greeks['vega'] * 0.50 * 100),
        'risk_level': 'Medium' if abs(greeks['vega']) > 0.05 else 'Low'
    }

    # Scenario 4: Time decay (1 week)
    time_decay_week = {
        'description': '1 week time decay',
        'pnl_change': greeks['theta'] * 7,  # Daily theta * 7 days
        'new_pnl': current_pnl + (greeks['theta'] * 7),
        'risk_level': 'Medium' if abs(greeks['theta']) > 0.05 else 'Low'
    }

    # Scenario 5: Gamma risk (large move)
    gamma_risk = {
        'description': 'Large move risk (gamma)',
        'pnl_change': 0.5 * greeks['gamma'] * (collateral / 100) * 0.05**2,  # 0.5 * gamma * S^2 * price_change^2
        'new_pnl': current_pnl + (0.5 * greeks['gamma'] * (collateral / 100) * 0.05**2),
        'risk_level': 'High' if abs(greeks['gamma']) > 0.02 else 'Medium'
    }

    scenarios = {
        'stock_drop_10': stock_drop_10,
        'stock_drop_20': stock_drop_20,
        'vol_increase_50': vol_increase_50,
        'time_decay_week': time_decay_week,
        'gamma_risk': gamma_risk
    }

    return scenarios

def calculate_put_annualized_returns(positions_df):
    """Calculate annualized returns for put positions and identify those to close (< 12%)"""
    if positions_df.empty:
        return {
            'put_positions': [],
            'positions_to_close': [],
            'total_collateral_tied': 0,
            'avg_annualized_return': 0,
            'risk_summary': {
                'total_delta': 0,
                'total_gamma': 0,
                'total_theta': 0,
                'total_vega': 0,
                'avg_prob_profit': 0,
                'high_risk_positions': 0
            }
        }

    put_positions = []
    positions_to_close = []
    total_collateral = 0

    # Risk metrics aggregation
    total_delta = 0
    total_gamma = 0
    total_theta = 0
    total_vega = 0
    total_prob_profit = 0
    high_risk_positions = 0

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

            # Calculate Greeks and risk metrics
            time_to_expiry = days_left / 365.0  # Convert to years
            risk_free_rate = 0.05  # Assume 5% risk-free rate

            # Estimate current stock price (rough approximation)
            current_stock_price = strike - premium_per_contract * 2  # For ATM puts

            # Calculate implied volatility (rough estimate)
            implied_vol = max(0.1, min(1.0, premium_per_contract / (strike * math.sqrt(time_to_expiry)) * 2))

            # Calculate Greeks
            greeks = calculate_black_scholes_greeks(
                S=current_stock_price,
                K=strike,
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=implied_vol,
                option_type='put'
            )

            # Calculate stress scenarios
            position_data = {
                'quantity': quantity,
                'current_pnl': unrealized_pnl_per_contract,
                'collateral': collateral_per_contract
            }
            stress_scenarios = calculate_stress_scenarios(position_data, greeks)

            # Determine risk level based on Greeks
            risk_level = 'Low'
            if abs(greeks['delta']) > 0.7 or abs(greeks['gamma']) > 0.02 or abs(greeks['theta']) > 0.1:
                risk_level = 'High'
                high_risk_positions += 1
            elif abs(greeks['delta']) > 0.5 or abs(greeks['gamma']) > 0.01 or abs(greeks['theta']) > 0.05:
                risk_level = 'Medium'

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
                'should_close': annualized_return < 12,
                # Enhanced risk metrics
                'greeks': greeks,
                'stress_scenarios': stress_scenarios,
                'risk_level': risk_level,
                'current_stock_price': current_stock_price,
                'implied_volatility': greeks['implied_vol']
            }

            put_positions.append(put_position)

            # Add to close list if return < 12%
            if annualized_return < 12:
                positions_to_close.append(put_position)

            # Aggregate risk metrics
            total_delta += greeks['delta'] * abs(quantity)
            total_gamma += greeks['gamma'] * abs(quantity)
            total_theta += greeks['theta'] * abs(quantity)
            total_vega += greeks['vega'] * abs(quantity)
            total_prob_profit += greeks['prob_profit']

        except Exception as e:
            print(f"Error calculating return for {symbol}: {e}")
            continue

    # Calculate average annualized return
    avg_return = 0
    if put_positions:
        avg_return = sum(p['annualized_return'] for p in put_positions) / len(put_positions)
        total_prob_profit = total_prob_profit / len(put_positions)

    # Risk summary
    risk_summary = {
        'total_delta': total_delta,
        'total_gamma': total_gamma,
        'total_theta': total_theta,
        'total_vega': total_vega,
        'avg_prob_profit': total_prob_profit,
        'high_risk_positions': high_risk_positions,
        'total_positions': len(put_positions)
    }

    return {
        'put_positions': put_positions,
        'positions_to_close': positions_to_close,
        'total_collateral_tied': total_collateral,
        'avg_annualized_return': avg_return,
        'risk_summary': risk_summary
    }

def calculate_stock_concentration_analysis(put_positions):
    """Calculate stock concentration analysis to identify over-investment in specific stocks"""
    if not put_positions:
        return {
            'stock_concentration': [],
            'total_positions': 0,
            'total_collateral': 0,
            'concentration_risk': {
                'high_concentration_stocks': 0,
                'max_concentration': 0,
                'avg_concentration': 0
            }
        }

    # Group positions by stock
    stock_data = {}
    total_collateral = 0
    total_positions = 0

    for position in put_positions:
        symbol = position['symbol']
        collateral = position['collateral'] * abs(position['quantity'])

        if symbol not in stock_data:
            stock_data[symbol] = {
                'symbol': symbol,
                'total_collateral': 0,
                'position_count': 0,
                'total_quantity': 0,
                'avg_annualized_return': 0,
                'total_pnl': 0,
                'positions': []
            }

        stock_data[symbol]['total_collateral'] += collateral
        stock_data[symbol]['position_count'] += 1
        stock_data[symbol]['total_quantity'] += abs(position['quantity'])
        stock_data[symbol]['total_pnl'] += position['current_pnl'] * abs(position['quantity'])
        stock_data[symbol]['positions'].append(position)

        total_collateral += collateral
        total_positions += 1

    # Calculate percentages and risk metrics
    stock_concentration = []
    high_concentration_stocks = 0
    max_concentration = 0
    concentration_sum = 0

    for symbol, data in stock_data.items():
        # Calculate percentage of total collateral
        percentage = (data['total_collateral'] / total_collateral * 100) if total_collateral > 0 else 0

        # Calculate average annualized return for this stock
        avg_return = sum(p['annualized_return'] for p in data['positions']) / len(data['positions'])
        data['avg_annualized_return'] = avg_return

        # Determine concentration risk level
        if percentage > 25:
            risk_level = 'High'
            high_concentration_stocks += 1
        elif percentage > 15:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'

        # Calculate average days to expiration
        avg_days_left = sum(p['days_left'] for p in data['positions']) / len(data['positions'])

        stock_info = {
            'symbol': symbol,
            'percentage': percentage,
            'total_collateral': data['total_collateral'],
            'position_count': data['position_count'],
            'total_quantity': data['total_quantity'],
            'avg_annualized_return': avg_return,
            'total_pnl': data['total_pnl'],
            'avg_days_left': avg_days_left,
            'risk_level': risk_level,
            'is_over_invested': percentage > 20,  # Flag if >20% in single stock
            'positions': data['positions']
        }

        stock_concentration.append(stock_info)
        max_concentration = max(max_concentration, percentage)
        concentration_sum += percentage

    # Sort by percentage (highest first)
    stock_concentration.sort(key=lambda x: x['percentage'], reverse=True)

    # Calculate average concentration
    avg_concentration = concentration_sum / len(stock_concentration) if stock_concentration else 0

    concentration_risk = {
        'high_concentration_stocks': high_concentration_stocks,
        'max_concentration': max_concentration,
        'avg_concentration': avg_concentration,
        'total_stocks': len(stock_concentration)
    }

    return {
        'stock_concentration': stock_concentration,
        'total_positions': total_positions,
        'total_collateral': total_collateral,
        'concentration_risk': concentration_risk
    }

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
        dfs['stock_concentration'] = calculate_stock_concentration_analysis([])
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

        # Calculate stock concentration analysis
        if dfs['put_analysis']['put_positions']:
            dfs['stock_concentration'] = calculate_stock_concentration_analysis(dfs['put_analysis']['put_positions'])
        else:
            dfs['stock_concentration'] = calculate_stock_concentration_analysis([])
    else:
        # Return empty DataFrames and analytics when no positions
        dfs['positions'] = pd.DataFrame()
        dfs['position_analytics'] = calculate_position_analytics(pd.DataFrame())
        dfs['put_analysis'] = calculate_put_annualized_returns(pd.DataFrame())
        dfs['stock_concentration'] = calculate_stock_concentration_analysis([])

    return dfs

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
            'put_analysis': calculate_put_annualized_returns(pd.DataFrame()),
            'stock_concentration': calculate_stock_concentration_analysis([])
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
