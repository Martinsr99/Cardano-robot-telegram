"""
Test script to verify that chat actions are sent when AI analysis is requested.
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from price_alerts_refactored import cmd_analyze_ai
from notifier import cmd_forecast
from telegram_utils import send_chat_action

def test_chat_action():
    """
    Test that chat actions are sent when AI analysis is requested.
    """
    print("Testing chat actions for AI analysis commands...")
    
    # We need to patch multiple functions to avoid real API calls
    with patch('telegram_utils.send_chat_action') as mock_chat_action, \
         patch('ai_analysis.analyze_crypto') as mock_analyze_crypto, \
         patch('requests.post') as mock_post:
        
        # Make the mocks return appropriate values
        mock_chat_action.return_value = True
        mock_analyze_crypto.return_value = "This is a mock analysis"
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_post_response
        
        # Create a mock bot with necessary attributes
        mock_bot = MagicMock()
        mock_bot.last_price = 85000  # Mock current price
        
        # Test cmd_analyze_ai
        print("\nTesting cmd_analyze_ai...")
        chat_id = 12345  # Mock chat ID
        user_id = "67890"  # Mock user ID
        
        try:
            # Call the function with a chat_id to trigger the chat action
            cmd_analyze_ai("BTC", mock_bot, user_id, chat_id)
            
            # Check if the chat action was sent
            if mock_chat_action.call_count > 0:
                print("✅ Chat action was sent for cmd_analyze_ai")
                # Print the action that was sent
                args, kwargs = mock_chat_action.call_args_list[0]
                print(f"Action: {kwargs.get('action')}")
                print(f"Chat ID: {kwargs.get('chat_id')}")
            else:
                print("❌ No chat action was sent for cmd_analyze_ai")
        except Exception as e:
            print(f"❌ Error testing cmd_analyze_ai: {e}")
        
        # Reset the mocks
        mock_chat_action.reset_mock()
        mock_analyze_crypto.reset_mock()
        mock_post.reset_mock()
        
        # Test cmd_forecast
        print("\nTesting cmd_forecast...")
        
        # For cmd_forecast, we need to patch the integration module
        with patch('forecast_system.integration.send_chat_action') as mock_integration_chat_action:
            mock_integration_chat_action.return_value = True
            
            try:
                # Call the function with a chat_id to trigger the chat action
                cmd_forecast("BTC largo", mock_bot, chat_id)
                
                # Check if the chat action was sent via either method
                if mock_chat_action.call_count > 0 or mock_integration_chat_action.call_count > 0:
                    print("✅ Chat action was sent for cmd_forecast")
                    if mock_chat_action.call_count > 0:
                        args, kwargs = mock_chat_action.call_args_list[0]
                    else:
                        args, kwargs = mock_integration_chat_action.call_args_list[0]
                    print(f"Action: {kwargs.get('action')}")
                    print(f"Chat ID: {kwargs.get('chat_id')}")
                else:
                    print("❌ No chat action was sent for cmd_forecast")
            except Exception as e:
                print(f"❌ Error testing cmd_forecast: {e}")

if __name__ == "__main__":
    test_chat_action()
