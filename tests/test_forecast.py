"""
Test script to verify that the forecast functionality is working correctly.
"""

import os
from load_api_key import load_api_key
from ai_analysis import analyze_crypto

def test_forecast():
    """
    Test that the forecast functionality is working correctly.
    """
    # Load API key from sensitive-data.txt
    print("Loading API key from sensitive-data.txt...")
    load_api_key()
    
    # Check if the API key is set in the environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ API key not found in environment variables.")
        return False
    
    # Print the first few characters of the API key (for security)
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    # Try to use the API key to generate a forecast
    print("Testing forecast functionality with a simple request...")
    try:
        # Generate a forecast for BTC
        symbol = "BTC"
        length = "short"  # Use short length for faster response
        
        print(f"Generating forecast for {symbol} (length: {length})...")
        forecast = analyze_crypto(symbol, length)
        
        # Print the first 100 characters of the forecast
        print(f"✅ Forecast generated successfully. First 100 characters: {forecast[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Forecast generation failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_forecast()
