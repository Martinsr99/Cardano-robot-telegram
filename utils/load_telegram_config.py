"""
Load Telegram configuration from sensitive-data.txt and set it as variables.
"""

import os
import re

def load_telegram_config():
    """
    Load Telegram configuration from sensitive-data.txt.
    
    Returns:
        tuple: (token, chat_id) - Telegram bot token and chat ID
    """
    try:
        # Get the absolute path to sensitive-data.txt
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        sensitive_file_path = os.path.join(root_dir, 'sensitive-data.txt')
        
        with open(sensitive_file_path, 'r') as f:
            content = f.read()
            
            # Extract Telegram token
            token_match = re.search(r'TELEGRAM_TOKEN=(.+)', content)
            if token_match:
                token = token_match.group(1).strip()
            else:
                token = "YOUR_TELEGRAM_BOT_TOKEN"
                print("⚠️ Telegram token not found in sensitive-data.txt")
            
            # Extract Telegram chat ID
            chat_id_match = re.search(r'TELEGRAM_CHAT_ID=(.+)', content)
            if chat_id_match:
                chat_id = chat_id_match.group(1).strip()
            else:
                chat_id = "YOUR_TELEGRAM_CHAT_ID"
                print("⚠️ Telegram chat ID not found in sensitive-data.txt")
            
            print("✅ Telegram configuration loaded from sensitive-data.txt")
            return token, chat_id
    except Exception as e:
        print(f"❌ Error loading Telegram configuration: {e}")
        return "YOUR_TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_CHAT_ID"

if __name__ == "__main__":
    load_telegram_config()
