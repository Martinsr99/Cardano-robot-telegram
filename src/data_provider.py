"""
Market data provider for the trading bot.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from config.config import SYMBOL, PERIOD, INTERVAL
from src.indicators import get_all_indicators

class MarketData:
    """
    Class for fetching and processing market data.
    """
    def __init__(self, symbol=SYMBOL, period=PERIOD, interval=INTERVAL):
        self.symbol = symbol
        self.period = period
        self.interval = interval
        self.data = None
        self.indicators = None
        self.dates = None
    
    def fetch_data(self):
        """
        Fetch market data from Yahoo Finance.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"📥 Descargando datos de {self.symbol}...")
            df = yf.download(self.symbol, period=self.period, interval=self.interval)
            
            if df.empty:
                print("❌ No se pudo obtener información.")
                return False
            
            # Store dates and prices
            self.dates = df.index
            self.data = {
                'open': df['Open'].values,
                'high': df['High'].values,
                'low': df['Low'].values,
                'close': df['Close'].values.flatten(),  # <- corregido para ser 1D
                'volume': df['Volume'].values,
                'dates': self.dates
            }
            
            # Calculate indicators
            self.indicators = get_all_indicators(self.data['close'])
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_latest_price(self):
        """
        Get the latest closing price.
        
        Returns:
            float: Latest closing price
        """
        if self.data is None or len(self.data['close']) == 0:
            return None
        
        return self.data['close'][-1]
    
    def get_latest_indicators(self):
        """
        Get the latest indicator values.
        
        Returns:
            dict: Latest indicator values
        """
        if self.indicators is None:
            return None
        
        latest = {}
        for key, values in self.indicators.items():
            if len(values) > 0:
                latest[key] = values[-1]
            else:
                latest[key] = None
        
        return latest
    
    def get_latest_date(self):
        """
        Get the latest data date.
        
        Returns:
            datetime: Latest data date
        """
        if self.dates is None or len(self.dates) == 0:
            return None
        
        return self.dates[-1]
    
    def get_data_summary(self):
        """
        Get a summary of the market data.
        
        Returns:
            str: Data summary
        """
        if self.data is None:
            return "No data available"
        
        latest_price = self.get_latest_price()
        latest_date = self.get_latest_date()
        
        return f"{self.symbol} at {latest_date}: ${latest_price:.4f}"
