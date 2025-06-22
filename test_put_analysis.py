import pandas as pd
from datetime import datetime, timedelta
from app import calculate_put_annualized_returns

def test_put_analysis():
    # Create sample put position data
    today = datetime.now()

    sample_positions = pd.DataFrame([
        {
            'Symbol': 'SPY',
            'Type': 'P',
            'Quantity': -10,  # Short put
            'Premium': 2.50,
            'Strike': 400.00,
            'Expiration': (today + timedelta(days=30)).strftime('%Y-%m-%d'),  # 30 days
            'Description': 'SPY 400 Put'
        },
        {
            'Symbol': 'QQQ',
            'Type': 'P',
            'Quantity': -5,   # Short put
            'Premium': 1.80,
            'Strike': 350.00,
            'Expiration': (today + timedelta(days=45)).strftime('%Y-%m-%d'),  # 45 days
            'Description': 'QQQ 350 Put'
        },
        {
            'Symbol': 'IWM',
            'Type': 'P',
            'Quantity': -15,  # Short put
            'Premium': 0.90,
            'Strike': 180.00,
            'Expiration': (today + timedelta(days=60)).strftime('%Y-%m-%d'),  # 60 days
            'Description': 'IWM 180 Put'
        },
        {
            'Symbol': 'AAPL',
            'Type': 'STOCK',  # This should be ignored
            'Quantity': 100,
            'Premium': 0,
            'Strike': 150.00,
            'Expiration': '',
            'Description': 'Apple Stock'
        }
    ])

    print("Sample Put Positions:")
    print(sample_positions)
    print("\n" + "="*60)

    # Calculate put analysis
    analysis = calculate_put_annualized_returns(sample_positions)

    print("Put Analysis Results:")
    print(f"Total Put Positions: {len(analysis['put_positions'])}")
    print(f"Positions to Sell (< 12%): {len(analysis['positions_to_sell'])}")
    print(f"Total Collateral Tied: ${analysis['total_collateral_tied']:,.2f}")
    print(f"Average Annualized Return: {analysis['avg_annualized_return']:.2f}%")

    print(f"\nDetailed Put Positions:")
    for i, put in enumerate(analysis['put_positions'], 1):
        print(f"\n{i}. {put['symbol']} {put['strike']} Put")
        print(f"   Expiration: {put['expiration']} ({put['days_left']} days left)")
        print(f"   Quantity: {put['quantity']}")
        print(f"   Premium: ${put['premium']:.2f}")
        print(f"   Collateral: ${put['collateral']:,.2f}")
        print(f"   Annualized Return: {put['annualized_return']:.2f}%")
        print(f"   Should Sell: {'YES' if put['should_sell'] else 'NO'}")

    if analysis['positions_to_sell']:
        print(f"\n🚨 POSITIONS TO SELL (Return < 12%):")
        for put in analysis['positions_to_sell']:
            print(f"   - {put['symbol']}: {put['annualized_return']:.2f}% return")
    else:
        print(f"\n✅ All put positions have returns >= 12%")

if __name__ == "__main__":
    test_put_analysis()
