"""
Test script for sending a price alert command to the Telegram bot.
"""

import sys
from telegram_utils import send_telegram_message, TELEGRAM_CHAT_ID

def main():
    # Check if a command was provided
    if len(sys.argv) < 2:
        print("Usage: python test_alert.py <command>")
        print("Example: python test_alert.py 'alert BTC 70000'")
        return
    
    # Get the command from command line arguments
    command = sys.argv[1]
    
    # Format the message as a Telegram command
    message = f"/{command}"
    
    # Send the message
    print(f"Sending command: {message}")
    send_telegram_message(message, chat_id=TELEGRAM_CHAT_ID)
    print("Command sent successfully")

if __name__ == "__main__":
    main()
