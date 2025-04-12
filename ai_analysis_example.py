"""
AI-powered market analysis for cryptocurrencies.

This module uses OpenAI's GPT-4 model to generate market analysis
for cryptocurrencies based on current price data.

Rename this file to ai_analysis.py and update with your own API key.
"""

import os
import json
import requests
from openai import OpenAI

# Default API key - should be set in environment variables or config
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

# Analysis prompt templates for different lengths
SHORT_PROMPT = """
You are a crypto analyst. Analyze {asset_name} (${current_price}) market situation briefly.

Keep your response very concise (max 150 words) and focus on:
1. Current trend (bullish/bearish/neutral)
2. Key support/resistance levels
3. Short-term outlook (1-3 days)

Format with clear sections. Use plain text without asterisks for formatting.
"""

NORMAL_PROMPT = """
You are a crypto analyst for Telegram users. Analyze {asset_name} (${current_price}) market situation.

Keep your response concise (max 250 words) with these sections:
1. 📈 Market Summary: Recent price action and trend
2. 🧠 Technical Analysis: Support/resistance levels and key indicators
3. 💡 Trading Outlook: Short-term perspective (1-7 days)

Format with clear sections. Use plain text without asterisks for formatting.
"""

LONG_PROMPT = """
You are a crypto analyst for Telegram users. Provide detailed analysis for {asset_name} (${current_price}).

Include these sections (max 400 words total):
1. 📈 Market Summary: Recent price movements and context
2. 🧠 Technical Analysis: Support/resistance, indicators, and patterns
3. 🔍 Market Sentiment: Current market mood and external factors
4. 💡 Trading Perspective: Short and medium-term outlook
5. ⚠️ Risk Assessment: Key things to watch

Format with clear sections. Use plain text without asterisks for formatting.
"""

# Default to normal length
ANALYSIS_PROMPT = NORMAL_PROMPT

class AIAnalyzer:
    """
    Class for generating AI-powered market analysis using OpenAI's GPT-4 model.
    """
    def __init__(self, api_key=None):
        """
        Initialize the AIAnalyzer with an OpenAI API key.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will use OPENAI_API_KEY from environment.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_market(self, asset_name, current_price):
        """
        Generate market analysis for a cryptocurrency.
        
        Args:
            asset_name (str): Name of the cryptocurrency (e.g., "BTC", "ETH")
            current_price (float): Current price of the cryptocurrency in USD
            
        Returns:
            str: Market analysis text
        """
        if not self.api_key:
            return "❌ Error: OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."
        
        try:
            # Format the prompt with asset name and current price
            prompt = ANALYSIS_PROMPT.format(
                asset_name=asset_name,
                current_price=current_price
            )
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional cryptocurrency market analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extract and return the analysis
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error generating analysis: {str(e)}"
    
    def get_price_data(self, asset_name):
        """
        Get current price data for a cryptocurrency from CoinGecko API.
        
        Args:
            asset_name (str): Name of the cryptocurrency (e.g., "BTC", "ETH")
            
        Returns:
            dict: Price data including current price, 24h change, etc.
        """
        try:
            # Convert asset name to CoinGecko ID format
            asset_id = self._get_coingecko_id(asset_name)
            
            # Call CoinGecko API
            url = f"https://api.coingecko.com/api/v3/coins/{asset_id}"
            response = requests.get(url)
            data = response.json()
            
            # Extract relevant price data
            price_data = {
                'current_price': data['market_data']['current_price']['usd'],
                'price_change_24h': data['market_data']['price_change_percentage_24h'],
                'price_change_7d': data['market_data']['price_change_percentage_7d'],
                'market_cap': data['market_data']['market_cap']['usd'],
                'volume_24h': data['market_data']['total_volume']['usd']
            }
            
            return price_data
            
        except Exception as e:
            print(f"Error fetching price data: {e}")
            return None
    
    def _get_coingecko_id(self, asset_name):
        """
        Convert common cryptocurrency symbol to CoinGecko ID.
        
        Args:
            asset_name (str): Cryptocurrency symbol (e.g., "BTC", "ETH")
            
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
            # ... (other mappings)
        }
        
        # Convert to uppercase for case-insensitive matching
        asset_name = asset_name.upper()
        
        # Return the mapping if it exists, otherwise use the lowercase asset name
        return mappings.get(asset_name, asset_name.lower())

# Singleton instance
_instance = None

def get_ai_analyzer(api_key=None):
    """
    Get the singleton instance of AIAnalyzer.
    
    Args:
        api_key (str, optional): OpenAI API key. If not provided, will use OPENAI_API_KEY from environment.
        
    Returns:
        AIAnalyzer: AI analyzer instance
    """
    global _instance
    if _instance is None:
        _instance = AIAnalyzer(api_key)
    return _instance

def analyze_crypto(asset_name, length="normal", api_key=None):
    """
    Generate market analysis for a cryptocurrency.
    
    Args:
        asset_name (str): Name of the cryptocurrency (e.g., "BTC", "ETH")
        length (str): Length of analysis - "short", "normal", or "long"
        api_key (str, optional): OpenAI API key. If not provided, will use OPENAI_API_KEY from environment.
        
    Returns:
        str: Market analysis text
    """
    global ANALYSIS_PROMPT
    
    # Set prompt based on requested length
    if length.lower() == "short":
        ANALYSIS_PROMPT = SHORT_PROMPT
    elif length.lower() == "long":
        ANALYSIS_PROMPT = LONG_PROMPT
    else:  # Default to normal
        ANALYSIS_PROMPT = NORMAL_PROMPT
    
    analyzer = get_ai_analyzer(api_key)
    
    # Get current price data
    price_data = analyzer.get_price_data(asset_name)
    
    if not price_data:
        return f"❌ Error: Could not fetch price data for {asset_name}. Please check the symbol and try again."
    
    # Generate analysis
    analysis = analyzer.analyze_market(asset_name, price_data['current_price'])
    
    return analysis
