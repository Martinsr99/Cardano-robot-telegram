"""
Load API key from sensitive-data.txt and set it as an environment variable.
"""

import os
import re

def load_api_key():
    """
    Load API key from sensitive-data.txt and set it as an environment variable.
    
    Returns:
        str: API key
    """
    try:
        print("Loading API key from sensitive-data.txt...")
        with open('sensitive-data.txt', 'r') as f:
            content = f.read()
            
            # Check if the file contains the new format with multiple keys
            if "TELEGRAM_TOKEN=" in content:
                # Get the first line which should be the OpenAI API key
                api_key = content.split('\n')[0].strip()
            else:
                # Old format - the entire file is the API key
                api_key = content.strip()
            
            # Set the API key as an environment variable
            os.environ["OPENAI_API_KEY"] = api_key
            
            # Print a masked version of the API key for verification
            masked_key = api_key[:10] + "..." if len(api_key) > 10 else "..."
            print(f"✅ API key loaded from sensitive-data.txt")
            print(f"✅ API key loaded: {masked_key}")
            
            return api_key
    except Exception as e:
        print(f"❌ Error loading API key: {e}")
        return None

if __name__ == "__main__":
    load_api_key()
