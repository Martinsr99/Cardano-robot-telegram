"""
Advanced Trading Bot - Main Entry Point

This bot analyzes cryptocurrency markets, identifies trading opportunities,
and sends notifications for buy/sell signals.
"""

import sys
import time
import datetime
import traceback
import os
from config import SYMBOL, CHECK_INTERVAL, SEND_ALERT, SIMULATED_INVESTMENT, TELEGRAM_COMMANDS_ENABLED
from models import Position, TradeHistory
from data_provider import MarketData
from signals import SignalGenerator
from notifier import send_telegram_message, register_bot
from forecast_system.integration import ForecastIntegration
from price_alerts_refactored import initialize_alerts
from utils import (
    format_price, calculate_quantity, format_position_summary,
    format_profit_loss, format_signal_strength, sleep_with_progress, handle_error
)

class TradingBot:
    """
    Main trading bot class that orchestrates the trading process.
    """
    def __init__(self):
        """Initialize the trading bot"""
        self.market_data = MarketData()
        self.position = Position.load()
        self.signal_generator = None
        self.history = TradeHistory()
        self.last_analysis_time = None
        self.last_analysis_result = None
        self.last_price = None
        self.forecast_integration = ForecastIntegration(self)
        self.callbacks = {
            'on_price_update': [],
            'on_analysis_complete': [],
            'on_position_update': [],
            'on_signal': []
        }
    
    def register_callback(self, event_type, callback):
        """Register a callback for a specific event"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def _notify_callbacks(self, event_type, data=None):
        """Notify all callbacks for a specific event"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in callback: {e}")
    
    def initialize(self):
        """Initialize the bot components"""
        print("🤖 Iniciando Advanced Trading Bot...")
        
        # Load current position
        if self.position.active:
            print(f"📋 Posición activa encontrada:")
            print(format_position_summary(self.position))
        else:
            print("📋 No hay posiciones activas")
        
        # Fetch market data
        if not self.market_data.fetch_data():
            print("❌ No se pudo obtener datos del mercado. Abortando.")
            return False
        
        # Initialize signal generator
        self.signal_generator = SignalGenerator(self.market_data)
        
        # Get latest price
        self.last_price = self.market_data.get_latest_price()
        self._notify_callbacks('on_price_update', self.last_price)
        
        # Show recent operations summary
        self._show_recent_operations_summary()
        
        # Register bot for Telegram commands
        if TELEGRAM_COMMANDS_ENABLED:
            register_bot(self)
            
            # Register forecast commands
            import notifier
            self.forecast_integration.register_telegram_commands(notifier)
            
            # Initialize price alerts system
            try:
                initialize_alerts()
                print("🔔 Sistema de alertas de precio inicializado")
            except Exception as e:
                print(f"❌ Error al inicializar el sistema de alertas: {e}")
        
        return True
    
    def _show_recent_operations_summary(self):
        """Show a summary of recent operations"""
        recent_trades = self.history.get_recent_trades(5)
        
        if not recent_trades:
            print("📊 No hay operaciones anteriores registradas.")
            return
        
        print("\n📊 Resumen de operaciones recientes:")
        for trade in recent_trades:
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
                
                print(f"  • {symbol}: {format_price(entry_price)} → {format_price(exit_price)}")
                print(f"    {profit_pct:.2%} ({format_price(profit_amount)}), Duración: {duration}")
                print(f"    Razón: {reason}")
            else:
                print(f"  • {symbol}: {format_price(entry_price)} (Posición abierta desde {entry_time})")
            
            print("")
    
    def analyze_market(self):
        """Analyze the market and generate signals"""
        # Get current time and price
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_price = self.market_data.get_latest_price()
        
        print(f"\n⏰ Análisis a las {current_time} - {SYMBOL}: {format_price(current_price)}")
        
        # Check for signals based on position status
        if self.position.active:
            self._check_sell_signals()
        else:
            self._check_buy_signals()
        
        print("\n✅ Análisis completado con éxito.")
    
    def _check_buy_signals(self):
        """Check for buy signals"""
        # Get buy signal
        is_buy, strength, reason = self.signal_generator.check_buy_signal()
        
        # Display signal information
        print(f"🔍 Análisis de compra: {reason}")
        print(format_signal_strength(strength))
        
        # Store analysis result
        self.last_analysis_result = {
            'type': 'buy',
            'is_signal': is_buy,
            'strength': strength,
            'reason': reason,
            'time': datetime.datetime.now()
        }
        self.last_analysis_time = datetime.datetime.now()
        
        # Notify callbacks
        self._notify_callbacks('on_analysis_complete', self.last_analysis_result)
        
        # Process buy signal
        if is_buy:
            current_price = self.market_data.get_latest_price()
            quantity = calculate_quantity(current_price)
            
            # Get price trend analysis
            trend_direction, trend_strength, trend_description = self.signal_generator.analyze_price_trend()
            
            # Create notification message
            msg = (
                f"*🔔 SEÑAL DE COMPRA para {SYMBOL}*\n"
                f"💰 *Precio:* `{format_price(current_price)}`\n"
                f"💪 *Fuerza de la señal:* `{strength:.2f}`\n"
                f"📝 *Análisis:* `{reason}`\n"
                f"💵 *Inversión:* `${SIMULATED_INVESTMENT:.2f}`\n"
                f"🔢 *Cantidad:* `{quantity:.6f}`"
            )
            
            print("\n" + msg.replace("*", "").replace("`", ""))
            
            # Calculate estimated take profit and stop loss
            take_profit_price = current_price * (1 + PROFIT_TARGET)
            stop_loss_price = current_price * (1 - STOP_LOSS)
            
            # Add to notification
            msg += (
                f"\n📈 *Take Profit:* `{format_price(take_profit_price)}`\n"
                f"📉 *Stop Loss:* `{format_price(stop_loss_price)}`\n\n"
                f"📊 *Tendencia del Mercado:*\n"
                f"`{trend_description}`"
            )
            
            # Send notification with alert recording
            signal_data = {
                'price': current_price,
                'strength': strength,
                'take_profit': take_profit_price,
                'stop_loss': stop_loss_price
            }
            
            if SEND_ALERT:
                send_telegram_message(msg, alert_type='buy', data=signal_data)
            
            # Open position
            self.position.open(SYMBOL, current_price, quantity, reason)
            print("📈 Posición abierta")
            
            # Notify callbacks
            self._notify_callbacks('on_position_update', self.position)
            self._notify_callbacks('on_signal', {
                'type': 'buy',
                'price': current_price,
                'reason': reason,
                'take_profit': take_profit_price,
                'stop_loss': stop_loss_price
            })
    
    def _check_sell_signals(self):
        """Check for sell signals"""
        # Get sell signal
        is_sell, reason = self.signal_generator.check_sell_signal(self.position)
        
        # Display signal information
        current_price = self.market_data.get_latest_price()
        print(f"🔍 Análisis de venta: {reason}")
        print(format_profit_loss(self.position.entry_price, current_price, self.position.quantity))
        
        # Store analysis result
        self.last_analysis_result = {
            'type': 'sell',
            'is_signal': is_sell,
            'reason': reason,
            'time': datetime.datetime.now()
        }
        self.last_analysis_time = datetime.datetime.now()
        
        # Notify callbacks
        self._notify_callbacks('on_analysis_complete', self.last_analysis_result)
        
        # Process sell signal
        if is_sell:
            profit_pct = (current_price - self.position.entry_price) / self.position.entry_price
            profit_amount = self.position.quantity * self.position.entry_price * profit_pct
            
            # Determine if take profit or stop loss was hit
            is_take_profit = profit_pct >= PROFIT_TARGET
            is_stop_loss = profit_pct <= -STOP_LOSS
            
            tp_sl_status = ""
            if is_take_profit:
                tp_sl_status = "✅ Take Profit alcanzado"
            elif is_stop_loss:
                tp_sl_status = "🛑 Stop Loss activado"
            
            # Get price trend analysis
            trend_direction, trend_strength, trend_description = self.signal_generator.analyze_price_trend()
            
            # Create notification message
            msg = (
                f"*🔔 SEÑAL DE VENTA para {SYMBOL}*\n"
                f"💰 *Precio de entrada:* `{format_price(self.position.entry_price)}`\n"
                f"💰 *Precio actual:* `{format_price(current_price)}`\n"
                f"📊 *Beneficio/Pérdida:* `{profit_pct:.2%} ({format_price(profit_amount)})`\n"
                f"⏱️ *Tiempo en posición:* `{(datetime.datetime.now() - self.position.entry_time).days} días`\n"
                f"📝 *Razón:* `{reason}`"
            )
            
            # Add TP/SL status if applicable
            if tp_sl_status:
                msg += f"\n🎯 *Estado:* `{tp_sl_status}`"
                
            # Add trend analysis
            msg += (
                f"\n\n📊 *Tendencia del Mercado:*\n"
                f"`{trend_description}`"
            )
            
            print("\n" + msg.replace("*", "").replace("`", ""))
            
            # Send notification with alert recording
            signal_data = {
                'entry_price': self.position.entry_price,
                'exit_price': current_price,
                'profit_pct': profit_pct,
                'profit_amount': profit_amount,
                'is_take_profit': is_take_profit,
                'is_stop_loss': is_stop_loss
            }
            
            if SEND_ALERT:
                send_telegram_message(msg, alert_type='sell', data=signal_data)
            
            # Close position
            self.position.close(current_price, reason)
            print("📉 Posición cerrada")
            
            # Notify callbacks
            self._notify_callbacks('on_position_update', self.position)
            self._notify_callbacks('on_signal', {
                'type': 'sell',
                'price': current_price,
                'reason': reason,
                'profit_pct': profit_pct,
                'profit_amount': profit_amount
            })
    
    def run_once(self):
        """Run the bot once"""
        try:
            if not self.initialize():
                return False
            
            # Comprobar último pronóstico al iniciar
            check_results = self.forecast_integration.check_forecast_on_startup()
            if "message" in check_results and not "error" in check_results:
                print(f"\n🔮 Comprobación de pronóstico: {check_results['message']}")
                if "accuracy_message" in check_results:
                    print(f"   {check_results['accuracy_message']}")
            
            # Generar nuevo pronóstico si no hay uno reciente
            if not self.forecast_integration.forecast_system.forecast_manager.get_latest_forecast():
                print("\n🔮 Generando pronóstico inicial...")
                self.forecast_integration.generate_new_forecast()
            
            self.analyze_market()
            return True
            
        except Exception as e:
            error_msg = handle_error(e, "en el análisis")
            # Record error in history
            self.history.add_alert({
                'type': 'error',
                'message': error_msg,
                'traceback': traceback.format_exc()
            })
            return False
    
    def run_continuously(self, update_interval=None):
        """Run the bot continuously"""
        print("🔄 Iniciando monitoreo continuo del mercado...")
        
        # Use provided interval or default
        interval = update_interval if update_interval is not None else CHECK_INTERVAL
        
        while True:
            try:
                success = self.run_once()
                
                if not success:
                    print("⚠️ Error en la ejecución. Reintentando en 5 minutos...")
                    time.sleep(300)
                    continue
                
                # Wait for next check
                if update_interval is None:  # Only show progress in CLI mode
                    sleep_with_progress(interval)
                else:
                    time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoreo detenido por el usuario.")
                break
            except Exception as e:
                error_msg = handle_error(e, "crítico")
                # Record error in history
                self.history.add_alert({
                    'type': 'critical_error',
                    'message': error_msg,
                    'traceback': traceback.format_exc()
                })
                print(f"{error_msg}\nEl monitoreo se ha detenido debido a un error.")
                break

    def analyze_market(self):
        """Analyze the market and generate signals"""
        # Get current time and price
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_price = self.market_data.get_latest_price()
        
        # Update last price and notify callbacks
        if current_price != self.last_price:
            self.last_price = current_price
            self._notify_callbacks('on_price_update', current_price)
        
        print(f"\n⏰ Análisis a las {current_time} - {SYMBOL}: {format_price(current_price)}")
        
        # Check for signals based on position status
        if self.position.active:
            self._check_sell_signals()
        else:
            self._check_buy_signals()
        
        print("\n✅ Análisis completado con éxito.")

def main():
    """Main entry point"""
    bot = TradingBot()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor":
            bot.run_continuously()
        elif sys.argv[1] == "--ui":
            # Import UI module only when needed
            from ui import start_ui
            start_ui(bot)
        else:
            print(f"Opción desconocida: {sys.argv[1]}")
            print("Opciones disponibles: --monitor, --ui")
    else:
        bot.run_once()
        print("\nPara monitoreo continuo, ejecute: python main.py --monitor")
        print("Para iniciar con interfaz gráfica, ejecute: python main.py --ui")

if __name__ == "__main__":
    main()
