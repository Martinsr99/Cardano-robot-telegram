"""
Utility functions for the trading bot.
"""

import time
import datetime
import traceback
from config import SYMBOL, SIMULATED_INVESTMENT, CHECK_INTERVAL

def format_price(price):
    """
    Format price with appropriate precision.
    
    Args:
        price (float): Price to format
        
    Returns:
        str: Formatted price
    """
    if price is None:
        return "N/A"
    
    if price < 0.01:
        return f"${price:.6f}"
    elif price < 1:
        return f"${price:.4f}"
    elif price < 1000:
        return f"${price:.2f}"
    else:
        return f"${price:,.2f}"

def calculate_quantity(price):
    """
    Calculate quantity to buy based on investment amount.
    
    Args:
        price (float): Current price
        
    Returns:
        float: Quantity to buy
    """
    if price is None or price <= 0:
        return 0
    
    return SIMULATED_INVESTMENT / price

def format_position_summary(position):
    """
    Format position summary.
    
    Args:
        position: Position instance
        
    Returns:
        str: Formatted position summary
    """
    if not position.active:
        return "No active position"
    
    entry_time_str = position.entry_time.strftime("%Y-%m-%d %H:%M:%S") if position.entry_time else "N/A"
    days_held = (datetime.datetime.now() - position.entry_time).days if position.entry_time else 0
    
    return (
        f"Position: {position.symbol}\n"
        f"Entry Price: {format_price(position.entry_price)}\n"
        f"Quantity: {position.quantity:.6f}\n"
        f"Entry Time: {entry_time_str}\n"
        f"Days Held: {days_held}"
    )

def format_profit_loss(entry_price, current_price, quantity):
    """
    Format profit/loss information.
    
    Args:
        entry_price (float): Entry price
        current_price (float): Current price
        quantity (float): Quantity
        
    Returns:
        str: Formatted profit/loss information
    """
    if None in [entry_price, current_price, quantity]:
        return "P/L: N/A"
    
    profit_pct = (current_price - entry_price) / entry_price
    profit_amount = quantity * entry_price * profit_pct
    
    return f"P/L: {profit_pct:.2%} ({format_price(profit_amount)})"

def format_signal_strength(strength):
    """
    Format signal strength as a visual bar.
    
    Args:
        strength (float): Signal strength (0-1)
        
    Returns:
        str: Visual representation of signal strength
    """
    if strength is None:
        return "Signal: N/A"
    
    # Convert to percentage
    pct = int(strength * 100)
    
    # Create visual bar
    bar_length = 20
    filled_length = int(bar_length * strength)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    return f"Signal: {bar} {pct}%"

def sleep_with_progress(seconds):
    """
    Sleep with progress indication.
    
    Args:
        seconds (int): Seconds to sleep
    """
    minutes = seconds // 60
    print(f"\n⏳ Próximo análisis en {minutes} minutos...")
    
    # Show progress every minute
    for i in range(minutes):
        time.sleep(60)
        remaining = minutes - i - 1
        if remaining > 0:
            print(f"⌛ {remaining} minutos restantes...")

def handle_error(e, context=""):
    """
    Handle and log error.
    
    Args:
        e (Exception): Exception to handle
        context (str): Error context
    """
    error_msg = f"❌ Error {context}: {str(e)}"
    print(error_msg)
    traceback.print_exc()
    return error_msg
