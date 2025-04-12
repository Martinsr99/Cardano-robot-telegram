"""
Telegram utilities for sending messages and handling notifications.
"""

import requests
from models import TradeHistory

# Telegram configuration - exported for use in other modules
TELEGRAM_TOKEN = "8041049082:AAGM2SkLoWgcGh2Nm1-nGfDYeL7S3gNdlPQ"
TELEGRAM_CHAT_ID = "365030875"

# Export these constants for use in other modules
__all__ = ['send_telegram_message', 'record_alert', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

def record_alert(alert_type, message, data=None):
    """
    Record an alert in the history
    
    Args:
        alert_type (str): Type of alert (buy, sell, error, etc.)
        message (str): Alert message
        data (dict): Additional data
    """
    history = TradeHistory()
    
    alert_data = {
        'type': alert_type,
        'message': message
    }
    
    # Add additional data if provided
    if data:
        alert_data.update(data)
    
    history.add_alert(alert_data)

def send_telegram_message(text, alert_type=None, data=None, chat_id=None):
    """
    Send a message to Telegram
    
    Args:
        text (str): Message text
        alert_type (str, optional): Type of alert to record
        data (dict, optional): Additional data for the alert
        chat_id (str, optional): Chat ID to send to
    """
    # Record alert in history if alert_type is provided
    if alert_type:
        record_alert(alert_type, text, data)
    
    try:
        # Use Telegram's HTML formatting which is more reliable
        import re
        
        # Convert Markdown-style formatting to HTML
        # Handle bold text (convert *text* to <b>text</b>)
        text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)
        
        # Handle links [text](url) to <a href="url">text</a>
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id if chat_id else TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("📤 Mensaje enviado correctamente.")
        else:
            print(f"❌ Error al enviar mensaje: {response.text}")
    except Exception as e:
        print(f"❌ Error de red al enviar mensaje: {e}")
