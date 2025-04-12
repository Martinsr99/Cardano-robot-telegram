# Price Alerts System for Telegram Bot

This package contains the essential files for implementing a price alerts system in a Telegram bot. The system allows users to create price alerts for cryptocurrencies and receive notifications when the price reaches the specified value.

## Files Included

### Core Files

- **price_alerts_refactored.py**: The main implementation of the price alerts functionality. It includes:
  - `AlertCondition` class for representing price conditions (>, <, =)
  - `PriceAlert` class for managing alerts with single or complex conditions
  - `AlertHistory` class for tracking triggered alerts
  - `VirtualPortfolio` class for managing a virtual trading portfolio
  - `PriceAlertManager` class for managing price alerts, including storage, retrieval, and checking
  - `PriceProvider` class for fetching cryptocurrency prices from exchanges
  - Command parsing functions and handlers for Telegram bot integration

- **ai_analysis.py**: Provides AI-powered market analysis for cryptocurrencies using OpenAI's GPT-4 model.

- **telegram_utils.py**: Utility functions for sending messages via Telegram.

### Test Files

- **test_price_alerts.py**: Tests for the price alerts functionality.
- **test_alert.py**: Tests for the Telegram bot integration.
- **test_ai_analysis.py**: Tests for the AI analysis functionality.
- **test_openai_direct.py**: Direct test for the OpenAI API integration.

## Features

1. **Price Alerts**:
   - Simple alerts: `/alert BTC 70000`
   - Alerts with operators: `/alert ETH > 3000` or `/alert ADA < 0.5`
   - Complex alerts with AND/OR logic: `/alert BTC > 70000 and ETH < 3000`

2. **Price Checking**:
   - Automatic background monitoring
   - Integration with Binance API for real-time prices
   - Persistent storage of alerts in JSON files

3. **Telegram Notifications**:
   - Formatted messages when an alert is triggered
   - Links to TradingView charts
   - Alert history tracking

4. **Additional Commands**:
   - `/my_alerts` - View active alerts
   - `/cancel BTC` - Cancel alerts for a symbol
   - `/cancel all` - Cancel all alerts
   - `/price BTC` - View current price
   - `/alert_history` - View triggered alerts history

5. **Virtual Portfolio**:
   - `/buy BTC 1000` - Buy cryptocurrencies
   - `/sell BTC 0.05` - Sell cryptocurrencies
   - `/portfolio` - View virtual portfolio

6. **AI Analysis**:
   - `/analyze_ai BTC` - Get AI-powered market analysis

## How to Use

1. Install the required dependencies:
   ```
   pip install ccxt openai
   ```

2. Set up your Telegram bot token and OpenAI API key:
   ```python
   # In telegram_utils.py
   TELEGRAM_TOKEN = "your-telegram-bot-token"
   
   # In ai_analysis.py
   OPENAI_API_KEY = "your-openai-api-key"
   ```

3. Initialize the price alerts system in your main bot file:
   ```python
   from price_alerts_refactored import initialize_alerts, cmd_alert, cmd_my_alerts, cmd_cancel, cmd_price, cmd_alert_history, cmd_buy, cmd_sell, cmd_portfolio, cmd_to_the_moon, cmd_analyze_ai
   
   # Initialize price alerts system
   initialize_alerts()
   
   # Register command handlers
   # (This depends on your bot implementation)
   ```

4. Run the tests to verify the functionality:
   ```
   python test_price_alerts.py
   python test_alert.py "alert BTC 70000"
   python test_ai_analysis.py "analyze_ai BTC"
   python test_openai_direct.py
   ```

## Notes

- The system stores alerts in `price_alerts.json`, alert history in `alert_history.json`, and virtual portfolio data in `virtual_portfolio.json`.
- The price provider uses the Binance API to fetch real-time cryptocurrency prices.
- The AI analysis feature requires an OpenAI API key with access to the GPT-4 model.
