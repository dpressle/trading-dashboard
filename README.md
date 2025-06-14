# Trading Dashboard

A comprehensive web-based dashboard for analyzing trading data, with special focus on options trading and complex multi-leg strategies.

## 🚀 Features

### 📊 **Portfolio Overview**
- **Account Summary**: Total value, cash, and margin information
- **Performance Metrics**: P&L tracking, win/loss ratios, and performance charts
- **Position Analysis**: Current holdings with detailed metrics

### 📈 **Trading Analysis**
- **Stock Transactions**: Individual stock trade tracking and analysis
- **Option Transactions**: Detailed options trading history
- **Complex Option Trades**: Multi-leg strategy aggregation and analysis
  - Automatic detection of spreads, straddles, condors, and other complex strategies
  - Credit/Debit analysis with proper profit/loss calculations
  - Trade duration and timeline tracking
  - Individual leg breakdown with visual cards

### 🎯 **Advanced Analytics**
- **Holding Period Analysis**: Categorization and statistics by trade duration
- **Realized P&L**: Profit/loss calculations after fees
- **Trade Structure Analysis**: Buy vs Sell legs, Calls vs Puts breakdown
- **Visual Metrics**: Color-coded cards for quick profit/loss identification

### 💻 **User Interface**
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Bootstrap 5**: Modern, clean interface with professional styling
- **Interactive Modals**: Detailed trade analysis in popup windows
- **Tabbed Navigation**: Organized sections for different data types

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trading_dashboard
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install flask pandas
```

### 4. Create Data Directory
```bash
mkdir -p data
```

### 5. Prepare Your Data
Place your trading data file(s) (`.tlg` format) in the `data/` folder. The application will automatically detect and list all `.tlg` files in the data directory.

#### 📥 **Obtaining .tlg Files**
- **Interactive Brokers**: Export third-party reports from your IBKR account
- **Third-party Tools**: Use IBKR-compatible reporting tools
- **File Format**: Ensure files are in `.tlg` format with pipe-delimited structure
- **Multiple Files**: You can have multiple `.tlg` files for different time periods or accounts

### 6. Run the Application
```bash
python app.py
```

The dashboard will be available at `http://localhost:5000`

## 📁 Project Structure

```
trading_dashboard/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Dashboard template
├── static/               # CSS, JS, and image files
├── data/                 # Trading data files
│   └── *.tlg            # Your trading data files
├── .venv/               # Virtual environment
└── README.md            # This file
```

## 📊 Data Format

The application processes trading data in `.tlg` format, which is a third-party report format used with Interactive Brokers (IBKR) trading platform.

### 📋 **About .tlg Files**
- **Source**: Interactive Brokers third-party reports
- **Format**: Pipe-delimited text files with structured sections
- **Content**: Account information, transactions, and positions
- **Generation**: Can be exported from IBKR platform or third-party tools

### 📁 **File Structure**
Each `.tlg` file contains the following sections:
- **ACCOUNT_INFORMATION**: Account details and personal information
- **STOCK_TRANSACTIONS**: Individual stock trades and transactions
- **OPTION_TRANSACTIONS**: Options trades with detailed contract information
- **STOCK_POSITIONS**: Current stock holdings and positions
- **OPTION_POSITIONS**: Current options positions and contract details

### 📈 **Data Fields**

#### Stock Transactions
- Date, Symbol, Description, Action, Quantity, Price, Amount, Fee

#### Option Transactions
- Date, Symbol, Description, Action, Type, Strike, Expiration, Quantity, Price, Amount, Fee
- **Description Format**: `SYMBOL DDMMMYY STRIKE TYPE` (e.g., "GOOG 04APR25 175 P")
- **Type**: P (Put) or C (Call)
- **Expiration**: Extracted from description (e.g., "04APR25" → "2025-04-04")

### 🔍 **Complex Trade Detection**
The system automatically groups option transactions into complex trades based on:
- Same underlying symbol
- Same expiration date
- Related execution dates
- Multi-leg structure analysis

## 🎯 Usage Guide

### Dashboard Navigation
1. **Portfolio Overview**: View account summary and performance metrics
2. **Recent Transactions**:
   - **Stocks Tab**: Individual stock trades
   - **Options Tab**: Individual option trades
   - **Complex Trades Tab**: Multi-leg option strategies
3. **Holding Period Analysis**: Trade duration statistics

### Complex Trade Analysis
1. Navigate to the "Complex Option Trades" tab
2. Click "View Legs" on any trade to see detailed analysis
3. The modal will show:
   - **Summary Cards**: Net Credit/Debit, Total Fees, Realized P&L, Trade Duration
   - **Trade Structure**: Buy/Sell legs, Calls/Puts breakdown
   - **Trade Timeline**: Start/End dates and duration
   - **Individual Legs**: Detailed cards for each option leg

### Understanding Credit/Debit Logic
- **SELL** options = **Credit** (negative amount = profit)
- **BUY** options = **Debit** (positive amount = loss)
- **Net Credit** = Green card (profitable position)
- **Net Debit** = Red card (costly position)

## 🔧 Technical Details

### Backend (Flask)
- **Data Parsing**: Custom parser for `.tlg` trading data files
- **Complex Trade Aggregation**: Algorithm to group related option transactions
- **Performance Calculations**: P&L, fees, and duration analysis

### Frontend (Bootstrap 5)
- **Responsive Grid**: Mobile-first design approach
- **Interactive Components**: Modals, tabs, and collapsible sections
- **Visual Indicators**: Color-coded cards and badges for quick analysis

### Key Functions
- `parse_trading_data()`: Processes raw trading data
- `aggregate_complex_option_trades()`: Groups multi-leg strategies
- `calculate_holding_period_stats()`: Analyzes trade duration patterns

## 🎨 Customization

### Styling
- Modify `templates/index.html` for layout changes
- Update Bootstrap classes for visual customization
- Add custom CSS in the `<style>` section

### Data Processing
- Edit `app.py` to modify data parsing logic
- Adjust complex trade detection algorithms
- Add new analytics functions

### Adding Features
- New data visualizations can be added to the template
- Additional analysis functions can be implemented in `app.py`
- Custom JavaScript can be added for enhanced interactivity

## 📈 Supported Trading Strategies

The dashboard automatically detects and analyzes:
- **Credit Spreads**: Sell high, buy low strikes
- **Debit Spreads**: Buy high, sell low strikes
- **Iron Condors**: Sell both call and put spreads
- **Straddles**: Buy both call and put at same strike
- **Strangles**: Buy both call and put at different strikes
- **Butterflies**: Three-leg option strategies
- **Calendar Spreads**: Different expiration dates
- **Diagonal Spreads**: Different strikes and expirations

## 🔍 Troubleshooting

### Common Issues
1. **Data File Not Found**: Ensure your `.tlg` file is in the `data/` folder
2. **Import Errors**: Activate the virtual environment before running
3. **Port Already in Use**: Change the port in `app.py` or kill existing processes
4. **Invalid .tlg Format**: Ensure file follows Interactive Brokers third-party report structure
5. **Missing Sections**: .tlg files should contain ACCOUNT_INFORMATION, STOCK_TRANSACTIONS, OPTION_TRANSACTIONS sections

### .tlg File Issues
- **File Not Loading**: Check that the file is properly formatted with pipe-delimited fields
- **Missing Data**: Ensure all required sections are present in the file
- **Date Format**: Dates should be in YYYYMMDD format
- **Option Descriptions**: Should follow format `SYMBOL DDMMMYY STRIKE TYPE`

### Debug Mode
Run with debug output:
```bash
python debug_complex_trades.py
```
The debug script will automatically use the first `.tlg` file found in the `data/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is for personal use and educational purposes.

## ⚖️ Legal Disclaimer

### 📋 **Terms of Use**
This trading dashboard application is provided **"AS IS"** for **personal use and educational purposes only**. By using this software, you acknowledge and agree to the following terms:

### 🚫 **No Financial Advice**
- This application is **NOT** financial advice
- The author is **NOT** a licensed financial advisor
- All trading decisions are **YOUR RESPONSIBILITY**
- Past performance does not guarantee future results

### 🛡️ **Disclaimer of Warranties**
- The software is provided without any warranties, express or implied
- The author makes **NO GUARANTEES** about accuracy, completeness, or reliability
- Data analysis and calculations may contain errors
- The application may not work as expected in all situations

### 💰 **No Liability for Financial Losses**
- The author is **NOT RESPONSIBLE** for any financial losses incurred
- Trading involves substantial risk of loss
- You assume all risks associated with trading decisions
- The author disclaims all liability for trading outcomes

### 🔒 **Personal Use Only**
- This software is intended for **personal use only**
- Commercial use is not authorized
- Redistribution requires explicit permission
- Modification for personal use is permitted

### 📊 **Data Accuracy**
- The application processes data as provided
- No verification of data accuracy is performed
- Users are responsible for validating their data
- The author is not liable for data processing errors

### 🚨 **Risk Warning**
**Trading options and other securities involves substantial risk and is not suitable for all investors. You can lose some or all of your invested capital. Always consult with a qualified financial advisor before making investment decisions.**

---

**Happy Trading! 📈💰**

## 🚀 Future Enhancements

- [ ] Real-time data integration
- [ ] Advanced charting capabilities
- [ ] Risk analysis tools
- [ ] Portfolio optimization suggestions
- [ ] Export functionality for reports
- [ ] Multiple account support
- [ ] API integration for live market data
