from datetime import datetime, timedelta
import pandas as pd

def test_put_calculation():
    """Test the put calculation logic with sample data"""

    # Sample put position data (similar to IBKR format)
    sample_put = {
        'ticker': 'SOFI',
        'position': -2.0,  # Short 2 contracts
        'strike': 13.0,
        'avgPrice': 0.29,  # Premium received per contract
        'mktValue': -39.42,  # Total market value (negative for short)
        'unrealizedPnl': 18.58,  # Total unrealized P&L
        'expiry': '20250718'
    }

    print("=== PUT CALCULATION TEST ===")
    print(f"Sample Put Position: {sample_put['ticker']}")
    print(f"Quantity: {sample_put['position']} contracts")
    print(f"Strike: ${sample_put['strike']}")
    print(f"Premium per contract: ${sample_put['avgPrice']}")
    print(f"Total market value: ${sample_put['mktValue']}")
    print(f"Total unrealized P&L: ${sample_put['unrealizedPnl']}")

    # Calculate per-contract values
    quantity = abs(sample_put['position'])
    premium_per_contract = sample_put['avgPrice']
    mkt_value_per_contract = abs(sample_put['mktValue']) / quantity
    unrealized_pnl_per_contract = sample_put['unrealizedPnl'] / quantity
    collateral_per_contract = sample_put['strike'] * 100

    print(f"\nPer-Contract Calculations:")
    print(f"Premium per contract: ${premium_per_contract}")
    print(f"Market value per contract: ${mkt_value_per_contract:.2f}")
    print(f"Unrealized P&L per contract: ${unrealized_pnl_per_contract:.2f}")
    print(f"Collateral per contract: ${collateral_per_contract}")

    # Calculate days to expiration
    exp_date = datetime.strptime(sample_put['expiry'], '%Y%m%d')
    days_left = (exp_date - datetime.now()).days

    print(f"\nTime Analysis:")
    print(f"Expiration: {exp_date.strftime('%Y-%m-%d')}")
    print(f"Days left: {days_left}")

    # Calculate annualized return
    if collateral_per_contract > 0 and days_left > 0:
        annualized_return = (mkt_value_per_contract / collateral_per_contract) * (365 / days_left) * 100
    else:
        annualized_return = 0

    print(f"\nAnnualized Return Calculation:")
    print(f"Formula: (${mkt_value_per_contract:.2f} / ${collateral_per_contract}) * (365 / {days_left}) * 100")
    print(f"Annualized Return: {annualized_return:.2f}%")
    print(f"Should Close (< 12%): {annualized_return < 12}")

    # Verify the math
    print(f"\nVerification:")
    print(f"Total premium received: ${premium_per_contract * quantity:.2f}")
    print(f"Total market value: ${mkt_value_per_contract * quantity:.2f}")
    print(f"Total P&L: ${premium_per_contract * quantity - mkt_value_per_contract * quantity:.2f}")
    print(f"IBKR Total P&L: ${sample_put['unrealizedPnl']}")

    return annualized_return

if __name__ == "__main__":
    test_put_calculation()
