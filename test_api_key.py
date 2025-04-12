"""
Test script to verify that the API key is being loaded correctly from sensitive-data.txt
and that it can be used to make a request to the OpenAI API.
"""

import os
from load_api_key import load_api_key
from openai import OpenAI

def test_api_key():
    """
    Test that the API key is loaded correctly and can be used to make a request to the OpenAI API.
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
    
    # Try to use the API key to make a request to the OpenAI API
    print("Testing API key with a simple request to OpenAI API...")
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=10
        )
        
        # Print the response
        print(f"✅ API request successful. Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ API request failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_api_key()
