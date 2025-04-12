"""
Technical indicators for market analysis.
"""

import numpy as np
import pandas as pd
from config import RSI_PERIOD, SMA_SHORT, SMA_LONG

def calculate_rsi(prices, period=RSI_PERIOD):
    """
    Calculate Relative Strength Index (RSI) using pandas for reliability.
    
    Args:
        prices (np.array): Array of price values
        period (int): RSI period
        
    Returns:
        np.array: RSI values
    """
    # Convert to pandas Series for more reliable calculation
    price_series = pd.Series(prices)
    
    # Calculate daily returns
    delta = price_series.diff()
    
    # Separate gains and losses
    gain = delta.copy()
    loss = delta.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    loss = -loss  # Make losses positive
    
    # Calculate average gains and losses
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Fill NaN values
    rsi = rsi.fillna(50)  # Neutral value for initial period
    
    return rsi.values

def calculate_sma(prices, period):
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        prices (np.array): Array of price values
        period (int): SMA period
        
    Returns:
        np.array: SMA values
    """
    # Use pandas rolling function for simplicity and correctness
    sma = pd.Series(prices).rolling(window=period).mean().values
    
    return sma

def calculate_ema(prices, period):
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        prices (np.array): Array of price values
        period (int): EMA period
        
    Returns:
        np.array: EMA values
    """
    # Use pandas ewm function for simplicity and correctness
    ema = pd.Series(prices).ewm(span=period, adjust=False).mean().values
    
    return ema

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    Args:
        prices (np.array): Array of price values
        fast_period (int): Fast EMA period
        slow_period (int): Slow EMA period
        signal_period (int): Signal EMA period
        
    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    # Calculate EMAs
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    # Calculate MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate signal line
    signal_line = pd.Series(macd_line).ewm(span=signal_period, adjust=False).mean().values
    
    # Calculate histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices, period=20, num_std=2):
    """
    Calculate Bollinger Bands.
    
    Args:
        prices (np.array): Array of price values
        period (int): SMA period
        num_std (float): Number of standard deviations
        
    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    # Calculate middle band (SMA)
    middle_band = calculate_sma(prices, period)
    
    # Calculate standard deviation
    rolling_std = pd.Series(prices).rolling(window=period).std().values
    
    # Calculate upper and lower bands
    upper_band = middle_band + (rolling_std * num_std)
    lower_band = middle_band - (rolling_std * num_std)
    
    return upper_band, middle_band, lower_band

def get_all_indicators(prices):
    """
    Calculate all technical indicators.
    
    Args:
        prices (np.array): Array of price values
        
    Returns:
        dict: Dictionary with all indicators
    """
    # Calculate indicators
    rsi = calculate_rsi(prices)
    sma_short = calculate_sma(prices, SMA_SHORT)
    sma_long = calculate_sma(prices, SMA_LONG)
    macd_line, macd_signal, macd_histogram = calculate_macd(prices)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)
    
    # Return all indicators
    return {
        'rsi': rsi,
        'sma_short': sma_short,
        'sma_long': sma_long,
        'macd_line': macd_line,
        'macd_signal': macd_signal,
        'macd_histogram': macd_histogram,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower
    }
