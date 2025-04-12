import threading
import time
import json
import requests
from datetime import datetime
from models import TradeHistory
from config import (
    TELEGRAM_COMMANDS_ENABLED, TELEGRAM_POLL_INTERVAL,
    TELEGRAM_ALLOWED_USERS, SYMBOL
)
from telegram_utils import send_telegram_message, TELEGRAM_TOKEN
from price_alerts_refactored import (
    cmd_alert, cmd_my_alerts, cmd_cancel, cmd_price,
    cmd_alert_history, cmd_buy, cmd_sell, cmd_portfolio,
    cmd_to_the_moon, cmd_analyze_ai, initialize_alerts
)

# TradingView chart link
TRADINGVIEW_CHART_ID = "ENQ6RrtR"

def get_tradingview_link(symbol=SYMBOL):
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

# Import from telegram_utils instead

# Global variables
last_update_id = 0
bot_instance = None
command_handlers = {}

def register_bot(bot):
    """
    Register the bot instance for command handling
    
    Args:
        bot: TradingBot instance
    """
    global bot_instance
    bot_instance = bot
    
    # Start the message polling thread if enabled
    if TELEGRAM_COMMANDS_ENABLED:
        start_polling()

def register_command(command, handler, description):
    """
    Register a command handler
    
    Args:
        command (str): Command name (without /)
        handler (callable): Function to handle the command
        description (str): Command description for help
    """
    command_handlers[command] = {
        'handler': handler,
        'description': description
    }

def start_polling():
    """Start polling for new messages"""
    thread = threading.Thread(target=_poll_messages)
    thread.daemon = True
    thread.start()
    print("🤖 Telegram command polling started")

def _poll_messages():
    """Poll for new messages"""
    global last_update_id
    
    while True:
        try:
            updates = get_updates(last_update_id)
            
            if updates and 'result' in updates and updates['result']:
                for update in updates['result']:
                    # Process update
                    if 'update_id' in update:
                        last_update_id = update['update_id'] + 1
                    
                    # Process message
                    if 'message' in update:
                        process_message(update['message'])
            
            # Sleep before next poll
            time.sleep(TELEGRAM_POLL_INTERVAL)
            
        except Exception as e:
            print(f"❌ Error polling messages: {e}")
            time.sleep(TELEGRAM_POLL_INTERVAL * 2)  # Wait longer on error

def get_updates(offset=0):
    """
    Get updates from Telegram
    
    Args:
        offset (int): Offset for updates
        
    Returns:
        dict: Updates response
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {
            "offset": offset,
            "timeout": 30
        }
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return None

def process_message(message):
    """
    Process a message from Telegram
    
    Args:
        message (dict): Message data
    """
    # Check if message contains text
    if 'text' not in message:
        return
    
    # Check if sender is allowed
    sender_id = None
    if 'from' in message and 'id' in message['from']:
        sender_id = str(message['from']['id'])
        if sender_id not in TELEGRAM_ALLOWED_USERS:
            print(f"⚠️ Unauthorized message from {sender_id}")
            return
    
    # Process command
    text = message['text']
    chat_id = message['chat']['id']
    
    if text.startswith('/'):
        # Extract command and arguments
        parts = text[1:].split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Handle command
        handle_command(command, args, chat_id, sender_id)

def handle_command(command, args, chat_id, user_id=None):
    """
    Handle a command
    
    Args:
        command (str): Command name
        args (str): Command arguments
        chat_id (int): Chat ID to respond to
        user_id (str): User ID who sent the command
    """
    global bot_instance
    
    # Check if bot is registered
    if bot_instance is None and command not in ['help', 'start']:
        send_telegram_message("❌ Bot no inicializado", chat_id=chat_id)
        return
    
    # Handle built-in commands
    if command == 'help':
        send_help(chat_id)
        return
    
    # Handle start command (when user initiates chat)
    if command == 'start':
        welcome_message = (
            f"*¡Bienvenido al Bot de Trading para {SYMBOL}!* 🤖\n\n"
            f"Este bot analiza el mercado de criptomonedas, detecta señales de compra y venta, "
            f"y te mantiene informado sobre el estado de tus operaciones.\n\n"
            f"*Comandos disponibles:*\n"
        )
        
        # Add command descriptions
        for cmd, info in command_handlers.items():
            welcome_message += f"/{cmd} - {info['description']}\n"
        
        # Add help command
        welcome_message += f"\n/help - Muestra esta ayuda\n\n"
        
        # Add usage tips
        welcome_message += (
            "*Consejos de uso:*\n"
            "• Usa /status para ver el estado actual del bot\n"
            "• Usa /trend para ver el análisis de tendencia del mercado\n"
            "• Usa /price para ver el precio actual e indicadores\n"
            "• Usa /history para ver el historial de operaciones\n\n"
            "¡Disfruta usando el bot! 📈"
        )
        
        send_telegram_message(welcome_message, chat_id=chat_id)
        return
    
    # Handle registered commands
    if command in command_handlers:
        try:
            # Check if the command handler accepts a user_id parameter
            if command in ['alert', 'my_alerts', 'cancel', 'price', 'alert_history', 
                          'buy', 'sell', 'portfolio', 'to_the_moon']:
                response = command_handlers[command]['handler'](args, bot_instance, user_id)
            # Check if the command handler needs chat_id for sending initial messages
            elif command in ['forecast', 'analyze_ai']:
                response = command_handlers[command]['handler'](args, bot_instance, user_id, chat_id)
            else:
                response = command_handlers[command]['handler'](args, bot_instance)
            send_telegram_message(response, chat_id=chat_id)
        except Exception as e:
            send_telegram_message(f"❌ Error: {str(e)}", chat_id=chat_id)
    else:
        send_telegram_message(f"❓ Comando desconocido: /{command}\nUsa /help para ver los comandos disponibles", chat_id=chat_id)

def send_help(chat_id):
    """
    Send help message
    
    Args:
        chat_id (int): Chat ID to respond to
    """
    help_text = "*Comandos disponibles:*\n\n"
    
    # Add built-in commands
    help_text += "/help - Muestra esta ayuda\n\n"
    
    # Add registered commands
    for cmd, info in command_handlers.items():
        help_text += f"/{cmd} - {info['description']}\n"
    
    send_telegram_message(help_text, chat_id=chat_id)

# These functions are now in telegram_utils.py

# Register command handlers
def cmd_status(args, bot):
    """Get current bot status"""
    if not bot:
        return "❌ Bot no disponible"
    
    # Get current price
    current_price = bot.last_price
    price_str = f"${current_price:.4f}" if current_price else "N/A"
    
    # Get position status
    position = bot.position
    if position.active:
        profit_pct = (current_price - position.entry_price) / position.entry_price if current_price else 0
        profit_amount = position.quantity * position.entry_price * profit_pct if current_price else 0
        
        position_str = (
            f"*Posición activa:* {position.symbol}\n"
            f"*Precio de entrada:* ${position.entry_price:.4f}\n"
            f"*Cantidad:* {position.quantity:.6f}\n"
            f"*P/L actual:* {profit_pct:.2%} (${profit_amount:.2f})"
        )
    else:
        position_str = "*No hay posición activa*"
    
    # Get last analysis
    last_analysis = ""
    if bot.last_analysis_result:
        analysis_type = bot.last_analysis_result.get('type', 'unknown')
        reason = bot.last_analysis_result.get('reason', 'N/A')
        time_str = bot.last_analysis_time.strftime("%Y-%m-%d %H:%M:%S") if bot.last_analysis_time else "N/A"
        
        last_analysis = (
            f"*Último análisis ({time_str}):*\n"
            f"Tipo: {analysis_type}\n"
            f"Razón: {reason}"
        )
    
    # Get TradingView chart link
    chart_link = get_tradingview_link(SYMBOL)
    
    # Compose response
    response = (
        f"*Estado del Bot - {SYMBOL}*\n\n"
        f"*Precio actual:* {price_str}\n\n"
        f"{position_str}\n\n"
        f"{last_analysis}\n\n"
        f"[Ver gráfico en TradingView]({chart_link})"
    )
    
    return response

def cmd_history(args, bot):
    """Get trade history"""
    if not bot:
        return "❌ Bot no disponible"
    
    # Parse limit argument
    limit = 5  # Default
    if args:
        try:
            limit = int(args)
        except ValueError:
            return "❌ Argumento inválido. Uso: /history [número]"
    
    # Get recent trades
    trades = bot.history.get_recent_trades(limit)
    
    if not trades:
        return "📊 No hay operaciones registradas."
    
    # Compose response
    response = f"*Historial de Operaciones ({len(trades)})*\n\n"
    
    for trade in trades:
        status = trade.get('status', 'unknown')
        symbol = trade.get('symbol', 'unknown')
        entry_price = trade.get('entry_price', 0)
        entry_time = trade.get('entry_time', 'unknown')
        
        if status == 'closed':
            exit_price = trade.get('exit_price', 0)
            exit_time = trade.get('exit_time', 'unknown')
            profit_pct = trade.get('profit_pct', 0)
            profit_amount = trade.get('profit_amount', 0)
            reason = trade.get('exit_reason', 'unknown')
            
            # Format duration
            duration_seconds = trade.get('duration_seconds', 0)
            if duration_seconds:
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"{int(hours)}h {int(minutes)}m"
            else:
                duration = "N/A"
            
            trade_str = (
                f"*{symbol}*: ${entry_price:.4f} → ${exit_price:.4f}\n"
                f"P/L: {profit_pct:.2%} (${profit_amount:.2f})\n"
                f"Duración: {duration}\n"
                f"Razón: {reason}\n"
            )
        else:
            trade_str = (
                f"*{symbol}*: ${entry_price:.4f} (Abierta)\n"
                f"Desde: {entry_time}\n"
            )
        
        response += f"{trade_str}\n"
    
    return response

def cmd_signals(args, bot):
    """Get recent signals"""
    if not bot:
        return "❌ Bot no disponible"
    
    # Parse limit argument
    limit = 5  # Default
    if args:
        try:
            limit = int(args)
        except ValueError:
            return "❌ Argumento inválido. Uso: /signals [número]"
    
    # Get recent alerts
    alerts = bot.history.get_recent_alerts(limit)
    
    if not alerts:
        return "📊 No hay señales registradas."
    
    # Compose response
    response = f"*Señales Recientes ({len(alerts)})*\n\n"
    
    for alert in alerts:
        alert_type = alert.get('type', 'unknown')
        timestamp = alert.get('timestamp', 'unknown')
        message = alert.get('message', 'N/A')
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = timestamp
        
        # Format based on type
        if alert_type == 'buy':
            type_str = "🟢 COMPRA"
        elif alert_type == 'sell':
            type_str = "🔴 VENTA"
        elif alert_type == 'error':
            type_str = "⚠️ ERROR"
        else:
            type_str = alert_type.upper()
        
        alert_str = (
            f"*{type_str}* ({time_str})\n"
            f"{message}\n"
        )
        
        response += f"{alert_str}\n"
    
    return response

def cmd_price(args, bot):
    """Get current price and indicators"""
    if not bot:
        return "❌ Bot no disponible"
    
    # Get current price
    current_price = bot.last_price
    if not current_price:
        return "❌ Precio no disponible"
    
    # Get indicators
    indicators = bot.market_data.get_latest_indicators()
    if not indicators:
        return f"*Precio de {SYMBOL}:* ${current_price:.4f}\n\n❌ Indicadores no disponibles"
    
    # Format indicators
    rsi = indicators.get('rsi', 'N/A')
    sma_short = indicators.get('sma_short', 'N/A')
    sma_long = indicators.get('sma_long', 'N/A')
    macd_line = indicators.get('macd_line', 'N/A')
    macd_signal = indicators.get('macd_signal', 'N/A')
    macd_histogram = indicators.get('macd_histogram', 'N/A')
    
    # Get TradingView chart link
    chart_link = get_tradingview_link(SYMBOL)
    
    # Compose response
    response = (
        f"*{SYMBOL} - Análisis Técnico*\n\n"
        f"*Precio:* ${current_price:.4f}\n\n"
        f"*Indicadores:*\n"
        f"RSI: {rsi:.2f}\n"
        f"SMA Corta: ${sma_short:.4f}\n"
        f"SMA Larga: ${sma_long:.4f}\n"
        f"MACD Línea: {macd_line:.6f}\n"
        f"MACD Señal: {macd_signal:.6f}\n"
        f"MACD Histograma: {macd_histogram:.6f}\n\n"
        f"[Ver gráfico en TradingView]({chart_link})"
    )
    
    return response

def cmd_analyze(args, bot):
    """Force market analysis"""
    if not bot:
        return "❌ Bot no disponible"
    
    try:
        # Run analysis
        bot.analyze_market()
        
        # Get result
        if bot.last_analysis_result:
            analysis_type = bot.last_analysis_result.get('type', 'unknown')
            is_signal = bot.last_analysis_result.get('is_signal', False)
            reason = bot.last_analysis_result.get('reason', 'N/A')
            
            signal_str = "✅ SEÑAL GENERADA" if is_signal else "❌ SIN SEÑAL"
            
            # Get TradingView chart link
            chart_link = get_tradingview_link(SYMBOL)
            
            response = (
                f"*Análisis Completado - {SYMBOL}*\n\n"
                f"*Tipo:* {analysis_type}\n"
                f"*Resultado:* {signal_str}\n"
                f"*Razón:* {reason}\n\n"
                f"[Ver gráfico en TradingView]({chart_link})"
            )
        else:
            response = "✅ Análisis completado, pero no hay resultados disponibles."
        
        return response
    except Exception as e:
        return f"❌ Error al analizar: {str(e)}"

def cmd_trend(args, bot):
    """Get market trend analysis"""
    if not bot:
        return "❌ Bot no disponible"
    
    if not bot.signal_generator:
        return "❌ Analizador de señales no inicializado"
    
    try:
        # Get trend analysis
        trend_direction, trend_strength, trend_description = bot.signal_generator.analyze_price_trend()
        
        # Get current price
        current_price = bot.last_price
        price_str = f"${current_price:.4f}" if current_price else "N/A"
        
        # Format trend emoji
        if trend_direction == "up":
            trend_emoji = "📈"
        elif trend_direction == "down":
            trend_emoji = "📉"
        else:
            trend_emoji = "📊"
        
        # Get TradingView chart link
        chart_link = get_tradingview_link(SYMBOL)
        
        # Compose response
        response = (
            f"*{trend_emoji} Análisis de Tendencia - {SYMBOL}*\n\n"
            f"*Precio actual:* {price_str}\n\n"
            f"*{trend_description}*\n\n"
        )
        
        # Add additional market context
        indicators = bot.market_data.get_latest_indicators()
        if indicators:
            rsi = indicators.get('rsi', 'N/A')
            macd_histogram = indicators.get('macd_histogram', 'N/A')
            
            response += (
                f"*Indicadores clave:*\n"
                f"• RSI: {rsi:.1f}\n"
                f"• MACD Histogram: {macd_histogram:.6f}\n"
            )
            
            # Add price action summary
            prices = bot.market_data.data['close']
            if len(prices) >= 5:
                change_1d = (prices[-1] - prices[-2]) / prices[-2]
                change_5d = (prices[-1] - prices[-5]) / prices[-5]
                
                response += (
                    f"\n*Movimiento de precio:*\n"
                    f"• 24h: {change_1d:.2%}\n"
                    f"• 5 días: {change_5d:.2%}\n\n"
                    f"[Ver gráfico en TradingView]({chart_link})"
                )
        
        return response
    except Exception as e:
        return f"❌ Error al analizar tendencia: {str(e)}"

def cmd_forecast(args, bot, chat_id=None):
    """Get price range forecast"""
    if not bot:
        return "❌ Bot no disponible"
    
    try:
        # Parse arguments
        parts = args.strip().split() if args else [SYMBOL.split('-')[0]]
        symbol = parts[0].upper()
        
        # Check if length is specified
        length = "normal"  # Default
        if len(parts) > 1:
            length_arg = parts[1].lower()
            if length_arg in ["corto", "short"]:
                length = "short"
            elif length_arg in ["largo", "long"]:
                length = "long"
        
        # Send initial message to indicate analysis is in progress
        if chat_id:
            initial_message = f"🧠 Generando análisis de mercado para {symbol} (formato {length})...\n\nEsto puede tardar unos segundos. Por favor, espera mientras nuestro analista de IA evalúa la situación actual del mercado."
            send_telegram_message(initial_message, chat_id=chat_id)
        
        # Get current price
        current_price = bot.last_price
        if not current_price:
            return f"❌ No se pudo obtener el precio actual para {symbol}"
        
        # Use AI analysis for forecasts
        try:
            from ai_analysis import analyze_crypto
            
            # Get analysis from OpenAI with specified length
            ai_analysis = analyze_crypto(symbol, length)
            
            # If there was an error in the analysis, return the error message
            if ai_analysis.startswith("❌ Error"):
                return ai_analysis
            
            # Get TradingView chart link
            chart_link = get_tradingview_link(symbol)
            
            # Compose response with AI analysis
            response = (
                f"🧠 Análisis de Mercado con IA - {symbol}\n\n"
                f"{ai_analysis}\n\n"
                f"[Ver gráfico en TradingView]({chart_link})"
            )
            
            return response
        except Exception as e:
            # If there's an error with the AI analysis, return a detailed error message
            error_msg = str(e)
            return f"❌ Error al generar análisis con IA: {error_msg}\n\nPor favor, intenta de nuevo más tarde o contacta al administrador del bot."
    except Exception as e:
        return f"❌ Error al generar pronóstico: {str(e)}"

# Register default commands
register_command('status', cmd_status, "Muestra el estado actual del bot")
register_command('history', cmd_history, "Muestra el historial de operaciones (uso: /history [número])")
register_command('signals', cmd_signals, "Muestra las señales recientes (uso: /signals [número])")
register_command('price', cmd_price, "Muestra el precio actual e indicadores (uso: /price SYMBOL)")
register_command('analyze', cmd_analyze, "Fuerza un análisis del mercado")
register_command('trend', cmd_trend, "Muestra el análisis de tendencia del mercado")
register_command('forecast', cmd_forecast, "Muestra el pronóstico de rango de precios (uso: /forecast [SYMBOL] [corto|normal|largo])")

# Price alert commands
register_command('alert', cmd_alert, "Crea o muestra alertas de precio (uso: /alert SYMBOL PRICE)")
register_command('my_alerts', cmd_my_alerts, "Muestra tus alertas de precio activas")
register_command('cancel', cmd_cancel, "Cancela alertas de precio (uso: /cancel SYMBOL o /cancel all)")
register_command('alert_history', cmd_alert_history, "Muestra el historial de alertas activadas")

# Virtual portfolio commands
register_command('buy', cmd_buy, "Compra criptomonedas en el portafolio virtual (uso: /buy SYMBOL AMOUNT_USD)")
register_command('sell', cmd_sell, "Vende criptomonedas del portafolio virtual (uso: /sell SYMBOL AMOUNT)")
register_command('portfolio', cmd_portfolio, "Muestra tu portafolio virtual")

# AI analysis command
register_command('analyze_ai', cmd_analyze_ai, "Genera un análisis de mercado con IA (uso: /analyze_ai SYMBOL [corto|normal|largo])")

# Easter eggs
register_command('to_the_moon', cmd_to_the_moon, "🚀 TO THE MOON!")

# Initialize price alerts system
try:
    initialize_alerts()
    print("🔔 Sistema de alertas de precio inicializado")
except Exception as e:
    print(f"❌ Error al inicializar el sistema de alertas: {e}")
