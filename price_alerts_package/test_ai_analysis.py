"""
Test script for the AI analysis functionality.

This script sends a command to the Telegram bot to test the analyze_ai command.
"""

import sys
import requests
from telegram_utils import TELEGRAM_TOKEN

def send_command(command):
    """
    Send a command to the Telegram bot.
    
    Args:
        command (str): Command to send (without the leading /)
    """
    # Get the first chat ID from the getUpdates API
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url)
        data = response.json()
        
        if not data.get('ok', False) or not data.get('result', []):
            print("❌ No se pudieron obtener actualizaciones del bot.")
            return
        
        # Get the first chat ID
        chat_id = None
        for update in data['result']:
            if 'message' in update and 'chat' in update['message']:
                chat_id = update['message']['chat']['id']
                break
        
        if not chat_id:
            print("❌ No se pudo encontrar un chat ID.")
            return
        
        # Send the command
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": f"/{command}"
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            print(f"📤 Mensaje enviado correctamente.")
            print(f"Command sent successfully")
        else:
            print(f"❌ Error al enviar el mensaje: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check if a command was provided
    if len(sys.argv) < 2:
        print("❌ Uso: python test_ai_analysis.py COMMAND")
        sys.exit(1)
    
    # Get the command from the command line
    command = sys.argv[1]
    
    # Send the command
    send_command(command)
