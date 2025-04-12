"""
Data models for the trading bot.
"""

import json
import os
import datetime
import uuid
from config import POSITION_FILE, HISTORY_FILE

class TradeHistory:
    """
    Manages the trading history.
    """
    def __init__(self):
        self.trades = []
        self.alerts = []
        self.load()
    
    def add_trade(self, trade_data):
        """Add a trade to history"""
        # Add a unique ID and timestamp if not present
        if 'id' not in trade_data:
            trade_data['id'] = str(uuid.uuid4())
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.datetime.now().isoformat()
        
        self.trades.append(trade_data)
        self.save()
        return trade_data['id']
    
    def add_alert(self, alert_data):
        """Add an alert to history"""
        # Add a unique ID and timestamp if not present
        if 'id' not in alert_data:
            alert_data['id'] = str(uuid.uuid4())
        if 'timestamp' not in alert_data:
            alert_data['timestamp'] = datetime.datetime.now().isoformat()
        
        self.alerts.append(alert_data)
        self.save()
        return alert_data['id']
    
    def get_recent_trades(self, limit=10):
        """Get recent trades"""
        return sorted(self.trades, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    def get_recent_alerts(self, limit=10):
        """Get recent alerts"""
        return sorted(self.alerts, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    def save(self):
        """Save history to file"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump({
                'trades': self.trades,
                'alerts': self.alerts
            }, f, indent=2)
    
    def load(self):
        """Load history from file"""
        if not os.path.exists(HISTORY_FILE):
            self.trades = []
            self.alerts = []
            return
        
        try:
            with open(HISTORY_FILE, 'r') as f:
                data = json.load(f)
                self.trades = data.get('trades', [])
                self.alerts = data.get('alerts', [])
        except Exception as e:
            print(f"Error loading history: {e}")
            self.trades = []
            self.alerts = []

class Position:
    """
    Represents a trading position with entry price, time, and quantity.
    """
    def __init__(self, symbol=None, entry_price=None, entry_time=None, quantity=None):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.quantity = quantity
        self.active = False
        self.trade_id = None
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
    
    def open(self, symbol, entry_price, quantity, reason=""):
        """Open a new position"""
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = datetime.datetime.now()
        self.quantity = quantity
        self.active = True
        
        # Record trade in history
        history = TradeHistory()
        trade_data = {
            'symbol': symbol,
            'entry_price': entry_price,
            'entry_time': self.entry_time.isoformat(),
            'quantity': quantity,
            'status': 'open',
            'entry_reason': reason
        }
        self.trade_id = history.add_trade(trade_data)
        
        self.save()
        
    def close(self, exit_price=None, reason=""):
        """Close the current position"""
        self.active = False
        self.exit_time = datetime.datetime.now()
        self.exit_price = exit_price
        self.exit_reason = reason
        
        # Update trade in history
        if self.trade_id:
            history = TradeHistory()
            for trade in history.trades:
                if trade.get('id') == self.trade_id:
                    trade['status'] = 'closed'
                    trade['exit_price'] = exit_price
                    trade['exit_time'] = self.exit_time.isoformat()
                    trade['exit_reason'] = reason
                    
                    # Calculate profit/loss
                    if exit_price and self.entry_price:
                        profit_pct = (exit_price - self.entry_price) / self.entry_price
                        profit_amount = self.quantity * self.entry_price * profit_pct
                        trade['profit_pct'] = profit_pct
                        trade['profit_amount'] = profit_amount
                        
                    # Calculate duration
                    if self.entry_time:
                        duration = (self.exit_time - self.entry_time).total_seconds()
                        trade['duration_seconds'] = duration
                    
                    history.save()
                    break
        
    def save(self):
        """Save position to file"""
        with open(POSITION_FILE, 'w') as f:
            json.dump({
                'symbol': self.symbol,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time.isoformat() if self.entry_time else None,
                'quantity': self.quantity,
                'active': self.active
            }, f)
    
    @classmethod
    def load(cls):
        """Load position from file"""
        if not os.path.exists(POSITION_FILE):
            return cls()
        
        with open(POSITION_FILE, 'r') as f:
            try:
                data = json.load(f)
                position = cls()
                position.symbol = data.get('symbol')
                position.entry_price = data.get('entry_price')
                position.entry_time = datetime.datetime.fromisoformat(data['entry_time']) if data.get('entry_time') else None
                position.quantity = data.get('quantity')
                position.active = data.get('active', False)
                return position
            except Exception as e:
                print(f"Error loading position: {e}")
                return cls()
    
    def __str__(self):
        if not self.active:
            return "No active position"
        
        return f"Position: {self.symbol} at ${self.entry_price:.4f}, quantity: {self.quantity:.6f}"
