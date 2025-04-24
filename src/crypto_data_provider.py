"""
Cryptocurrency data provider using CoinGecko API.
"""

import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class CryptoDataProvider:
    """
    Class for fetching cryptocurrency data from CoinGecko API.
    """
    def __init__(self, symbol: str = "BTC"):
        """
        Initialize the data provider.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
        """
        self.symbol = symbol
        self.base_url = "https://api.coingecko.com/api/v3"
        self.data = None
        self.indicators = None
        self.dates = None
        self.coin_id = self._get_coin_id(symbol)
    
    def _get_coin_id(self, symbol: str) -> str:
        """
        Convert common cryptocurrency symbol to CoinGecko ID.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "BTC", "ETH")
            
        Returns:
            str: CoinGecko ID for the cryptocurrency
        """
        # Common mappings
        mappings = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ALGO': 'algorand',
            'XLM': 'stellar',
            'FIL': 'filecoin',
            'VET': 'vechain',
            'THETA': 'theta-token',
            'ICP': 'internet-computer',
            'TRX': 'tron',
            'XTZ': 'tezos',
            'EOS': 'eos',
            'AAVE': 'aave',
            'EGLD': 'elrond-erd-2',
            'XMR': 'monero',
            'CAKE': 'pancakeswap-token',
            'AXS': 'axie-infinity',
            'HBAR': 'hedera-hashgraph',
            'NEO': 'neo',
            'WAVES': 'waves',
            'COMP': 'compound-governance-token',
            'KSM': 'kusama',
            'DASH': 'dash',
            'HNT': 'helium',
            'HOT': 'holotoken',
            'ZEC': 'zcash',
            'ENJ': 'enjincoin',
            'MANA': 'decentraland',
            'SAND': 'the-sandbox',
            'SUSHI': 'sushi',
            'ONE': 'harmony',
            'BTT': 'bittorrent',
            'CHZ': 'chiliz',
            'BAT': 'basic-attention-token',
            'IOTA': 'iota',
            'CELO': 'celo',
            'ZIL': 'zilliqa',
            'FLOW': 'flow',
            'QTUM': 'qtum',
            'RVN': 'ravencoin',
            'ICX': 'icon',
            'ONT': 'ontology',
            'DGB': 'digibyte',
            'ZRX': '0x',
            'SC': 'siacoin',
            'ANKR': 'ankr',
            'OMG': 'omisego',
            'BNT': 'bancor',
            'CRV': 'curve-dao-token',
            'SNX': 'havven',
            'IOTX': 'iotex',
            'KAVA': 'kava',
            'LRC': 'loopring',
            'STORJ': 'storj',
            'ALPHA': 'alpha-finance',
            'DENT': 'dent',
            'SKL': 'skale',
            'BAKE': 'bakerytoken',
            'SXP': 'swipe',
            'REEF': 'reef-finance',
            'NKN': 'nkn',
            'OGN': 'origin-protocol',
            'AUDIO': 'audius',
            'CTSI': 'cartesi',
            'OCEAN': 'ocean-protocol',
            'CKB': 'nervos-network',
            'STMX': 'storm',
            'ARPA': 'arpa-chain',
            'CELR': 'celer-network',
            'SRM': 'serum',
            'HIVE': 'hive',
            'WAN': 'wanchain',
            'FET': 'fetch-ai',
            'BAND': 'band-protocol',
            'ROSE': 'oasis-network',
            'LUNA': 'terra-luna',
            'SHIB': 'shiba-inu',
            'NEAR': 'near',
            'FTM': 'fantom',
            'GRT': 'the-graph',
            '1INCH': '1inch',
            'RUNE': 'thorchain',
        }
        
        # Convert to uppercase for case-insensitive matching
        symbol = symbol.upper()
        
        # Return the mapping if it exists, otherwise use the lowercase symbol
        return mappings.get(symbol, symbol.lower())
    
    def fetch_data(self) -> bool:
        """
        Fetch cryptocurrency data from CoinGecko API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"📥 Descargando datos de {self.symbol}...")
            
            # Get current price data
            current_data = self._get_current_price_data()
            if not current_data:
                print("❌ No se pudo obtener información de precio actual.")
                return False
            
            # Add a delay to avoid rate limiting
            time.sleep(1.5)
            
            # Get historical price data (last 30 days)
            historical_data = self._get_historical_price_data(days=30)
            if not historical_data:
                print("❌ No se pudo obtener información histórica.")
                return False
            
            # Process data
            self._process_data(current_data, historical_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Error fetching cryptocurrency data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_current_price_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current price data from CoinGecko API.
        
        Returns:
            dict: Current price data
        """
        try:
            url = f"{self.base_url}/coins/{self.coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"❌ Error: API returned status code {response.status_code}")
                return None
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error getting current price data: {e}")
            return None
    
    def _get_historical_price_data(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get historical price data from CoinGecko API.
        
        Args:
            days: Number of days of historical data to fetch
            
        Returns:
            dict: Historical price data
        """
        try:
            url = f"{self.base_url}/coins/{self.coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily"
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"❌ Error: API returned status code {response.status_code}")
                return None
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error getting historical price data: {e}")
            return None
    
    def _process_data(self, current_data: Dict[str, Any], historical_data: Dict[str, Any]) -> None:
        """
        Process the fetched data.
        
        Args:
            current_data: Current price data
            historical_data: Historical price data
        """
        # Extract current price data
        market_data = current_data.get("market_data", {})
        current_price = market_data.get("current_price", {}).get("usd", 0)
        
        # Extract historical price data
        prices = historical_data.get("prices", [])
        volumes = historical_data.get("total_volumes", [])
        
        # Convert to arrays
        timestamps = [price[0] for price in prices]
        close_prices = [price[1] for price in prices]
        volumes_data = [volume[1] for volume in volumes]
        
        # Convert timestamps to datetime
        dates = [datetime.fromtimestamp(ts / 1000) for ts in timestamps]
        
        # Store data
        self.dates = dates
        self.data = {
            'open': close_prices[:-1] + [current_price],  # Use close prices as open prices (approximation)
            'high': close_prices[:-1] + [current_price],  # Use close prices as high prices (approximation)
            'low': close_prices[:-1] + [current_price],   # Use close prices as low prices (approximation)
            'close': close_prices[:-1] + [current_price],
            'volume': volumes_data,
            'dates': dates
        }
        
        # Calculate indicators
        self._calculate_indicators()
    
    def _calculate_indicators(self) -> None:
        """
        Calculate technical indicators.
        """
        if not self.data or not self.data['close']:
            return
        
        close_prices = np.array(self.data['close'])
        
        # Calculate RSI (14-period)
        rsi = self._calculate_rsi(close_prices, 14)
        
        # Calculate SMA (20-period and 50-period)
        sma_short = self._calculate_sma(close_prices, 20)
        sma_long = self._calculate_sma(close_prices, 50)
        
        # Calculate MACD
        macd_line, macd_signal, macd_histogram = self._calculate_macd(close_prices)
        
        # Store indicators
        self.indicators = {
            'rsi': rsi,
            'sma_short': sma_short,
            'sma_long': sma_long,
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram
        }
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Price data
            period: RSI period
            
        Returns:
            np.ndarray: RSI values
        """
        # Calculate price changes
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)
        
        # Calculate RSI for the rest of the data
        for i in range(period, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)
        
        return rsi
    
    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            prices: Price data
            period: SMA period
            
        Returns:
            np.ndarray: SMA values
        """
        sma = np.zeros_like(prices)
        for i in range(len(prices)):
            if i < period:
                sma[i] = np.mean(prices[:i+1])
            else:
                sma[i] = np.mean(prices[i-period+1:i+1])
        
        return sma
    
    def _calculate_macd(self, prices: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """
        Calculate Moving Average Convergence Divergence (MACD).
        
        Args:
            prices: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal EMA period
            
        Returns:
            tuple: (MACD line, MACD signal, MACD histogram)
        """
        # Calculate EMAs
        ema_fast = self._calculate_ema(prices, fast_period)
        ema_slow = self._calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = ema_fast - ema_slow
        
        # Calculate MACD signal
        macd_signal = self._calculate_ema(macd_line, signal_period)
        
        # Calculate MACD histogram
        macd_histogram = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_histogram
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            prices: Price data
            period: EMA period
            
        Returns:
            np.ndarray: EMA values
        """
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA
        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def get_latest_price(self) -> float:
        """
        Get the latest closing price.
        
        Returns:
            float: Latest closing price
        """
        if self.data is None or len(self.data['close']) == 0:
            return None
        
        return self.data['close'][-1]
    
    def get_latest_indicators(self) -> Dict[str, float]:
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
    
    def get_latest_date(self) -> datetime:
        """
        Get the latest data date.
        
        Returns:
            datetime: Latest data date
        """
        if self.dates is None or len(self.dates) == 0:
            return None
        
        return self.dates[-1]
    
    def get_data_summary(self) -> str:
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
