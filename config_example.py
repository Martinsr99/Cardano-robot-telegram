"""
Example configuration settings for the trading bot.
Rename this file to config.py and update with your own values.
"""

# Market configuration
SYMBOL = "BTC-USD"  # Cryptocurrency to monitor
PERIOD = "180d"     # Historical data period
INTERVAL = "1d"     # Data interval

# Trading parameters
PROFIT_TARGET = 0.05  # 5% profit target
STOP_LOSS = 0.03      # 3% stop loss
POSITION_FILE = "position.json"
HISTORY_FILE = "history.json"
SIMULATED_INVESTMENT = 100  # Amount in USD for simulated purchases

# Notification settings
SEND_ALERT = True
TELEGRAM_COMMANDS_ENABLED = True
TELEGRAM_POLL_INTERVAL = 10  # Seconds between checking for new messages
TELEGRAM_ALLOWED_USERS = ["YOUR_TELEGRAM_USER_ID"]  # List of user IDs allowed to send commands

# Monitoring settings
CHECK_INTERVAL = 3600  # Check every hour (in seconds)

# Technical indicators configuration
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
SMA_SHORT = 20
SMA_LONG = 50
