"""
Test script for the AI analysis module with different length parameters.
"""

import sys
import os
from ai_analysis import analyze_crypto

def test_analyze_crypto_lengths():
    """
    Test the analyze_crypto function with different length parameters.
    """
    symbol = "BTC"  # Use Bitcoin as the test symbol
    
    print(f"Testing AI analysis for {symbol} with different lengths...\n")
    
    # Test short length
    print("=== SHORT LENGTH ===")
    try:
        short_analysis = analyze_crypto(symbol, "short")
        print(f"Length: {len(short_analysis)} characters")
        print(f"Word count: {len(short_analysis.split())}")
        print(short_analysis[:200] + "...\n")
    except Exception as e:
        print(f"Error with short analysis: {e}\n")
    
    # Test normal length (default)
    print("=== NORMAL LENGTH ===")
    try:
        normal_analysis = analyze_crypto(symbol, "normal")
        print(f"Length: {len(normal_analysis)} characters")
        print(f"Word count: {len(normal_analysis.split())}")
        print(normal_analysis[:200] + "...\n")
    except Exception as e:
        print(f"Error with normal analysis: {e}\n")
    
    # Test long length
    print("=== LONG LENGTH ===")
    try:
        long_analysis = analyze_crypto(symbol, "long")
        print(f"Length: {len(long_analysis)} characters")
        print(f"Word count: {len(long_analysis.split())}")
        print(long_analysis[:200] + "...\n")
    except Exception as e:
        print(f"Error with long analysis: {e}\n")

if __name__ == "__main__":
    test_analyze_crypto_lengths()
