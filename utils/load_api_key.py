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
        # Get the absolute path to sensitive-data.txt
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        sensitive_file_path = os.path.join(root_dir, 'sensitive-data.txt')
        
        with open(sensitive_file_path, 'r') as f:
            content = f.read()
            
            # Check if the file contains the new format with multiple keys
            if "TELEGRAM_TOKEN=" in content:
                # Extract the OpenAI API key using regex
                api_key_match = re.search(r'sk-[a-zA-Z0-9_-]+', content)
                if api_key_match:
                    api_key = api_key_match.group(0)
                else:
                    raise ValueError("OpenAI API key not found in sensitive-data.txt")
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
