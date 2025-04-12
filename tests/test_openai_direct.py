"""
Direct test for the OpenAI API integration.

This script directly tests the analyze_crypto function from ai_analysis.py
to verify if it's actually using OpenAI's API.
"""

from ai_analysis import analyze_crypto

def main():
    """Test the analyze_crypto function directly"""
    print("Testing OpenAI API integration...")
    print("Analyzing BTC...")
    
    # Call the analyze_crypto function
    analysis = analyze_crypto("BTC")
    
    # Print the analysis
    print("\nAnalysis result:")
    print("=" * 50)
    print(analysis)
    print("=" * 50)
    
    # Check if the analysis is from OpenAI
    if "Error" in analysis:
        print("\nFailed to get analysis from OpenAI.")
    else:
        print("\nSuccessfully received analysis from OpenAI.")

if __name__ == "__main__":
    main()
