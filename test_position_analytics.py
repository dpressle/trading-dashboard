import pandas as pd
from app import calculate_position_analytics

def test_position_analytics():
    # Create sample position data
    sample_positions = pd.DataFrame([
        {
            'Symbol': 'AAPL',
            'Type': 'STOCK',
            'Quantity': 100,
            'Price': 150.00,
            'Amount': 14000.00,  # Cost basis
            'Description': 'Apple Inc'
        },
        {
            'Symbol': 'TSLA',
            'Type': 'STOCK',
            'Quantity': -50,
            'Price': 200.00,
            'Amount': -9000.00,  # Cost basis (negative for short)
            'Description': 'Tesla Inc'
        },
        {
            'Symbol': 'SPY',
            'Type': 'C',
            'Quantity': 10,
            'Price': 5.50,
            'Amount': 600.00,
            'Description': 'SPY 400 Call'
        }
    ])

    print("Sample Positions:")
    print(sample_positions)
    print("\n" + "="*50)

    # Calculate analytics
    analytics = calculate_position_analytics(sample_positions)

    print("Position Analytics Results:")
    print(f"Total Positions: {analytics['total_positions']}")
    print(f"Total Value: ${analytics['total_value']:.2f}")
    print(f"Total Cost: ${analytics['total_cost']:.2f}")
    print(f"Unrealized P&L: ${analytics['unrealized_pnl']:.2f}")
    print(f"P&L %: {analytics['unrealized_pnl_pct']:.2f}%")
    print(f"Long Positions: {analytics['long_positions']}")
    print(f"Short Positions: {analytics['short_positions']}")
    print(f"Option Positions: {analytics['option_positions']}")
    print(f"Stock Positions: {analytics['stock_positions']}")

    if analytics['most_profitable']:
        print(f"Most Profitable: {analytics['most_profitable']['symbol']} (+${analytics['most_profitable']['pnl']:.2f})")

    if analytics['least_profitable']:
        print(f"Least Profitable: {analytics['least_profitable']['symbol']} (${analytics['least_profitable']['pnl']:.2f})")

    if analytics['largest_position']:
        print(f"Largest Position: {analytics['largest_position']['symbol']} (${analytics['largest_position']['value']:.2f})")

    print(f"\nRisk Metrics:")
    print(f"Largest Gain: ${analytics['risk_metrics']['largest_gain']:.2f}")
    print(f"Largest Loss: ${analytics['risk_metrics']['largest_loss']:.2f}")
    print(f"Avg Position Size: ${analytics['risk_metrics']['avg_position_size']:.2f}")

if __name__ == "__main__":
    test_position_analytics()
