# Advanced Trading Bot

An advanced cryptocurrency trading bot with AI-powered market analysis, price alerts, and Telegram integration.

## Features

- **Price Alerts**: Set up custom price alerts for any cryptocurrency
- **AI-Powered Analysis**: Get detailed market analysis using OpenAI's GPT models
- **Telegram Integration**: Receive alerts and interact with the bot via Telegram
- **Virtual Portfolio**: Track your virtual trades and performance
- **Technical Indicators**: Uses various technical indicators for trading signals
- **Forecast System**: Predicts potential price movements and generates alerts

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/advanced-trading-bot.git
   cd advanced-trading-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Before running the bot, you need to configure the API keys and other settings:

1. **Telegram Bot Setup**:
   - Create a new bot using [BotFather](https://t.me/botfather) on Telegram
   - Get your Telegram user ID using [userinfobot](https://t.me/userinfobot)
   - Update the `telegram_utils.py` file with your Telegram bot token and chat ID:
     ```python
     TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
     TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
     ```
   - Update the `config.py` file with your Telegram user ID:
     ```python
     TELEGRAM_ALLOWED_USERS = ["YOUR_TELEGRAM_USER_ID"]
     ```

2. **OpenAI API Setup** (for AI analysis):
   - Get an API key from [OpenAI](https://platform.openai.com/account/api-keys)
   - Set the API key in `ai_analysis.py` or as an environment variable:
     ```python
     # In ai_analysis.py
     OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
     ```
     or
     ```bash
     # As an environment variable
     export OPENAI_API_KEY="your-api-key"
     ```

3. **Configure Trading Parameters**:
   - Edit `config.py` to set your preferred trading parameters:
     ```python
     # Market configuration
     SYMBOL = "ADA-USD"  # Change to your preferred cryptocurrency
     PERIOD = "180d"     # Historical data period
     INTERVAL = "1d"     # Data interval
     
     # Trading parameters
     PROFIT_TARGET = 0.05  # 5% profit target
     STOP_LOSS = 0.03      # 3% stop loss
     ```

## Usage

### Running the Bot

Start the bot with the monitoring option:

```bash
python main.py --monitor
```

This will:
- Initialize the price alert system
- Start monitoring the market
- Begin polling for Telegram commands

### Telegram Commands

Once the bot is running, you can interact with it via Telegram:

- `/alert BTC 70000` - Create an alert when BTC reaches $70000
- `/alert ETH > 3000` - Alert when ETH exceeds $3000
- `/alert ADA < 0.5` - Alert when ADA falls below $0.5
- `/my_alerts` - List your active alerts
- `/cancel SYMBOL` - Cancel alerts for a specific symbol
- `/cancel all` - Cancel all your alerts
- `/price SYMBOL` - Get current price for a cryptocurrency
- `/analyze_ai SYMBOL [short|normal|long]` - Get AI-powered market analysis
- `/forecast SYMBOL [short|normal|long]` - Get price forecast
- `/portfolio` - View your virtual portfolio
- `/buy SYMBOL AMOUNT` - Buy in virtual portfolio
- `/sell SYMBOL AMOUNT` - Sell in virtual portfolio

### Complex Alerts

You can create complex alerts with AND/OR logic:

```
/alert BTC > 70000 and ETH < 3000
/alert SOL > 100 or ADA < 0.5
```

## Project Structure

- `main.py` - Main entry point
- `telegram_utils.py` - Telegram integration utilities
- `ai_analysis.py` - AI-powered market analysis
- `price_alerts.py` - Price alert system
- `data_provider.py` - Market data provider
- `signals.py` - Trading signal generator
- `models.py` - Data models
- `config.py` - Configuration settings
- `forecast_system/` - Price forecasting system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
