"""
Advanced Price Alert System for the trading bot.

This module handles the creation, storage, and checking of price alerts.
When an alert condition is met, it sends a notification to the user.
"""

import json
import os
import time
import threading
import datetime
import random
import ccxt
from utils.telegram_utils import send_telegram_message
from src.ai_analysis import analyze_crypto
from utils.load_api_key import load_api_key

# Files to store data
ALERTS_FILE = "price_alerts.json"
HISTORY_FILE = "alert_history.json"
PORTFOLIO_FILE = "virtual_portfolio.json"

# Alert condition types
EQUAL = "="
GREATER = ">"
LESS = "<"
AND = "and"
OR = "or"

class AlertCondition:
    """
    Represents a single price alert condition.
    """
    def __init__(self, symbol, operator, target_price):
        self.symbol = symbol.upper()  # Normalize symbol to uppercase
        self.operator = operator  # >, <, or =
        self.target_price = float(target_price)
    
    def check(self, current_price):
        """
        Check if the condition is met
        
        Args:
            current_price (float): Current price to check against
            
        Returns:
            bool: True if condition is met, False otherwise
        """
        if self.operator == EQUAL:
            # For equality, we use a small tolerance (0.1%)
            tolerance = self.target_price * 0.001
            return abs(current_price - self.target_price) <= tolerance
        elif self.operator == GREATER:
            return current_price > self.target_price
        elif self.operator == LESS:
            return current_price < self.target_price
        return False
    
    def to_dict(self):
        """Convert condition to dictionary for storage"""
        return {
            'symbol': self.symbol,
            'operator': self.operator,
            'target_price': self.target_price
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create condition from dictionary"""
        return cls(
            symbol=data['symbol'],
            operator=data['operator'],
            target_price=data['target_price']
        )
    
    def __str__(self):
        op_str = "=" if self.operator == EQUAL else self.operator
        return f"{self.symbol} {op_str} ${self.target_price:.2f}"


class PriceAlert:
    """
    Represents a price alert with conditions and user information.
    Supports simple alerts and complex conditions with AND/OR logic.
    """
    def __init__(self, conditions, user_id, logic=None, alert_id=None, created_at=None):
        self.conditions = conditions  # List of AlertCondition objects
        self.logic = logic  # AND or OR for multiple conditions, None for single condition
        self.user_id = str(user_id)
        self.alert_id = alert_id or self._generate_id()
        self.created_at = created_at or datetime.datetime.now().isoformat()
        self.triggered = False
        self.triggered_at = None
        self.triggered_prices = {}  # Symbol -> price mapping when triggered
    
    def _generate_id(self):
        """Generate a unique ID for the alert"""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self):
        """Convert alert to dictionary for storage"""
        return {
            'id': self.alert_id,
            'conditions': [c.to_dict() for c in self.conditions],
            'logic': self.logic,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'triggered': self.triggered,
            'triggered_at': self.triggered_at,
            'triggered_prices': self.triggered_prices
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create alert from dictionary"""
        conditions = [AlertCondition.from_dict(c) for c in data['conditions']]
        alert = cls(
            conditions=conditions,
            logic=data.get('logic'),
            user_id=data['user_id'],
            alert_id=data['id'],
            created_at=data['created_at']
        )
        alert.triggered = data.get('triggered', False)
        alert.triggered_at = data.get('triggered_at')
        alert.triggered_prices = data.get('triggered_prices', {})
        return alert
    
    def check(self, prices):
        """
        Check if the alert conditions are met
        
        Args:
            prices (dict): Dictionary mapping symbols to current prices
            
        Returns:
            bool: True if conditions are met, False otherwise
        """
        if len(self.conditions) == 1:
            condition = self.conditions[0]
            if condition.symbol not in prices:
                return False
            return condition.check(prices[condition.symbol])
        
        # Multiple conditions with AND/OR logic
        results = []
        for condition in self.conditions:
            if condition.symbol not in prices:
                results.append(False)
                continue
            results.append(condition.check(prices[condition.symbol]))
        
        if self.logic == AND:
            return all(results)
        elif self.logic == OR:
            return any(results)
        
        # Default to AND if logic not specified
        return all(results)
    
    def get_symbols(self):
        """Get all symbols in this alert"""
        return [c.symbol for c in self.conditions]
    
    def __str__(self):
        if len(self.conditions) == 1:
            return f"Alert for {self.conditions[0]}"
        
        condition_strs = [str(c) for c in self.conditions]
        logic = self.logic or AND
        return f"Alert for {(' ' + logic + ' ').join(condition_strs)}"


class AlertHistory:
    """
    Manages the history of triggered alerts.
    """
    def __init__(self):
        self.history = []
        self.load()
    
    def add(self, alert, prices):
        """
        Add a triggered alert to history
        
        Args:
            alert (PriceAlert): The triggered alert
            prices (dict): Current prices when triggered
        """
        entry = {
            'id': alert.alert_id,
            'user_id': alert.user_id,
            'conditions': [str(c) for c in alert.conditions],
            'triggered_at': datetime.datetime.now().isoformat(),
            'prices': prices
        }
        self.history.append(entry)
        self.save()
    
    def get_for_user(self, user_id, limit=10):
        """
        Get recent alert history for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of entries to return
            
        Returns:
            list: Recent alert history entries
        """
        user_history = [h for h in self.history if h['user_id'] == str(user_id)]
        return sorted(user_history, key=lambda x: x['triggered_at'], reverse=True)[:limit]
    
    def save(self):
        """Save history to file"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump({
                'history': self.history
            }, f, indent=2)
    
    def load(self):
        """Load history from file"""
        if not os.path.exists(HISTORY_FILE):
            self.history = []
            return
        
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.history = data.get('history', [])
        except Exception as e:
            print(f"Error loading alert history: {e}")
            self.history = []


class VirtualPortfolio:
    """
    Manages a virtual trading portfolio for users.
    """
    def __init__(self):
        self.portfolios = {}  # user_id -> portfolio
        self.load()
    
    def get_portfolio(self, user_id):
        """
        Get a user's portfolio, creating it if it doesn't exist
        
        Args:
            user_id (str): User ID
            
        Returns:
            dict: User's portfolio
        """
        user_id = str(user_id)
        if user_id not in self.portfolios:
            # Initialize with default USD balance
            self.portfolios[user_id] = {
                'balance_usd': 10000.0,  # Start with $10,000
                'assets': {},            # Symbol -> amount
                'transactions': []       # Transaction history
            }
            self.save()
        
        return self.portfolios[user_id]
    
    def buy(self, user_id, symbol, amount_usd, price):
        """
        Buy an asset in the virtual portfolio
        
        Args:
            user_id (str): User ID
            symbol (str): Asset symbol
            amount_usd (float): USD amount to spend
            price (float): Current price
            
        Returns:
            dict: Result with success flag and message
        """
        user_id = str(user_id)
        portfolio = self.get_portfolio(user_id)
        
        # Check if user has enough balance
        if portfolio['balance_usd'] < amount_usd:
            return {
                'success': False,
                'message': f"Insufficient balance. You have ${portfolio['balance_usd']:.2f}, need ${amount_usd:.2f}"
            }
        
        # Calculate amount of asset to buy
        asset_amount = amount_usd / price
        
        # Update portfolio
        portfolio['balance_usd'] -= amount_usd
        
        symbol = symbol.upper()
        if symbol not in portfolio['assets']:
            portfolio['assets'][symbol] = 0
        
        portfolio['assets'][symbol] += asset_amount
        
        # Record transaction
        transaction = {
            'type': 'buy',
            'symbol': symbol,
            'amount_usd': amount_usd,
            'asset_amount': asset_amount,
            'price': price,
            'timestamp': datetime.datetime.now().isoformat()
        }
        portfolio['transactions'].append(transaction)
        
        self.save()
        
        return {
            'success': True,
            'message': f"Bought {asset_amount:.6f} {symbol} at ${price:.2f} for ${amount_usd:.2f}"
        }
    
    def sell(self, user_id, symbol, asset_amount, price):
        """
        Sell an asset from the virtual portfolio
        
        Args:
            user_id (str): User ID
            symbol (str): Asset symbol
            asset_amount (float): Amount of asset to sell
            price (float): Current price
            
        Returns:
            dict: Result with success flag and message
        """
        user_id = str(user_id)
        portfolio = self.get_portfolio(user_id)
        symbol = symbol.upper()
        
        # Check if user has the asset
        if symbol not in portfolio['assets'] or portfolio['assets'][symbol] < asset_amount:
            available = portfolio['assets'].get(symbol, 0)
            return {
                'success': False,
                'message': f"Insufficient {symbol}. You have {available:.6f}, want to sell {asset_amount:.6f}"
            }
        
        # Calculate USD amount
        amount_usd = asset_amount * price
        
        # Update portfolio
        portfolio['balance_usd'] += amount_usd
        portfolio['assets'][symbol] -= asset_amount
        
        # Remove asset if balance is zero
        if portfolio['assets'][symbol] <= 0:
            del portfolio['assets'][symbol]
        
        # Record transaction
        transaction = {
            'type': 'sell',
            'symbol': symbol,
            'amount_usd': amount_usd,
            'asset_amount': asset_amount,
            'price': price,
            'timestamp': datetime.datetime.now().isoformat()
        }
        portfolio['transactions'].append(transaction)
        
        self.save()
        
        return {
            'success': True,
            'message': f"Sold {asset_amount:.6f} {symbol} at ${price:.2f} for ${amount_usd:.2f}"
        }
    
    def get_portfolio_value(self, user_id, prices):
        """
        Calculate total portfolio value
        
        Args:
            user_id (str): User ID
            prices (dict): Current prices for assets
            
        Returns:
            dict: Portfolio value summary
        """
        user_id = str(user_id)
        portfolio = self.get_portfolio(user_id)
        
        # Calculate asset values
        asset_values = {}
        total_asset_value = 0
        
        for symbol, amount in portfolio['assets'].items():
            if symbol in prices:
                value = amount * prices[symbol]
                asset_values[symbol] = {
                    'amount': amount,
                    'price': prices[symbol],
                    'value': value
                }
                total_asset_value += value
        
        total_value = portfolio['balance_usd'] + total_asset_value
        
        return {
            'balance_usd': portfolio['balance_usd'],
            'assets': asset_values,
            'total_asset_value': total_asset_value,
            'total_value': total_value
        }
    
    def save(self):
        """Save portfolios to file"""
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump({
                'portfolios': self.portfolios
            }, f, indent=2)
    
    def load(self):
        """Load portfolios from file"""
        if not os.path.exists(PORTFOLIO_FILE):
            self.portfolios = {}
            return
        
        try:
            with open(PORTFOLIO_FILE, 'r') as f:
                data = json.load(f)
                self.portfolios = data.get('portfolios', {})
        except Exception as e:
            print(f"Error loading portfolios: {e}")
            self.portfolios = {}


class PriceAlertManager:
    """
    Manages price alerts, including storage, retrieval, and checking.
    """
    def __init__(self):
        self.alerts = []
        self.alert_history = AlertHistory()
        self.virtual_portfolio = VirtualPortfolio()
        self.price_provider = PriceProvider()
        self.load_alerts()
        self._stop_event = threading.Event()
        self._thread = None
        
        # Fun GIFs for easter eggs
        self.moon_gifs = [
            "https://media.giphy.com/media/Ogak8XuKHLs6PYcqlp/giphy.gif",
            "https://media.giphy.com/media/trN9ht5RlE3Dcwavg2/giphy.gif",
            "https://media.giphy.com/media/DnMMGxEvniha7CvASq/giphy.gif"
        ]
    
    def add_alert(self, alert):
        """
        Add a new price alert
        
        Args:
            alert (PriceAlert): Alert to add
            
        Returns:
            str: Alert ID
        """
        self.alerts.append(alert)
        self.save_alerts()
        return alert.alert_id
    
    def remove_alert(self, alert_id):
        """
        Remove an alert by ID
        
        Args:
            alert_id (str): Alert ID to remove
            
        Returns:
            bool: True if alert was removed, False otherwise
        """
        initial_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if a.alert_id != alert_id]
        
        if len(self.alerts) < initial_count:
            self.save_alerts()
            return True
        return False
    
    def remove_alerts_for_symbol(self, user_id, symbol):
        """
        Remove all alerts for a specific symbol and user
        
        Args:
            user_id (str): User ID
            symbol (str): Symbol to remove alerts for
            
        Returns:
            int: Number of alerts removed
        """
        user_id = str(user_id)
        symbol = symbol.upper()
        
        initial_count = len(self.alerts)
        
        # Keep alerts that don't match the criteria
        self.alerts = [
            a for a in self.alerts 
            if a.user_id != user_id or 
            (symbol != "ALL" and symbol not in a.get_symbols())
        ]
        
        removed_count = initial_count - len(self.alerts)
        if removed_count > 0:
            self.save_alerts()
        
        return removed_count
    
    def get_alerts_for_user(self, user_id):
        """
        Get all alerts for a specific user
        
        Args:
            user_id (str): User ID
            
        Returns:
            list: List of alerts for the user
        """
        return [a for a in self.alerts if a.user_id == str(user_id) and not a.triggered]
    
    def get_all_active_alerts(self):
        """
        Get all active (non-triggered) alerts
        
        Returns:
            list: List of active alerts
        """
        return [a for a in self.alerts if not a.triggered]
    
    def save_alerts(self):
        """Save alerts to file"""
        with open(ALERTS_FILE, 'w') as f:
            json.dump({
                'alerts': [a.to_dict() for a in self.alerts]
            }, f, indent=2)
    
    def load_alerts(self):
        """Load alerts from file"""
        if not os.path.exists(ALERTS_FILE):
            self.alerts = []
            return
        
        try:
            with open(ALERTS_FILE, 'r') as f:
                data = json.load(f)
                self.alerts = [PriceAlert.from_dict(a) for a in data.get('alerts', [])]
        except Exception as e:
            print(f"Error loading alerts: {e}")
            self.alerts = []
    
    def start_monitoring(self, check_interval=60):
        """
        Start monitoring thread to check alerts
        
        Args:
            check_interval (int): Interval in seconds between checks
        """
        if self._thread and self._thread.is_alive():
            print("Alert monitoring already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_alerts, args=(check_interval,))
        self._thread.daemon = True
        self._thread.start()
        print("🔔 Price alert monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=5)
            print("🔔 Price alert monitoring stopped")
    
    def _monitor_alerts(self, check_interval):
        """
        Monitor alerts in a background thread
        
        Args:
            check_interval (int): Interval in seconds between checks
        """
        while not self._stop_event.is_set():
            try:
                self._check_alerts()
                # Sleep for the specified interval, but check stop_event frequently
                for _ in range(check_interval):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Error in alert monitoring: {e}")
                time.sleep(check_interval)
    
    def _check_alerts(self):
        """Check all active alerts against current prices"""
        active_alerts = self.get_all_active_alerts()
        if not active_alerts:
            return
        
        # Collect all symbols needed
        all_symbols = set()
        for alert in active_alerts:
            all_symbols.update(alert.get_symbols())
        
        # Fetch prices for all symbols
        prices = self.price_provider.get_prices(all_symbols)
        if not prices:
            return
        
        # Check each alert
        for alert in active_alerts:
            if alert.check(prices):
                self._trigger_alert(alert, prices)
    
    def _trigger_alert(self, alert, prices):
        """
        Trigger an alert and send notification
        
        Args:
            alert (PriceAlert): Alert that was triggered
            prices (dict): Current prices for symbols
        """
        # Mark alert as triggered
        alert.triggered = True
        alert.triggered_at = datetime.datetime.now().isoformat()
        alert.triggered_prices = {s: prices.get(s) for s in alert.get_symbols()}
        self.save_alerts()
        
        # Add to history
        self.alert_history.add(alert, alert.triggered_prices)
        
        # Create notification message
        if len(alert.conditions) == 1:
            condition = alert.conditions[0]
            symbol = condition.symbol
            price = prices.get(symbol)
            
            # Get TradingView chart link
            chart_link = self.price_provider._get_tradingview_link(symbol)
            
            msg = (
                f"*🔔 ALERTA DE PRECIO ACTIVADA*\n\n"
                f"*Símbolo:* {symbol}\n"
                f"*Condición:* {condition}\n"
                f"*Precio actual:* ${price:.4f}\n"
                f"*Creada:* {alert.created_at}\n\n"
                f"[Ver gráfico en TradingView]({chart_link})"
            )
        else:
            # Multiple conditions
            conditions_text = []
            for condition in alert.conditions:
                symbol = condition.symbol
                price = prices.get(symbol, "N/A")
                if price != "N/A":
                    price_str = f"${price:.4f}"
                else:
                    price_str = "N/A"
                conditions_text.append(f"{condition} (actual: {price_str})")
            
            # Use first symbol for chart link
            first_symbol = alert.conditions[0].symbol
            chart_link = self.price_provider._get_tradingview_link(first_symbol)
            
            msg = (
                f"*🔔 ALERTA COMPLEJA ACTIVADA*\n\n"
                f"*Condiciones:*\n"
            )
            
            for i, text in enumerate(conditions_text, 1):
                msg += f"{i}. {text}\n"
            
            msg += (
                f"\n*Lógica:* {alert.logic or 'AND'}\n"
                f"*Creada:* {alert.created_at}\n\n"
                f"[Ver gráfico en TradingView]({chart_link})"
            )
        
        # Send notification to the user
        send_telegram_message(msg, chat_id=alert.user_id)
        print(f"Alert triggered for user {alert.user_id}: {alert}")
    
    def get_price(self, symbol):
        """
        Get current price for a symbol
        
        Args:
            symbol (str): Symbol to get price for
            
        Returns:
            dict: Price information
        """
        return self.price_provider.get_price(symbol)
    
    def to_the_moon(self):
        """Get a random 'to the moon' GIF"""
        return random.choice(self.moon_gifs)


class PriceProvider:
    """
    Provides cryptocurrency prices from exchange APIs.
    """
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        # Cache for current prices
        self.current_prices = {}
        self.last_price_update = None
    
    def get_prices(self, symbols):
        """
        Get current prices for multiple symbols
        
        Args:
            symbols (set): Set of symbols to get prices for
            
        Returns:
            dict: Symbol -> price mapping
        """
        # Check if we need to update prices (cache for 30 seconds)
        current_time = time.time()
        if (self.last_price_update is None or 
            current_time - self.last_price_update > 30):
            
            # Fetch prices for all symbols
            prices = {}
            for symbol in symbols:
                try:
                    ticker_symbol = self._format_ticker_symbol(symbol)
                    ticker = self.exchange.fetch_ticker(ticker_symbol)
                    prices[symbol] = ticker['last']
                except Exception as e:
                    print(f"Error fetching price for {symbol}: {e}")
            
            # Update cache
            self.current_prices = prices
            self.last_price_update = current_time
            
            return prices
        
        # Filter cached prices for requested symbols
        return {s: p for s, p in self.current_prices.items() if s in symbols}
    
    def get_price(self, symbol):
        """
        Get current price for a symbol
        
        Args:
            symbol (str): Symbol to get price for
            
        Returns:
            dict: Price information
        """
        symbol = symbol.upper()
        
        try:
            # Get current price
            ticker_symbol = self._format_ticker_symbol(symbol)
            ticker = self.exchange.fetch_ticker(ticker_symbol)
            
            # Get 24h change
            change_24h = ticker.get('percentage', None)
            if change_24h is None and 'open' in ticker and ticker['open'] > 0:
                change_24h = (ticker['last'] - ticker['open']) / ticker['open'] * 100
            
            # Get chart link
            chart_link = self._get_tradingview_link(symbol)
            
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'change_24h': change_24h,
                'volume': ticker.get('quoteVolume', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'chart_link': chart_link
            }
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None
    
    def _format_ticker_symbol(self, symbol):
        """
        Format symbol for exchange API
        
        Args:
            symbol (str): Symbol like BTC, ETH, etc.
            
        Returns:
            str: Formatted symbol like BTC/USDT
        """
        # Remove any existing suffix
        base_symbol = symbol.split('-')[0].split('/')[0]
        
        # Add USDT suffix if not present
        if '/' not in base_symbol:
            return f"{base_symbol}/USDT"
        return base_symbol
    
    def _get_tradingview_link(self, symbol):
        """
        Generate a TradingView chart link for the symbol
        
        Args:
            symbol (str): Symbol like BTC, ETH, etc.
            
        Returns:
            str: TradingView chart link
        """
        # Format symbol for TradingView
        base_symbol = symbol.split('-')[0].split('/')[0]
        
        # Use the direct TradingView symbol page
        return f"https://es.tradingview.com/symbols/{base_symbol}USD/"


# Command parsing functions
def parse_alert_command(args, user_id):
    """
    Parse alert command from user
    
    Args:
        args (str): Command arguments (e.g., "BTC 50000" or "BTC > 50000")
        user_id (str): User ID
        
    Returns:
        tuple: (success, message, alert)
    """
    if not args:
        return False, "❌ Formato incorrecto. Uso: /alert SYMBOL PRICE o /alert SYMBOL > PRICE", None
    
    # Check for complex alert with AND/OR
    if " and " in args.lower() or " or " in args.lower():
        return _parse_complex_alert(args, user_id)
    
    # Parse simple alert
    # Check for operator
    operator = EQUAL  # Default
    if ">" in args:
        parts = args.split(">", 1)
        symbol = parts[0].strip().upper()
        price_str = parts[1].strip()
        operator = GREATER
    elif "<" in args:
        parts = args.split("<", 1)
        symbol = parts[0].strip().upper()
        price_str = parts[1].strip()
        operator = LESS
    else:
        # No explicit operator, use space as separator
        parts = args.strip().split()
        if len(parts) < 2:
            return False, "❌ Formato incorrecto. Uso: /alert SYMBOL PRICE o /alert SYMBOL > PRICE", None
        
        symbol = parts[0].upper()
        price_str = parts[1]
    
    try:
        price = float(price_str)
    except ValueError:
        return False, f"❌ Precio inválido: {price_str}", None
    
    if price <= 0:
        return False, "❌ El precio debe ser mayor que cero", None
    
    # Create condition and alert
    condition = AlertCondition(symbol, operator, price)
    alert = PriceAlert([condition], user_id)
    
    op_str = "=" if operator == EQUAL else operator
    return True, f"✅ Alerta creada para {symbol} {op_str} ${price:.2f}", alert


def _parse_complex_alert(args, user_id):
    """
    Parse a complex alert with AND/OR logic
    
    Args:
        args (str): Command arguments
        user_id (str): User ID
        
    Returns:
        tuple: (success, message, alert)
    """
    # Determine logic type
    logic = AND
    if " and " in args.lower():
        parts = args.lower().split(" and ")
    elif " or " in args.lower():
        parts = args.lower().split(" or ")
        logic = OR
    else:
        return False, "❌ Formato incorrecto para alerta compleja", None
    
    # Parse each condition
    conditions = []
    condition_strs = []
    
    for part in parts:
        # Parse operator
        operator = EQUAL  # Default
        if ">" in part:
            subparts = part.split(">", 1)
            symbol = subparts[0].strip().upper()
            price_str = subparts[1].strip()
            operator = GREATER
        elif "<" in part:
            subparts = part.split("<", 1)
            symbol = subparts[0].strip().upper()
            price_str = subparts[1].strip()
            operator = LESS
        else:
            # No explicit operator, use space as separator
            subparts = part.strip().split()
            if len(subparts) < 2:
                return False, f"❌ Condición inválida: {part}", None
            
            symbol = subparts[0].upper()
            price_str = subparts[1]
        
        try:
            price = float(price_str)
        except ValueError:
            return False, f"❌ Precio inválido: {price_str}", None
        
        if price <= 0:
            return False, "❌ El precio debe ser mayor que cero", None
        
        # Create condition
        condition = AlertCondition(symbol, operator, price)
        conditions.append(condition)
        condition_strs.append(str(condition))
    
    # Create alert
    alert = PriceAlert(conditions, user_id, logic)
    
    return True, f"✅ Alerta compleja creada: {' ' + logic + ' '.join(condition_strs)}", alert


# Singleton instance
_instance = None

def get_alert_manager():
    """
    Get the singleton instance of PriceAlertManager
    
    Returns:
        PriceAlertManager: Alert manager instance
    """
    global _instance
    if _instance is None:
        _instance = PriceAlertManager()
    return _instance


# Command handlers for Telegram bot
def cmd_alert(args, bot, user_id=None):
    """
    Handle alert command
    
    Args:
        args (str): Command arguments
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    if not args:
        # Show active alerts for user
        manager = get_alert_manager()
        alerts = manager.get_alerts_for_user(user_id)
        
        if not alerts:
            return "No tienes alertas de precio activas.\n\n*Para crear una alerta:*\n• /alert BTC 70000 - Alerta cuando BTC llegue a $70000\n• /alert ETH > 3000 - Alerta cuando ETH supere $3000\n• /alert ADA < 0.5 - Alerta cuando ADA caiga por debajo de $0.5"
        
        response = "*Tus alertas de precio activas:*\n\n"
        for i, alert in enumerate(alerts, 1):
            response += f"{i}. {alert}\n"
        
        response += "\n*Comandos disponibles:*\n• /alert SYMBOL PRICE - Crear alerta\n• /cancel SYMBOL - Eliminar alertas para un símbolo\n• /cancel all - Eliminar todas tus alertas"
        return response
    
    # Parse command and create alert
    success, message, alert = parse_alert_command(args, user_id)
    
    if not success:
        return message
    
    # Add alert
    manager = get_alert_manager()
    manager.add_alert(alert)
    
    # Ensure monitoring is running
    manager.start_monitoring()
    
    return message


def cmd_my_alerts(args, bot, user_id=None):
    """
    List user's active alerts
    
    Args:
        args (str): Command arguments (not used)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    manager = get_alert_manager()
    alerts = manager.get_alerts_for_user(user_id)
    
    if not alerts:
        return "No tienes alertas de precio activas."
    
    response = "*Tus alertas de precio activas:*\n\n"
    for i, alert in enumerate(alerts, 1):
        response += f"{i}. {alert}\n"
    
    response += "\nPara crear una alerta: /alert SYMBOL PRICE\nPara eliminar: /cancel SYMBOL o /cancel all"
    return response


def cmd_cancel(args, bot, user_id=None):
    """
    Cancel alerts for a symbol or all alerts
    
    Args:
        args (str): Command arguments (symbol or "all")
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    if not args:
        return "❌ *Error:* Debes especificar un símbolo o 'all'.\n\n*Uso correcto:*\n• /cancel BTC - Eliminar alertas para Bitcoin\n• /cancel all - Eliminar todas tus alertas"
    
    symbol = args.strip().upper()
    manager = get_alert_manager()
    
    # Remove alerts
    removed_count = manager.remove_alerts_for_symbol(user_id, symbol)
    
    if removed_count == 0:
        if symbol == "ALL":
            return "No tenías alertas activas. Puedes crear una con /alert SYMBOL PRICE"
        else:
            return f"No tenías alertas activas para {symbol}. Puedes ver tus alertas activas con /my_alerts"
    
    if symbol == "ALL":
        return f"✅ Se han eliminado todas tus alertas ({removed_count})."
    else:
        return f"✅ Se han eliminado {removed_count} alertas para {symbol}."


def cmd_price(args, bot, user_id=None):
    """
    Get current price for a symbol
    
    Args:
        args (str): Command arguments (symbol)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    if not args:
        return "❌ *Error:* Debes especificar un símbolo de criptomoneda.\n\n*Uso correcto:* /price SYMBOL\n\n*Ejemplos:*\n• /price BTC\n• /price ETH\n• /price ADA"
    
    symbol = args.strip().upper()
    manager = get_alert_manager()
    
    # Get price
    price_info = manager.get_price(symbol)
    
    if not price_info:
        return f"❌ No se pudo obtener el precio para {symbol}. Verifica que el símbolo sea correcto."
    
    # Format 24h change
    change_24h = price_info.get('change_24h')
    if change_24h is not None:
        if change_24h > 0:
            change_str = f"📈 +{change_24h:.2f}%"
        elif change_24h < 0:
            change_str = f"📉 {change_24h:.2f}%"
        else:
            change_str = "0.00%"
    else:
        change_str = "N/A"
    
    # Create response
    response = (
        f"*{symbol} - Precio Actual*\n\n"
        f"*Precio:* ${price_info['price']:.4f}\n"
        f"*Cambio 24h:* {change_str}\n"
        f"*Máximo 24h:* ${price_info['high_24h']:.4f}\n"
        f"*Mínimo 24h:* ${price_info['low_24h']:.4f}\n\n"
        f"[Ver gráfico en TradingView]({price_info['chart_link']})"
    )
    
    return response


def cmd_alert_history(args, bot, user_id=None):
    """
    Show triggered alerts history
    
    Args:
        args (str): Command arguments (not used)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    manager = get_alert_manager()
    history = manager.alert_history.get_for_user(user_id)
    
    if not history:
        return "No tienes alertas activadas en el historial."
    
    response = "*Historial de Alertas Activadas:*\n\n"
    
    for i, entry in enumerate(history[:10], 1):
        # Format triggered time
        try:
            dt = datetime.datetime.fromisoformat(entry['triggered_at'])
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = entry['triggered_at']
        
        # Format conditions
        conditions_str = ", ".join(entry['conditions'])
        
        response += f"{i}. {conditions_str}\n   Activada: {time_str}\n\n"
    
    return response


def cmd_buy(args, bot, user_id=None):
    """
    Buy crypto in virtual portfolio
    
    Args:
        args (str): Command arguments (symbol amount)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    if not args:
        return "❌ *Error:* Formato incorrecto.\n\n*Uso correcto:* /buy SYMBOL AMOUNT_USD\n\n*Ejemplos:*\n• /buy BTC 1000 - Comprar $1000 de Bitcoin\n• /buy ETH 500 - Comprar $500 de Ethereum"
    
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ *Error:* Formato incorrecto.\n\n*Uso correcto:* /buy SYMBOL AMOUNT_USD\n\n*Ejemplos:*\n• /buy BTC 1000 - Comprar $1000 de Bitcoin\n• /buy ETH 500 - Comprar $500 de Ethereum"
    
    symbol = parts[0].upper()
    
    try:
        amount_usd = float(parts[1])
    except ValueError:
        return f"❌ *Error:* Cantidad inválida: '{parts[1]}'\n\nDebes especificar un valor numérico, por ejemplo: /buy {symbol} 1000"
    
    if amount_usd <= 0:
        return "❌ *Error:* La cantidad debe ser mayor que cero.\n\nEspecifica una cantidad positiva, por ejemplo: /buy {symbol} 1000"
    
    # Get current price
    manager = get_alert_manager()
    price_info = manager.get_price(symbol)
    
    if not price_info:
        return f"❌ No se pudo obtener el precio para {symbol}."
    
    # Execute buy
    result = manager.virtual_portfolio.buy(user_id, symbol, amount_usd, price_info['price'])
    
    if not result['success']:
        return f"❌ {result['message']}"
    
    # Get updated portfolio
    portfolio = manager.virtual_portfolio.get_portfolio_value(user_id, {symbol: price_info['price']})
    
    # Create response
    response = (
        f"*✅ Compra Exitosa*\n\n"
        f"{result['message']}\n\n"
        f"*Balance:* ${portfolio['balance_usd']:.2f}\n"
        f"*Valor de activos:* ${portfolio['total_asset_value']:.2f}\n"
        f"*Valor total:* ${portfolio['total_value']:.2f}"
    )
    
    return response


def cmd_sell(args, bot, user_id=None):
    """
    Sell crypto from virtual portfolio
    
    Args:
        args (str): Command arguments (symbol amount)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    if not args:
        return "❌ *Error:* Formato incorrecto.\n\n*Uso correcto:* /sell SYMBOL AMOUNT\n\n*Ejemplos:*\n• /sell BTC 0.05 - Vender 0.05 Bitcoin\n• /sell ETH 1.5 - Vender 1.5 Ethereum\n\nPuedes ver tu portafolio con /portfolio"
    
    parts = args.strip().split()
    if len(parts) < 2:
        return "❌ *Error:* Formato incorrecto.\n\n*Uso correcto:* /sell SYMBOL AMOUNT\n\n*Ejemplos:*\n• /sell BTC 0.05 - Vender 0.05 Bitcoin\n• /sell ETH 1.5 - Vender 1.5 Ethereum"
    
    symbol = parts[0].upper()
    
    try:
        amount = float(parts[1])
    except ValueError:
        return f"❌ *Error:* Cantidad inválida: '{parts[1]}'\n\nDebes especificar un valor numérico, por ejemplo: /sell {symbol} 0.5"
    
    if amount <= 0:
        return f"❌ *Error:* La cantidad debe ser mayor que cero.\n\nEspecifica una cantidad positiva, por ejemplo: /sell {symbol} 0.5"
    
    # Get current price
    manager = get_alert_manager()
    price_info = manager.get_price(symbol)
    
    if not price_info:
        return f"❌ No se pudo obtener el precio para {symbol}."
    
    # Execute sell
    result = manager.virtual_portfolio.sell(user_id, symbol, amount, price_info['price'])
    
    if not result['success']:
        return f"❌ {result['message']}"
    
    # Get updated portfolio
    portfolio = manager.virtual_portfolio.get_portfolio_value(user_id, {symbol: price_info['price']})
    
    # Create response
    response = (
        f"*✅ Venta Exitosa*\n\n"
        f"{result['message']}\n\n"
        f"*Balance:* ${portfolio['balance_usd']:.2f}\n"
        f"*Valor de activos:* ${portfolio['total_asset_value']:.2f}\n"
        f"*Valor total:* ${portfolio['total_value']:.2f}"
    )
    
    return response


def cmd_portfolio(args, bot, user_id=None):
    """
    Show virtual portfolio
    
    Args:
        args (str): Command arguments (not used)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message
    """
    manager = get_alert_manager()
    
    # Get all symbols in portfolio
    portfolio = manager.virtual_portfolio.get_portfolio(user_id)
    symbols = list(portfolio['assets'].keys())
    
    if not symbols:
        return f"*💰 Tu Portafolio Virtual*\n\n*Balance:* ${portfolio['balance_usd']:.2f}\n\nNo tienes activos en tu portafolio."
    
    # Get current prices
    prices = {}
    for symbol in symbols:
        price_info = manager.get_price(symbol)
        if price_info:
            prices[symbol] = price_info['price']
    
    # Get portfolio value
    portfolio_value = manager.virtual_portfolio.get_portfolio_value(user_id, prices)
    
    # Create response
    response = (
        f"*💰 Tu Portafolio Virtual*\n\n"
        f"*Balance:* ${portfolio_value['balance_usd']:.2f}\n"
        f"*Valor de activos:* ${portfolio_value['total_asset_value']:.2f}\n"
        f"*Valor total:* ${portfolio_value['total_value']:.2f}\n\n"
        f"*Activos:*\n"
    )
    
    for symbol, asset_info in portfolio_value['assets'].items():
        response += f"• {symbol}: {asset_info['amount']:.6f} (${asset_info['value']:.2f})\n"
    
    return response


def cmd_to_the_moon(args, bot, user_id=None):
    """
    Easter egg - to the moon GIF
    
    Args:
        args (str): Command arguments (not used)
        bot: Bot instance (not used)
        user_id (str): User ID from message
        
    Returns:
        str: Response message with GIF
    """
    manager = get_alert_manager()
    gif_url = manager.to_the_moon()
    
    return f"🚀 *TO THE MOON!* 🌕\n\n{gif_url}"


def cmd_analyze_ai(args, bot, user_id=None, chat_id=None):
    """
    Generate AI-powered market analysis for a cryptocurrency
    
    Args:
        args (str): Command arguments (symbol [length])
        bot: Bot instance (not used)
        user_id (str): User ID from message
        chat_id (int, optional): Chat ID to send initial message
        
    Returns:
        str: AI-generated market analysis
    """
    if not args:
        return "❌ Error: Debes especificar un símbolo de criptomoneda.\n\nUso correcto: /analyze_ai SYMBOL [corto|normal|largo]\n\nEjemplos:\n• /analyze_ai BTC\n• /analyze_ai ETH corto\n• /analyze_ai ADA largo"
    
    # Parse arguments
    parts = args.strip().split()
    symbol = parts[0].upper()
    
    # Check if length is specified
    length = "normal"  # Default
    if len(parts) > 1:
        length_arg = parts[1].lower()
        if length_arg in ["corto", "short"]:
            length = "short"
        elif length_arg in ["largo", "long"]:
            length = "long"
    
    # Send chat action and waiting message to indicate analysis is in progress
    if chat_id:
        from utils.telegram_utils import send_chat_action, send_telegram_message
        # Send typing action to indicate processing
        send_chat_action("typing", chat_id)
        # Send a message to inform the user that analysis is being generated
        waiting_message = f"🧠 Generando análisis de mercado para {symbol} (formato {length})...\n\nEsto puede tardar unos segundos. Por favor, espera mientras nuestro analista de IA evalúa la situación actual del mercado."
        send_telegram_message(waiting_message, chat_id=chat_id)
    
    try:
        # Get analysis from OpenAI with specified length
        analysis = analyze_crypto(symbol, length)
        
        if analysis.startswith("❌ Error"):
            return analysis
        
        # Get TradingView chart link
        chart_link = ""
        try:
            # Try to get chart link from price provider
            manager = get_alert_manager()
            chart_link = manager.price_provider._get_tradingview_link(symbol)
        except Exception:
            # If that fails, use a default link format
            base_symbol = symbol.split('-')[0].split('/')[0]
            chart_link = f"https://es.tradingview.com/symbols/{base_symbol}USD/"
        
        # Format the response with the AI analysis and chart link
        response = (
            f"🧠 Análisis de Mercado con IA - {symbol}\n\n"
            f"{analysis}\n\n"
            f"[Ver gráfico en TradingView]({chart_link})"
        )
        
        return response
    except Exception as e:
        return f"❌ Error al generar análisis: {str(e)}\n\nPor favor, intenta de nuevo más tarde o contacta al administrador del bot."


def initialize_alerts():
    """
    Initialize the alert system
    """
    # Load API key from sensitive-data.txt
    load_api_key()
    
    manager = get_alert_manager()
    manager.start_monitoring()
    return manager
