# IBKR Trading Dashboard

A comprehensive web-based dashboard for Interactive Brokers (IBKR) trading data analysis, with real-time connection to IBKR Gateway API and advanced options trading analytics.

## 🚀 Features

### 📊 **Real-Time Portfolio Overview**
- **Live Account Data**: Real-time account details, balances, and performance metrics
- **Connection Monitoring**: Automatic IBKR Gateway connection status and error handling
- **Performance Tracking**: P&L tracking, win/loss ratios, and performance charts
- **Position Analysis**: Current holdings with detailed metrics and analytics

### 📈 **Advanced Trading Analytics**
- **Position Analytics**: Comprehensive analysis of current positions including P&L, cost basis, and risk metrics
  - **Collateral Usage Analysis**: ⭐ NEW! Real-time tracking of put option collateral as percentage of total account value
  - **Account Value Integration**: Uses IBKR net liquidation value for accurate collateral percentage calculation
  - **Visual Progress Indicators**: Color-coded progress bars showing collateral usage levels
  - **Smart Risk Alerts**: Dynamic recommendations based on collateral usage thresholds
  - **Available Capital Tracking**: Shows remaining capital not tied to collateral
- **Put Analysis**: Specialized analysis for put options with annualized return calculations
- **Performance Metrics**: Multi-period performance analysis (1D, 7D, MTD, YTD)
- **Account Ledger**: Detailed cash balance and net liquidation value tracking

### 🎯 **Options Trading Focus**
- **Put Annualized Returns**: Automatic calculation of annualized returns for put positions
- **Position Recommendations**: Identifies put positions with returns below 12% for potential closure
- **Collateral Analysis**: Tracks total collateral tied up in put positions
- **Risk Metrics**: Largest gains/losses, average position size, and position type breakdown
- **Stock Concentration Analysis**: ⭐ NEW! Portfolio allocation analysis by stock to identify over-investment risk

### 🔬 **Enhanced Risk Analytics** ⭐ NEW!
- **Black-Scholes Greeks**: Delta, Gamma, Theta, and Vega calculations for all put positions
- **Probability of Profit**: Statistical likelihood of profit using option pricing models
- **Stress Testing Scenarios**: P&L projections under various market conditions:
  - Stock price drops (10% and 20%)
  - Volatility increases (50%)
  - Time decay (1 week)
  - Gamma risk from large moves
- **Portfolio Risk Metrics**: Aggregated Greeks across all positions
- **Risk Level Classification**: High/Medium/Low risk categorization
- **Implied Volatility Estimates**: Market volatility expectations
- **Real-Time Risk Monitoring**: Live updates of risk metrics
- **Real Stock Prices**: ⭐ NEW! Live stock prices from IBKR for accurate ITM detection and Greeks calculations

### 🎯 **In-The-Money (ITM) Analysis** ⭐ NEW!
- **Real-Time ITM Detection**: Uses live stock prices from IBKR to identify in-the-money put positions
- **Assignment Risk Assessment**: Calculates potential assignment costs and risk levels
- **Critical Alerts**: Immediate warnings for deep ITM positions near expiration
- **Action Recommendations**: Specific guidance for managing ITM positions
- **Risk Level Classification**: Critical, High, Medium, and Low risk categories
- **Assignment Value Calculation**: Potential cost if put is assigned
- **Distance from Strike**: How far stock price is below put strike
- **Risk Management Strategies**: Detailed guidance for different risk levels

### 💻 **User Interface**
- **Real-Time Updates**: Live data refresh with connection status monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Bootstrap 5**: Modern, clean interface with professional styling
- **Interactive Controls**: Manual reconnect, refresh, and tickle control buttons
- **Error Handling**: Clear error messages and actionable troubleshooting steps

## 🛠️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Interactive Brokers account
- IBKR Gateway access

### 1. Clone the Repository
```bash
git clone <repository-url>
cd trading_dashboard
```

### 2. Configure Environment Variables
Create a `.env` file or set environment variables:
```bash
export IBKR_GATEWAY_URL=localhost
export IBIND_ACCOUNT_ID=your_account_id
export IBIND_PORT=5001
```

### 3. Start the Application
```bash
docker-compose up -d
```

The dashboard will be available at `http://localhost:5000`

## 📁 Project Structure

```
trading_dashboard/
├── app.py                    # Main Flask application
├── ibkr_client.py           # IBKR API client wrapper
├── templates/
│   └── index.html           # Dashboard template
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # Flask app container
├── Dockerfile.ibkr_gateway  # IBKR Gateway container
├── requirements.txt         # Python dependencies
├── test_*.py               # Test scripts for various components
└── README.md               # This file
```

## 🔌 IBKR Gateway Setup

### Authentication
1. **Access IBKR Gateway**: Open `https://localhost:5001` in your browser
2. **Login**: Enter your IBKR credentials (username/password)
3. **Complete 2FA**: If enabled, complete two-factor authentication
4. **Verify Connection**: The dashboard will automatically detect successful authentication

### Connection Monitoring
The dashboard includes robust connection handling:
- **Automatic Monitoring**: Continuous connection status checking
- **Background Tickle**: Keeps IBKR session alive
- **Error Recovery**: Handles disconnections and session expirations
- **Manual Controls**: Reconnect and refresh buttons for user control

## 📊 Data Sources

### IBKR API Integration
The dashboard connects directly to IBKR Gateway API endpoints:
- **Account Details**: Account information and type
- **Positions**: Current open positions with real-time market data
- **Account Performance**: Multi-period performance metrics
- **Account Ledger**: Cash balances and net liquidation values
- **Trades**: Historical trade data (when available)

### Real-Time Updates
- **Live Data**: All data is fetched in real-time from IBKR
- **Automatic Refresh**: Background processes keep data current
- **Connection Status**: Real-time monitoring of IBKR Gateway connectivity

## 🎯 Usage Guide

### Dashboard Navigation
1. **Connection Status**: Monitor IBKR Gateway connection at the top
2. **Account Overview**: View account details and balances
3. **Performance**: Multi-period performance metrics
4. **Positions**: Current holdings with detailed analytics
5. **Put Analysis**: Specialized put options analysis and recommendations

### Connection Management
- **Status Banner**: Shows current connection status
- **Reconnect Button**: Manual reconnection attempt
- **Refresh Button**: Refresh all dashboard data
- **IBKR Login Link**: Direct link to IBKR Gateway for re-authentication

### Put Analysis Features
- **Annualized Returns**: Automatic calculation for all put positions
- **Closure Recommendations**: Identifies positions with <12% annualized returns
- **Collateral Tracking**: Total collateral tied up in put positions
- **Risk Assessment**: Position-specific risk metrics
- **Stock Concentration Analysis**: ⭐ NEW!
  - **Portfolio Allocation**: Percentage breakdown of put positions by stock
  - **Concentration Risk**: Identifies stocks with >20% portfolio allocation
  - **Risk Level Indicators**: High (>25%), Medium (15-25%), Low (<15%) concentration
  - **Over-Investment Alerts**: Warning system for concentrated positions
  - **Diversification Metrics**: Total stocks, max concentration, average concentration
  - **Stock-Specific Analytics**: Average returns, total P&L, and position counts per stock
- **Advanced Risk Analytics**: ⭐ NEW!
  - **Greeks Analysis**: Delta, Gamma, Theta, Vega for each position
  - **Probability of Profit**: Statistical profit likelihood
  - **Stress Testing**: P&L projections under market stress scenarios
  - **Portfolio Risk Summary**: Aggregated risk metrics across all positions
  - **Risk Level Indicators**: High/Medium/Low risk classification
  - **Implied Volatility**: Market volatility expectations

### 📊 **Collateral Usage Analysis** ⭐ NEW!

#### Understanding Collateral Management
The dashboard now provides comprehensive collateral usage analysis to help you manage your put option risk exposure effectively.

#### Key Metrics Displayed
- **Total Collateral**: Sum of all put option collateral requirements
- **Total Account Value**: Your IBKR account's net liquidation value
- **Collateral Percentage**: What percentage of your account is tied up as collateral
- **Available Capital**: Remaining capital not committed to collateral

#### Visual Risk Indicators
- **Progress Bar**: Visual representation of collateral usage
- **Color-Coded Alerts**:
  - 🟢 **Green (< 30%)**: Healthy usage - room for additional positions
  - 🟡 **Yellow (30-50%)**: Moderate usage - monitor closely
  - 🔴 **Red (> 50%)**: High usage - consider reducing positions

#### Smart Recommendations
The system provides dynamic recommendations based on your collateral usage:
- **Low Usage (< 30%)**: "Healthy collateral usage - Room for additional positions"
- **Moderate Usage (30-50%)**: "Moderate collateral usage - Monitor closely"
- **High Usage (> 50%)**: "High collateral usage - Consider reducing position sizes"

#### Risk Management Benefits
- **Prevent Over-Leveraging**: Avoid tying up too much capital in collateral
- **Optimize Position Sizing**: Balance returns with risk exposure
- **Real-Time Monitoring**: Track collateral usage as positions change
- **Account Integration**: Uses actual IBKR account values for accuracy

#### How It Works
1. **Account Value**: Fetches net liquidation value from IBKR account ledger
2. **Collateral Calculation**: Sums up all put option collateral from position analysis
3. **Percentage Calculation**: Divides collateral by account value
4. **Risk Assessment**: Applies thresholds to determine risk level
5. **Visual Display**: Shows metrics with color-coded progress indicators

### 🔬 **Enhanced Risk Analytics Usage** ⭐ NEW!

#### Understanding the Greeks
- **Delta (-0.5 to 0)**: How much your put position value changes with stock price
  - Delta = -0.8: Position gains $0.80 for every $1 stock drop
  - Delta = -0.2: Position gains $0.20 for every $1 stock drop
- **Gamma (0 to 0.05+)**: How quickly delta changes (acceleration risk)
  - High gamma (>0.02): Delta changes rapidly with stock moves
  - Low gamma (<0.01): Delta changes slowly
- **Theta (negative)**: Daily time decay (value lost per day)
  - Theta = -0.1: Position loses $0.10 per day from time decay
- **Vega (0 to 0.2+)**: Sensitivity to volatility changes
  - High vega: Position value changes significantly with volatility

#### Interpreting Risk Levels
- **High Risk**: Delta > 0.7, Gamma > 0.02, or Theta < -0.1
- **Medium Risk**: Delta 0.5-0.7, Gamma 0.01-0.02, or Theta -0.05 to -0.1
- **Low Risk**: Delta < 0.5, Gamma < 0.01, and Theta > -0.05

#### Stress Testing Scenarios
- **Stock Drop 10%**: Shows P&L impact of moderate market decline
- **Stock Drop 20%**: Shows P&L impact of significant market decline
- **Volatility +50%**: Shows impact of market volatility spike
- **Time Decay (1 week)**: Shows value erosion over 7 days
- **Gamma Risk**: Shows impact of large, rapid price moves

#### Portfolio Risk Management
- **Total Delta**: Portfolio sensitivity to overall market direction
- **Total Gamma**: Portfolio acceleration risk from large moves
- **Total Theta**: Daily time decay across all positions
- **Total Vega**: Portfolio volatility exposure
- **High Risk Positions**: Count of positions requiring close attention

#### Stock Concentration Analysis ⭐ NEW!

##### Understanding Concentration Risk
- **Portfolio Allocation**: Shows what percentage of your put collateral is allocated to each stock
- **Concentration Thresholds**:
  - **High Risk (>25%)**: Significant concentration requiring immediate attention
  - **Medium Risk (15-25%)**: Moderate concentration to monitor closely
  - **Low Risk (<15%)**: Well-diversified allocation
- **Over-Investment Alert**: Stocks with >20% allocation are flagged for review

##### Key Metrics
- **Total Stocks**: Number of different stocks in your put portfolio
- **Max Concentration**: Highest percentage allocated to any single stock
- **Average Concentration**: Mean allocation across all stocks
- **High Concentration Count**: Number of stocks with >25% allocation

#### Real Stock Price Integration ⭐ NEW!

##### Accurate ITM Detection
- **Live Market Data**: Real-time stock prices from IBKR market data feeds
- **Precise ITM Calculation**: Accurate detection of in-the-money put positions
- **Assignment Risk Assessment**: Realistic assignment probability based on actual stock prices
- **Greeks Accuracy**: More precise option Greeks calculations using real underlying prices

##### How It Works
1. **Symbol Search**: IBKR API searches for stock symbols to get contract IDs
2. **Market Data Snapshot**: Real-time price data fetched for each stock
3. **Price Extraction**: Current price extracted from IBKR quote data
4. **ITM Analysis**: Stock price compared to put strike for accurate ITM detection
5. **Greeks Calculation**: Real stock price used in Black-Scholes calculations

##### Benefits
- **Eliminates Estimation Errors**: No more rough estimates based on option premiums
- **Real-Time Accuracy**: Live prices reflect current market conditions
- **Better Risk Assessment**: More accurate assignment risk calculations
- **Improved Greeks**: More precise delta, gamma, theta, and vega values
- **Market-Aware Analysis**: ITM status reflects actual market conditions

##### Fallback Handling
- **Graceful Degradation**: If stock price unavailable, Greeks use default values
- **Clear Indicators**: UI shows "N/A" when real prices not available
- **Error Logging**: Detailed logging for troubleshooting price fetch issues
- **Partial Analysis**: ITM analysis only shows positions with real price data

## 🔍 Troubleshooting

### Common Issues

1. **"401 Unauthorized"**
   - Re-authenticate in IBKR Gateway at `https://localhost:5001`
   - Complete 2FA if enabled
   - Click "Reconnect" button in dashboard

2. **"Connection refused"**
   - Ensure IBKR Gateway container is running: `docker ps`
   - Check if port 5001 is accessible: `curl -k https://localhost:5001`
   - Restart containers: `docker-compose restart`

3. **"404 Not Found"**
   - IBKR Gateway may not be fully initialized
   - Wait a few minutes for startup
   - Check IBKR Gateway logs: `docker logs trading_dashboard-ibkr_gateway-1`

4. **"Network connectivity issues"**
   - Verify Docker containers are running with host networking
   - Check firewall settings
   - Ensure no other services are using port 5001

### Manual Reconnection Steps
1. Check connection status banner for specific error messages
2. Click "Reconnect" button to attempt manual reconnection
3. Click "IBKR Login" link to open IBKR Gateway for re-authentication
4. If still failing, restart containers: `docker-compose restart`
5. Refresh the dashboard page

### Debug Commands
```bash
# Check container status
docker ps

# View Flask app logs
docker logs trading_dashboard-flask-1

# View IBKR Gateway logs
docker logs trading_dashboard-ibkr_gateway-1

# Test IBKR Gateway connectivity
curl -k https://localhost:5001

# Check environment variables
docker exec trading_dashboard-flask-1 env | grep IBKR
```

## 🧪 Testing

### Test Scripts
The project includes comprehensive test scripts:
- `test_ibkr_client.py` - Test IBKR API client functionality
- `test_connection_handling.py` - Test connection management
- `test_position_analytics.py` - Test position analysis calculations
- `test_put_analysis.py` - Test put options analysis

### Running Tests
```bash
# Test IBKR client
python test_ibkr_client.py

# Test connection handling
python test_connection_handling.py

# Test position analytics
python test_position_analytics.py
```

## 🔒 Security & Privacy

### Data Handling
- **Local Processing**: All data processing happens locally
- **No Data Storage**: No sensitive data is stored permanently
- **Secure Communication**: HTTPS communication with IBKR Gateway
- **Session Management**: Proper session handling and cleanup

### Authentication
- **IBKR Credentials**: Stored securely in IBKR Gateway
- **Session Tokens**: Managed by IBKR Gateway
- **No Local Storage**: Credentials are not stored in the application

## 🚀 Future Enhancements

- [ ] Real-time market data integration
- [ ] Advanced charting capabilities
- [ ] Risk analysis tools
- [ ] Portfolio optimization suggestions
- [ ] Export functionality for reports
- [ ] Multiple account support
- [ ] Historical trade analysis
- [ ] Custom alerts and notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with IBKR Gateway
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
- The application processes data as provided by IBKR
- No verification of data accuracy is performed
- Users are responsible for validating their data
- The author is not liable for data processing errors

### 🚨 **Risk Warning**
**Trading options and other securities involves substantial risk and is not suitable for all investors. You can lose some or all of your invested capital. Always consult with a qualified financial advisor before making investment decisions.**

---

**Happy Trading! 📈💰**
