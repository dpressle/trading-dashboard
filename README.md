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
- **Put Analysis**: Specialized analysis for put options with annualized return calculations
- **Performance Metrics**: Multi-period performance analysis (1D, 7D, MTD, YTD)
- **Account Ledger**: Detailed cash balance and net liquidation value tracking

### 🎯 **Options Trading Focus**
- **Put Annualized Returns**: Automatic calculation of annualized returns for put positions
- **Position Recommendations**: Identifies put positions with returns below 12% for potential closure
- **Collateral Analysis**: Tracks total collateral tied up in put positions
- **Risk Metrics**: Largest gains/losses, average position size, and position type breakdown

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

## 🔧 Technical Details

### Backend (Flask + IBKR API)
- **IBKR Client**: Custom wrapper for IBKR Gateway API
- **Connection Management**: Robust error handling and reconnection logic
- **Data Processing**: Real-time position and performance analytics
- **Background Workers**: Tickle worker for session maintenance

### Frontend (Bootstrap 5)
- **Responsive Design**: Mobile-first approach
- **Real-Time Updates**: Live data refresh and status monitoring
- **Interactive Controls**: Manual connection management
- **Error Handling**: User-friendly error messages and troubleshooting

### Docker Architecture
- **Flask Container**: Web application with network_mode: host
- **IBKR Gateway Container**: IBKR Gateway service with network_mode: host
- **Shared Network**: Both containers access localhost for direct communication

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
