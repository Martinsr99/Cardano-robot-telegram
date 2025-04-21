"""
Configuration settings for the trading bot.
"""
import os

# Market configuration
SYMBOL = "ADA-USD"
PERIOD = "180d"
INTERVAL = "1d"

# Trading parameters
PROFIT_TARGET = 0.05  # 5% de beneficio objetivo
STOP_LOSS = 0.03  # 3% de stop loss
POSITION_FILE = "position.json"
HISTORY_FILE = "history.json"
SIMULATED_INVESTMENT = 100  # Cantidad en USD para simular compras

# Notification settings
SEND_ALERT = True
TELEGRAM_COMMANDS_ENABLED = True
TELEGRAM_POLL_INTERVAL = 10  # Seconds between checking for new messages
# Load Telegram chat ID from sensitive-data.txt
from utils.load_telegram_config import load_telegram_config
_, TELEGRAM_CHAT_ID = load_telegram_config()
TELEGRAM_ALLOWED_USERS = [TELEGRAM_CHAT_ID]  # List of user IDs allowed to send commands

# Monitoring settings
CHECK_INTERVAL = 3600  # Verificar cada hora (en segundos)

# Technical indicators configuration
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
SMA_SHORT = 20
SMA_LONG = 50

# Financial assistant configuration
# Minimum time between financial analyses in hours (default: 4 hours)
FINANCIAL_ANALYSIS_MIN_INTERVAL = int(os.environ.get("FINANCIAL_ANALYSIS_MIN_INTERVAL", "4"))
