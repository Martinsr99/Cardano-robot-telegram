"""
AI-powered market analysis for cryptocurrencies.

This module uses OpenAI's GPT-4 model to generate market analysis
for cryptocurrencies based on current price data.
"""

import os
import json
import requests
from openai import OpenAI

# Default API key - should be set in environment variables or config
def get_api_key():
    """Get the API key from the environment variable."""
    return os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

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
        self.api_key = api_key or get_api_key()
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
            'CHR': 'chromia',
            'CVC': 'civic',
            'STPT': 'standard-tokenization-protocol',
            'TROY': 'troy',
            'MTL': 'metal',
            'OXT': 'orchid-protocol',
            'PERL': 'perlin',
            'TOMO': 'tomochain',
            'VTHO': 'vethor-token',
            'AKRO': 'akropolis',
            'KNC': 'kyber-network',
            'JST': 'just',
            'TRB': 'tellor',
            'MDX': 'mdex',
            'PAXG': 'pax-gold',
            'WNXM': 'wrapped-nxm',
            'TLM': 'alien-worlds',
            'MASK': 'mask-network',
            'LIT': 'litentry',
            'XVS': 'venus',
            'DODO': 'dodo',
            'BADGER': 'badger-dao',
            'ALICE': 'my-neighbor-alice',
            'DUSK': 'dusk-network',
            'KEEP': 'keep-network',
            'BOND': 'barnbridge',
            'TWT': 'trust-wallet-token',
            'FORTH': 'ampleforth-governance-token',
            'AR': 'arweave',
            'POLS': 'polkastarter',
            'LINA': 'linear',
            'PERP': 'perpetual-protocol',
            'SUPER': 'superfarm',
            'CFX': 'conflux-token',
            'AUTO': 'auto',
            'ATM': 'atletico-madrid',
            'TVK': 'terra-virtua-kolect',
            'HARD': 'kava-lend',
            'GLM': 'golem',
            'FIRO': 'zcoin',
            'NMR': 'numeraire',
            'FRONT': 'frontier-token',
            'WING': 'wing-finance',
            'MIR': 'mirror-protocol',
            'FOR': 'force-protocol',
            'BEL': 'bella-protocol',
            'AUCTION': 'auction',
            'POND': 'marlin',
            'BTCST': 'btc-standard-hashrate-token',
            'RAY': 'raydium',
            'ALPHA': 'alpha-finance',
            'ORN': 'orion-protocol',
            'YFII': 'yfii-finance',
            'FIS': 'stafi',
            'XVG': 'verge',
            'FIRO': 'zcoin',
            'VITE': 'vite',
            'IRIS': 'iris-network',
            'MFT': 'hifi-finance',
            'BURGER': 'burger-swap',
            'SLP': 'smooth-love-potion',
            'CTXC': 'cortex',
            'TKO': 'tokocrypto',
            'IDEX': 'aurora-dao',
            'DREP': 'drep-new',
            'PHA': 'phala-network',
            'AVA': 'travala',
            'GHST': 'aavegotchi',
            'DCR': 'decred',
            'WRX': 'wazirx',
            'UTK': 'utrust',
            'STRAX': 'stratis',
            'PUNDIX': 'pundi-x-2',
            'GTC': 'gitcoin',
            'MBOX': 'mobox',
            'QNT': 'quant-network',
            'AMP': 'amp-token',
            'REQ': 'request-network',
            'TRIBE': 'tribe-2',
            'VGX': 'ethos',
            'QUICK': 'quickswap',
            'MINA': 'mina-protocol',
            'CLV': 'clover-finance',
            'ERN': 'ethernity-chain',
            'FARM': 'harvest-finance',
            'ALPACA': 'alpaca-finance',
            'AGLD': 'adventure-gold',
            'RAD': 'radicle',
            'BETA': 'beta-finance',
            'RARE': 'superrare',
            'LAZIO': 'lazio-fan-token',
            'CHESS': 'tranchess',
            'ADX': 'adex',
            'BICO': 'biconomy',
            'PORTO': 'fc-porto',
            'JASMY': 'jasmycoin',
            'ACA': 'acala',
            'DAR': 'mines-of-dalarnia',
            'BNX': 'binaryx',
            'RGT': 'rari-governance-token',
            'CITY': 'manchester-city-fan-token',
            'ENS': 'ethereum-name-service',
            'SANTOS': 'santos-fc-fan-token',
            'ANY': 'anyswap',
            'HIGH': 'highstreet',
            'CVX': 'convex-finance',
            'PEOPLE': 'constitutiondao',
            'OOKI': 'ooki',
            'SPELL': 'spell-token',
            'JOE': 'joe',
            'ACH': 'alchemy-pay',
            'IMX': 'immutable-x',
            'GLMR': 'moonbeam',
            'LOKA': 'league-of-kingdoms',
            'BTTC': 'bittorrent-2',
            'ACM': 'ac-milan-fan-token',
            'ANC': 'anchor-protocol',
            'BDOT': 'bdot',
            'API3': 'api3',
            'XNO': 'nano',
            'WOO': 'woo-network',
            'ALPINE': 'alpine-f1-team-fan-token',
            'T': 'threshold-network-token',
            'ASTR': 'astar',
            'NBT': 'niobium-coin',
            'MULTI': 'multichain',
            'MOBX': 'mobix',
            'GF': 'girlfriend',
            'BIFI': 'beefy-finance',
            'LEVER': 'lever',
            'STG': 'stargate-finance',
            'GMT': 'stepn',
            'APE': 'apecoin',
            'BSW': 'biswap',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'BUSD': 'binance-usd',
            'DAI': 'dai',
            'UST': 'terrausd',
            'TUSD': 'true-usd',
            'USDP': 'paxos-standard',
            'FRAX': 'frax',
            'LUSD': 'liquity-usd',
            'GUSD': 'gemini-dollar',
            'SUSD': 'nusd',
            'HUSD': 'husd',
            'OUSD': 'origin-dollar',
            'MUSD': 'musd',
            'USDX': 'usdx',
            'CUSD': 'celo-dollar',
            'DUSD': 'defidollar',
            'ZUSD': 'zusd',
            'USDK': 'usdk',
            'USDN': 'neutrino',
            'USDJ': 'just-stablecoin',
            'EURT': 'tether-eurt',
            'EURS': 'stasis-eurs',
            'JEUR': 'jarvis-synthetic-euro',
            'SEUR': 'seur',
            'EOSDT': 'eosdt',
            'XSGD': 'xsgd',
            'CADC': 'cad-coin',
            'BIDR': 'binance-idr',
            'TRYB': 'bilira',
            'CNHT': 'cny-tether',
            'IDRT': 'rupiah-token',
            'KRWP': 'krown',
            'XCHF': 'cryptofranc',
            'QCAD': 'qcad',
            'NZDS': 'nzd-stablecoin',
            'EURS': 'stasis-eurs',
            'XAUD': 'xaud',
            'USDQ': 'usdq',
            'GYEN': 'gyen',
            'JPYC': 'jpycoin',
            'XIDR': 'straitsx-indonesia-rupiah',
            'XSGD': 'xsgd',
            'TCAD': 'true-cad',
            'TGBP': 'true-gbp',
            'THKD': 'true-hkd',
            'TAUD': 'true-aud',
            'BIDR': 'binance-idr',
            'BKRW': 'binance-krw',
            'BUSD': 'binance-usd',
            'BGBP': 'binance-gbp',
            'BVND': 'binance-vnd',
            'BEUR': 'binance-eur',
            'BZAR': 'binance-zar',
            'BKRW': 'binance-krw',
            'BRUB': 'binance-rub',
            'BIRS': 'binance-irs',
            'BIDR': 'binance-idr',
            'BKZT': 'binance-kzt',
            'BNGN': 'binance-ngn',
            'BTRY': 'binance-try',
            'BZAR': 'binance-zar',
            'WBTC': 'wrapped-bitcoin',
            'WETH': 'weth',
            'WBNB': 'wbnb',
            'WAVAX': 'wrapped-avax',
            'WMATIC': 'wmatic',
            'WFTM': 'wrapped-fantom',
            'WSOL': 'wrapped-solana',
            'WONE': 'wrapped-one',
            'WGLMR': 'wrapped-moonbeam',
            'WASTR': 'wrapped-astar',
            'WMOVR': 'wrapped-moonriver',
            'WROSE': 'wrapped-rose',
            'WCELO': 'wrapped-celo',
            'WKAVA': 'wrapped-kava',
            'WFUSE': 'wrapped-fuse',
            'WBRISE': 'wrapped-brise',
            'WBTT': 'wrapped-bittorrent',
            'WCKB': 'wrapped-nervos-dao',
            'WDOGE': 'wrapped-dogecoin',
            'WLTC': 'wrapped-litecoin',
            'WXRP': 'wrapped-xrp',
            'WADA': 'wrapped-cardano',
            'WTRX': 'wrapped-tron',
            'WXLM': 'wrapped-stellar',
            'WDOT': 'wrapped-polkadot',
            'WLINK': 'wrapped-chainlink',
            'WUNI': 'wrapped-uniswap',
            'WAAVE': 'wrapped-aave',
            'WSHIB': 'wrapped-shiba-inu',
            'WNEAR': 'wrapped-near',
            'WFIL': 'wrapped-filecoin',
            'WALGO': 'wrapped-algorand',
            'WVET': 'wrapped-vechain',
            'WICP': 'wrapped-internet-computer',
            'WEOS': 'wrapped-eos',
            'WXTZ': 'wrapped-tezos',
            'WBCH': 'wrapped-bitcoin-cash',
            'WXMR': 'wrapped-monero',
            'WDASH': 'wrapped-dash',
            'WZEC': 'wrapped-zcash',
            'WIOTA': 'wrapped-iota',
            'WNEO': 'wrapped-neo',
            'WDCR': 'wrapped-decred',
            'WZIL': 'wrapped-zilliqa',
            'WBTG': 'wrapped-bitgem',
            'WBSV': 'wrapped-bitcoin-sv',
            'WBTC': 'wrapped-bitcoin',
            'WETH': 'weth',
            'WBNB': 'wbnb',
            'WAVAX': 'wrapped-avax',
            'WMATIC': 'wmatic',
            'WFTM': 'wrapped-fantom',
            'WSOL': 'wrapped-solana',
            'WONE': 'wrapped-one',
            'WGLMR': 'wrapped-moonbeam',
            'WASTR': 'wrapped-astar',
            'WMOVR': 'wrapped-moonriver',
            'WROSE': 'wrapped-rose',
            'WCELO': 'wrapped-celo',
            'WKAVA': 'wrapped-kava',
            'WFUSE': 'wrapped-fuse',
            'WBRISE': 'wrapped-brise',
            'WBTT': 'wrapped-bittorrent',
            'WCKB': 'wrapped-nervos-dao',
            'WDOGE': 'wrapped-dogecoin',
            'WLTC': 'wrapped-litecoin',
            'WXRP': 'wrapped-xrp',
            'WADA': 'wrapped-cardano',
            'WTRX': 'wrapped-tron',
            'WXLM': 'wrapped-stellar',
            'WDOT': 'wrapped-polkadot',
            'WLINK': 'wrapped-chainlink',
            'WUNI': 'wrapped-uniswap',
            'WAAVE': 'wrapped-aave',
            'WSHIB': 'wrapped-shiba-inu',
            'WNEAR': 'wrapped-near',
            'WFIL': 'wrapped-filecoin',
            'WALGO': 'wrapped-algorand',
            'WVET': 'wrapped-vechain',
            'WICP': 'wrapped-internet-computer',
            'WEOS': 'wrapped-eos',
            'WXTZ': 'wrapped-tezos',
            'WBCH': 'wrapped-bitcoin-cash',
            'WXMR': 'wrapped-monero',
            'WDASH': 'wrapped-dash',
            'WZEC': 'wrapped-zcash',
            'WIOTA': 'wrapped-iota',
            'WNEO': 'wrapped-neo',
            'WDCR': 'wrapped-decred',
            'WZIL': 'wrapped-zilliqa',
            'WBTG': 'wrapped-bitgem',
            'WBSV': 'wrapped-bitcoin-sv',
        }
        
        # Convert to lowercase for case-insensitive matching
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
    # Always create a new instance to ensure we get the latest API key from the environment
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
