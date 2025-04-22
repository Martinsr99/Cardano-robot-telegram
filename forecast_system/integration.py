"""
Integration - Integración del sistema de pronóstico con el bot de trading
"""

import os
import sys
import json
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Importar sistema de pronóstico
from forecast_system.forecast_system import ForecastSystem
from forecast_system.position_tracker import PositionTracker

# Importar componentes del bot de trading
# Asumimos que estamos en el mismo directorio que el bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_provider import MarketData
from signals import SignalGenerator
from models import TradeHistory
from utils.utils import format_price
from config.config import SYMBOL

class ForecastIntegration:
    """
    Integración del sistema de pronóstico con el bot de trading.
    """
    def __init__(self, bot=None):
        """
        Inicializa la integración.
        
        Args:
            bot: Instancia del bot de trading (opcional)
        """
        self.bot = bot
        self.forecast_system = ForecastSystem()
        self.position_tracker = PositionTracker()
        
        # Crear directorio para gráficos si no existe
        os.makedirs("forecast_system/visualization/output", exist_ok=True)
    
    def set_bot(self, bot):
        """
        Establece la instancia del bot de trading.
        
        Args:
            bot: Instancia del bot de trading
        """
        self.bot = bot
    
    def check_forecast_on_startup(self) -> Dict[str, Any]:
        """
        Comprueba el último pronóstico al iniciar el bot.
        
        Returns:
            Resultados de la comprobación
        """
        if not self.bot:
            return {"error": "Bot no inicializado"}
        
        # Obtener precio actual
        current_price = self.bot.last_price
        if not current_price:
            return {"error": "Precio actual no disponible"}
        
        # Comprobar último pronóstico
        check_results = self.forecast_system.check_last_forecast(current_price)
        
        # Si hay suficientes evaluaciones, entrenar el modelo
        stats = self.forecast_system.get_system_stats()
        if stats["evaluation_count"] >= 10:
            self.forecast_system.train_model()
        
        return check_results
    
    def generate_new_forecast(self, send_alert=True) -> Dict[str, Any]:
        """
        Genera un nuevo pronóstico basado en los datos actuales del mercado.
        
        Args:
            send_alert: Si es True, envía una alerta por Telegram si se detecta un movimiento significativo
            
        Returns:
            Datos del pronóstico generado
        """
        if not self.bot:
            return {"error": "Bot no inicializado"}
        
        # Obtener datos del mercado
        market_data = self.bot.market_data
        if not market_data:
            return {"error": "Datos de mercado no disponibles"}
        
        # Obtener generador de señales
        signal_generator = self.bot.signal_generator
        if not signal_generator:
            return {"error": "Generador de señales no disponible"}
        
        # Generar pronóstico
        forecast_data = signal_generator.forecast_price_range()
        if not forecast_data:
            return {"error": "No se pudo generar el pronóstico"}
        
        # Registrar pronóstico en el sistema
        forecast_id = self.forecast_system.register_forecast(forecast_data)
        
        # Obtener resumen del pronóstico
        forecast_summary = self.forecast_system.get_forecast_summary(forecast_id)
        
        # Verificar alertas pendientes
        current_price = self.bot.last_price
        verified_drop_alerts = self.forecast_system.forecast_manager.verify_pending_drop_alerts(current_price)
        verified_rise_alerts = self.forecast_system.forecast_manager.verify_pending_rise_alerts(current_price)
        
        # Enviar alertas si se detectan movimientos significativos
        if send_alert:
            from notifier import send_telegram_message
            from config.config import SYMBOL
            
            # Alerta de bajada
            if forecast_data.get('expected_drop', False):
                drop_pct = forecast_data.get('drop_pct', 0)
                drop_horizon = forecast_data.get('drop_horizon', 'desconocido')
                
                # Registrar alerta de bajada para verificación posterior
                alert_data = {
                    'drop_horizon': drop_horizon,
                    'drop_pct': drop_pct,
                    'current_price': current_price
                }
                
                alert_id = self.forecast_system.forecast_manager.register_drop_alert(
                    forecast_id,
                    alert_data
                )
                
                # Crear posición abierta a partir de la alerta
                position = self.position_tracker.open_position_from_alert(
                    {**alert_data, 'id': alert_id, 'timestamp': datetime.now().isoformat()},
                    SYMBOL
                )
                
                # Crear mensaje de alerta
                msg = (
                    f"*🔴 ALERTA DE BAJADA PARA {SYMBOL}*\n\n"
                    f"*Precio actual:* `{format_price(current_price)}`\n"
                    f"*Bajada esperada:* `{drop_pct:.2f}%`\n"
                    f"*Horizonte:* `{drop_horizon}`\n\n"
                    f"*Análisis:*\n"
                    f"Se ha detectado una posible oportunidad de venta debido a una bajada significativa "
                    f"esperada en el precio. Considere cerrar posiciones largas o abrir posiciones cortas.\n\n"
                    f"*ID de alerta:* `{alert_id}`\n"
                    f"Esta alerta será verificada automáticamente después del período indicado.\n\n"
                    f"Use el comando /forecast para ver el pronóstico completo."
                )
                
                # Enviar alerta
                send_telegram_message(msg, alert_type='drop_warning', data={
                    'price': current_price,
                    'drop_pct': drop_pct,
                    'drop_horizon': drop_horizon,
                    'alert_id': alert_id
                })
            
            # Alerta de subida
            if forecast_data.get('expected_rise', False):
                rise_pct = forecast_data.get('rise_pct', 0)
                rise_horizon = forecast_data.get('rise_horizon', 'desconocido')
                
                # Registrar alerta de subida para verificación posterior
                alert_data = {
                    'rise_horizon': rise_horizon,
                    'rise_pct': rise_pct,
                    'current_price': current_price
                }
                
                alert_id = self.forecast_system.forecast_manager.register_rise_alert(
                    forecast_id,
                    alert_data
                )
                
                # Crear posición abierta a partir de la alerta
                position = self.position_tracker.open_position_from_alert(
                    {**alert_data, 'id': alert_id, 'timestamp': datetime.now().isoformat()},
                    SYMBOL
                )
                
                # Crear mensaje de alerta
                msg = (
                    f"*🟢 ALERTA DE SUBIDA PARA {SYMBOL}*\n\n"
                    f"*Precio actual:* `{format_price(current_price)}`\n"
                    f"*Subida esperada:* `{rise_pct:.2f}%`\n"
                    f"*Horizonte:* `{rise_horizon}`\n\n"
                    f"*Análisis:*\n"
                    f"Se ha detectado una posible oportunidad de compra debido a una subida significativa "
                    f"esperada en el precio. Considere abrir posiciones largas o cerrar posiciones cortas.\n\n"
                    f"*ID de alerta:* `{alert_id}`\n"
                    f"Esta alerta será verificada automáticamente después del período indicado.\n\n"
                    f"Use el comando /forecast para ver el pronóstico completo."
                )
                
                # Enviar alerta
                send_telegram_message(msg, alert_type='rise_warning', data={
                    'price': current_price,
                    'rise_pct': rise_pct,
                    'rise_horizon': rise_horizon,
                    'alert_id': alert_id
                })
            
            # Notificar sobre alertas verificadas
            if verified_drop_alerts or verified_rise_alerts:
                verified_alerts_msg = f"*📊 ALERTAS VERIFICADAS PARA {SYMBOL}*\n\n"
                
                if verified_drop_alerts:
                    verified_alerts_msg += "*Alertas de bajada verificadas:*\n"
                    for alert in verified_drop_alerts:
                        result = "✅ Correcta" if alert["was_correct"] else "❌ Incorrecta"
                        verified_alerts_msg += f"• ID: `{alert['id']}` - {result} (Cambio real: {alert['actual_drop_pct']:.2f}%)\n"
                
                if verified_rise_alerts:
                    verified_alerts_msg += "\n*Alertas de subida verificadas:*\n"
                    for alert in verified_rise_alerts:
                        result = "✅ Correcta" if alert["was_correct"] else "❌ Incorrecta"
                        verified_alerts_msg += f"• ID: `{alert['id']}` - {result} (Cambio real: {alert['actual_rise_pct']:.2f}%)\n"
                
                # Comprobar si se han creado operaciones
                recent_operations = self.forecast_system.forecast_manager.get_recent_operations(limit=3)
                if recent_operations:
                    verified_alerts_msg += "\n*Operaciones completadas:*\n"
                    for op in recent_operations:
                        profit = op["profit_pct"]
                        profit_text = f"+{profit:.2f}%" if profit > 0 else f"{profit:.2f}%"
                        verified_alerts_msg += f"• ID: `{op['id']}` - Resultado: {profit_text}\n"
                
                # Enviar mensaje de verificación
                send_telegram_message(verified_alerts_msg, alert_type='alerts_verification')
        
        return forecast_summary
    
    def evaluate_forecast_with_current_price(self) -> Dict[str, Any]:
        """
        Evalúa el pronóstico más reciente con el precio actual.
        
        Returns:
            Resultados de la evaluación
        """
        if not self.bot:
            return {"error": "Bot no inicializado"}
        
        # Obtener precio actual
        current_price = self.bot.last_price
        if not current_price:
            return {"error": "Precio actual no disponible"}
        
        # Obtener último pronóstico
        latest_forecast = self.forecast_system.forecast_manager.get_latest_forecast()
        if not latest_forecast:
            return {"error": "No hay pronósticos para evaluar"}
        
        # Crear diccionario de precios reales
        actual_prices = {
            "actual_24h": current_price,
            "actual_3d": current_price,
            "actual_7d": current_price
        }
        
        # Evaluar pronóstico
        evaluation = self.forecast_system.evaluate_latest_forecast(actual_prices)
        
        return evaluation
    
    def generate_forecast_report(self) -> Dict[str, str]:
        """
        Genera un informe completo del sistema de pronóstico.
        
        Returns:
            Diccionario con rutas de los archivos generados
        """
        if not self.bot:
            return {"error": "Bot no inicializado"}
        
        # Obtener datos históricos de precios
        market_data = self.bot.market_data
        if not market_data or not hasattr(market_data, 'data') or 'close' not in market_data.data:
            return {"error": "Datos históricos de precios no disponibles"}
        
        # Convertir a DataFrame
        dates = []
        prices = []
        
        # Obtener fechas para los precios históricos
        # Asumimos que los datos son diarios y el último es el más reciente
        end_date = datetime.now()
        for i in range(len(market_data.data['close']) - 1, -1, -1):
            dates.insert(0, end_date - timedelta(days=len(market_data.data['close']) - 1 - i))
            prices.insert(0, market_data.data['close'][i])
        
        price_history = pd.DataFrame({
            'date': dates,
            'price': prices
        })
        
        # Generar informe
        report_files = self.forecast_system.generate_report(price_history)
        
        return report_files
    
    def get_forecast_command_response(self, args="", chat_id=None) -> str:
        """
        Genera una respuesta para el comando /forecast en Telegram.
        
        Args:
            args (str): Command arguments (symbol [length])
            chat_id (int, optional): Chat ID to send initial message
            
        Returns:
            Mensaje de respuesta
        """
        if not self.bot:
            return "❌ Bot no inicializado"
        
        try:
            # Parse arguments
            parts = args.strip().split() if args else [SYMBOL.split('-')[0]]
            symbol = parts[0].upper()
            
            # Send chat action and waiting message to indicate analysis is in progress
            if chat_id:
                from utils.telegram_utils import send_chat_action, send_telegram_message
                # Send typing action to indicate processing
                send_chat_action("typing", chat_id)
                # Send a message to inform the user that analysis is being generated
                waiting_message = f"🧠 Generando pronóstico financiero para {symbol}...\n\nEsto puede tardar unos segundos. Por favor, espera mientras nuestro asistente financiero analiza el mercado."
                send_telegram_message(waiting_message, chat_id=chat_id)
            
            # Importar el asistente financiero
            from src.financial_assistant import get_asset_forecast
            
            # Obtener pronóstico (esto también cerrará análisis antiguos)
            forecast = get_asset_forecast(symbol)
            
            # Obtener enlace a TradingView
            from src.notifier import get_tradingview_link
            chart_link = get_tradingview_link(symbol)
            
            # Componer respuesta
            response = f"{forecast}\n\n[Ver gráfico en TradingView]({chart_link})"
            
            return response
        except Exception as e:
            error_msg = str(e)
            return f"❌ Error al generar pronóstico financiero: {error_msg}\n\nPor favor, intenta de nuevo más tarde o contacta al administrador del bot."
    
    def get_forecast_accuracy_response(self) -> str:
        """
        Genera una respuesta para el comando /accuracy en Telegram.
        
        Returns:
            Mensaje de respuesta
        """
        # Obtener estadísticas del sistema
        stats = self.forecast_system.get_system_stats()
        
        # Comprobar si hay suficientes datos
        if stats["evaluation_count"] < 3:
            return "❌ No hay suficientes evaluaciones para mostrar estadísticas de precisión"
        
        # Componer mensaje de respuesta
        response = f"*📊 Precisión del Sistema de Pronóstico - {SYMBOL}*\n\n"
        
        # Añadir contadores
        response += f"*Pronósticos generados:* {stats['forecast_count']}\n"
        response += f"*Evaluaciones realizadas:* {stats['evaluation_count']}\n\n"
        
        # Añadir estadísticas de precisión
        accuracy_stats = stats["accuracy_stats"]
        
        if "short_term" in accuracy_stats:
            short_term = accuracy_stats["short_term"]
            response += (
                f"*Corto plazo (24h):*\n"
                f"• Error medio: {short_term['mean_error_pct']:.2f}%\n"
                f"• Dentro del rango: {short_term['within_range_pct']:.1f}%\n\n"
            )
        
        if "medium_term" in accuracy_stats:
            medium_term = accuracy_stats["medium_term"]
            response += (
                f"*Medio plazo (3-5 días):*\n"
                f"• Error medio: {medium_term['mean_error_pct']:.2f}%\n"
                f"• Dentro del rango: {medium_term['within_range_pct']:.1f}%\n\n"
            )
        
        if "long_term" in accuracy_stats:
            long_term = accuracy_stats["long_term"]
            response += (
                f"*Largo plazo (1-2 semanas):*\n"
                f"• Error medio: {long_term['mean_error_pct']:.2f}%\n"
                f"• Dentro del rango: {long_term['within_range_pct']:.1f}%\n\n"
            )
        
        # Añadir mensaje de mejora
        response += f"*Tendencia:* {stats['improvement_message']}\n\n"
        
        # Añadir información sobre modelos de IA
        model_info = stats["model_info"]
        
        response += "*Modelos de IA:*\n"
        for horizon, info in model_info.items():
            if horizon == "short_term":
                horizon_name = "Corto plazo"
            elif horizon == "medium_term":
                horizon_name = "Medio plazo"
            else:
                horizon_name = "Largo plazo"
            
            if info["trained"]:
                response += f"• {horizon_name}: ✅ Entrenado ({info['type']})\n"
            else:
                response += f"• {horizon_name}: ❌ No entrenado\n"
        
        return response
    
    def get_drop_alerts_response(self) -> str:
        """
        Genera una respuesta para el comando /dropalerts en Telegram.
        
        Returns:
            Mensaje de respuesta
        """
        if not self.bot:
            return "❌ Bot no inicializado"
        
        # Verificar alertas pendientes
        current_price = self.bot.last_price
        verified_alerts = self.forecast_system.forecast_manager.verify_pending_drop_alerts(current_price)
        
        # Obtener estadísticas de alertas
        stats = self.forecast_system.forecast_manager.get_drop_alerts_stats()
        
        # Obtener alertas recientes
        recent_alerts = self.forecast_system.forecast_manager.get_recent_drop_alerts(limit=5)
        
        # Componer mensaje de respuesta
        if "message" in stats:
            response = f"*🔴 Alertas de Bajada - {SYMBOL}*\n\n{stats['message']}"
            return response
        
        response = f"*🔴 Alertas de Bajada - {SYMBOL}*\n\n"
        
        # Añadir contadores
        response += f"*Total de alertas:* {stats['total_alerts']}\n"
        response += f"*Alertas verificadas:* {stats['verified_alerts']}\n"
        response += f"*Alertas correctas:* {stats['correct_alerts']}\n"
        response += f"*Precisión:* {stats['accuracy']:.1f}%\n\n"
        
        # Añadir estadísticas por horizonte
        response += "*Precisión por horizonte:*\n"
        for horizon, data in stats.get("horizons", {}).items():
            response += f"• {horizon}: {data['accuracy']:.1f}% ({data['correct']}/{data['total']})\n"
        
        response += "\n"
        
        # Añadir alertas recientes
        if recent_alerts:
            response += "*Alertas recientes:*\n"
            for alert in recent_alerts:
                # Formatear fecha
                timestamp = datetime.fromisoformat(alert["timestamp"])
                date_str = timestamp.strftime("%d/%m/%Y %H:%M")
                
                # Determinar estado
                if alert["verified"]:
                    if alert["was_correct"]:
                        status = "✅ Correcta"
                    else:
                        status = "❌ Incorrecta"
                    
                    # Añadir cambio real
                    actual_drop = alert["actual_drop_pct"]
                    if actual_drop <= -2.0:
                        drop_text = f"Bajó {abs(actual_drop):.2f}%"
                    else:
                        drop_text = f"Cambió {actual_drop:.2f}%"
                    
                    status += f" ({drop_text})"
                else:
                    status = "⏳ Pendiente"
                
                response += (
                    f"• {date_str}: {alert['drop_horizon']}, "
                    f"Bajada esperada: {abs(alert['drop_pct']):.2f}%, "
                    f"Estado: {status}\n"
                )
            
            response += "\n"
        
        # Añadir alertas verificadas en esta ejecución
        if verified_alerts:
            response += "*Alertas verificadas ahora:*\n"
            for alert in verified_alerts:
                timestamp = datetime.fromisoformat(alert["timestamp"])
                date_str = timestamp.strftime("%d/%m/%Y %H:%M")
                
                if alert["was_correct"]:
                    result = f"✅ Correcta (Bajó {abs(alert['actual_drop_pct']):.2f}%)"
                else:
                    result = f"❌ Incorrecta (Cambió {alert['actual_drop_pct']:.2f}%)"
                
                response += f"• {date_str}: {alert['drop_horizon']}, {result}\n"
            
            response += "\n"
        
        # Añadir tendencia
        response += f"*Tendencia:* La precisión de las alertas está {stats['trend']}\n\n"
        
        # Añadir nota final
        response += (
            "*Nota:* Las alertas de bajada se verifican automáticamente después del período "
            "indicado. Una alerta se considera correcta si el precio baja al menos un 2%."
        )
        
        return response
    
    def get_rise_alerts_response(self) -> str:
        """
        Genera una respuesta para el comando /risealerts en Telegram.
        
        Returns:
            Mensaje de respuesta
        """
        if not self.bot:
            return "❌ Bot no inicializado"
        
        # Verificar alertas pendientes
        current_price = self.bot.last_price
        verified_alerts = self.forecast_system.forecast_manager.verify_pending_rise_alerts(current_price)
        
        # Obtener estadísticas de alertas
        stats = self.forecast_system.forecast_manager.get_rise_alerts_stats()
        
        # Obtener alertas recientes
        recent_alerts = self.forecast_system.forecast_manager.get_recent_rise_alerts(limit=5)
        
        # Componer mensaje de respuesta
        if "message" in stats:
            response = f"*🟢 Alertas de Subida - {SYMBOL}*\n\n{stats['message']}"
            return response
        
        response = f"*🟢 Alertas de Subida - {SYMBOL}*\n\n"
        
        # Añadir contadores
        response += f"*Total de alertas:* {stats['total_alerts']}\n"
        response += f"*Alertas verificadas:* {stats['verified_alerts']}\n"
        response += f"*Alertas correctas:* {stats['correct_alerts']}\n"
        response += f"*Precisión:* {stats['accuracy']:.1f}%\n\n"
        
        # Añadir estadísticas por horizonte
        response += "*Precisión por horizonte:*\n"
        for horizon, data in stats.get("horizons", {}).items():
            response += f"• {horizon}: {data['accuracy']:.1f}% ({data['correct']}/{data['total']})\n"
        
        response += "\n"
        
        # Añadir alertas recientes
        if recent_alerts:
            response += "*Alertas recientes:*\n"
            for alert in recent_alerts:
                # Formatear fecha
                timestamp = datetime.fromisoformat(alert["timestamp"])
                date_str = timestamp.strftime("%d/%m/%Y %H:%M")
                
                # Determinar estado
                if alert["verified"]:
                    if alert["was_correct"]:
                        status = "✅ Correcta"
                    else:
                        status = "❌ Incorrecta"
                    
                    # Añadir cambio real
                    actual_rise = alert["actual_rise_pct"]
                    if actual_rise >= 2.0:
                        rise_text = f"Subió {actual_rise:.2f}%"
                    else:
                        rise_text = f"Cambió {actual_rise:.2f}%"
                    
                    status += f" ({rise_text})"
                else:
                    status = "⏳ Pendiente"
                
                response += (
                    f"• {date_str}: {alert['rise_horizon']}, "
                    f"Subida esperada: {alert['rise_pct']:.2f}%, "
                    f"Estado: {status}\n"
                )
            
            response += "\n"
        
        # Añadir alertas verificadas en esta ejecución
        if verified_alerts:
            response += "*Alertas verificadas ahora:*\n"
            for alert in verified_alerts:
                timestamp = datetime.fromisoformat(alert["timestamp"])
                date_str = timestamp.strftime("%d/%m/%Y %H:%M")
                
                if alert["was_correct"]:
                    result = f"✅ Correcta (Subió {alert['actual_rise_pct']:.2f}%)"
                else:
                    result = f"❌ Incorrecta (Cambió {alert['actual_rise_pct']:.2f}%)"
                
                response += f"• {date_str}: {alert['rise_horizon']}, {result}\n"
            
            response += "\n"
        
        # Añadir tendencia
        response += f"*Tendencia:* La precisión de las alertas está {stats['trend']}\n\n"
        
        # Añadir nota final
        response += (
            "*Nota:* Las alertas de subida se verifican automáticamente después del período "
            "indicado. Una alerta se considera correcta si el precio sube al menos un 2%."
        )
        
        return response
    
    def get_operations_response(self) -> str:
        """
        Genera una respuesta para el comando /operations en Telegram.
        
        Returns:
            Mensaje de respuesta
        """
        if not self.bot:
            return "❌ Bot no inicializado"
        
        # Obtener estadísticas de operaciones
        stats = self.forecast_system.forecast_manager.get_operations_stats()
        
        # Obtener operaciones recientes
        recent_operations = self.forecast_system.forecast_manager.get_recent_operations(limit=10)
        
        # Componer mensaje de respuesta
        if "message" in stats:
            response = f"*📈 Operaciones de Trading - {SYMBOL}*\n\n{stats['message']}"
            return response
        
        response = f"*📈 Operaciones de Trading - {SYMBOL}*\n\n"
        
        # Añadir estadísticas generales
        response += f"*Total de operaciones:* {stats['total_operations']}\n"
        response += f"*Operaciones rentables:* {stats['profitable_operations']} ({stats['win_rate']:.1f}%)\n"
        response += f"*Ganancia media:* {stats['avg_profit']:.2f}%\n"
        response += f"*Ganancia total:* {stats['total_profit']:.2f}%\n\n"
        
        # Añadir operaciones recientes
        if recent_operations:
            response += "*Operaciones recientes:*\n"
            for op in recent_operations:
                # Formatear fechas
                entry_timestamp = datetime.fromisoformat(op["entry_timestamp"])
                exit_timestamp = datetime.fromisoformat(op["exit_timestamp"])
                entry_date = entry_timestamp.strftime("%d/%m/%Y %H:%M")
                exit_date = exit_timestamp.strftime("%d/%m/%Y %H:%M")
                
                # Calcular duración
                duration_seconds = (exit_timestamp - entry_timestamp).total_seconds()
                hours, remainder = divmod(duration_seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                duration = f"{int(hours)}h {int(minutes)}m"
                
                # Formatear ganancia/pérdida
                profit = op["profit_pct"]
                if profit > 0:
                    profit_text = f"🟢 +{profit:.2f}%"
                else:
                    profit_text = f"🔴 {profit:.2f}%"
                
                # Formatear precios
                entry_price = format_price(op["entry_price"])
                exit_price = format_price(op["exit_price"])
                
                response += (
                    f"• {entry_date} → {exit_date} ({duration})\n"
                    f"  {entry_price} → {exit_price}, {profit_text}\n"
                    f"  Entrada: {op['entry_alert_type']}, Salida: {op['exit_alert_type']}\n\n"
                )
        
        # Añadir nota final
        response += (
            "*Nota:* Las operaciones se generan automáticamente cuando se confirman "
            "alertas de subida y bajada. Una operación completa consiste en una entrada "
            "(alerta verificada) y una salida (alerta opuesta verificada)."
        )
        
        return response
    
    def get_positions_response(self) -> str:
        """
        Genera una respuesta para el comando /positions en Telegram.
        
        Returns:
            Mensaje de respuesta
        """
        if not self.bot:
            return "❌ Bot no inicializado"
        
        # Obtener posiciones abiertas
        open_positions = self.position_tracker.get_open_positions()
        
        # Verificar si hay posiciones abiertas
        if not open_positions:
            return f"*📊 Posiciones Abiertas - {SYMBOL}*\n\nNo hay posiciones abiertas actualmente."
        
        # Obtener precio actual
        current_price = self.bot.last_price
        
        # Componer mensaje de respuesta
        response = f"*📊 Posiciones Abiertas - {SYMBOL}*\n\n"
        
        # Añadir contador
        response += f"*Total de posiciones abiertas:* {len(open_positions)}\n\n"
        
        # Añadir posiciones abiertas
        response += "*Posiciones actuales:*\n"
        for position in open_positions:
            # Formatear fecha
            timestamp = datetime.fromisoformat(position["entry_timestamp"])
            date_str = timestamp.strftime("%d/%m/%Y %H:%M")
            
            # Calcular duración
            now = datetime.now()
            duration_seconds = (now - timestamp).total_seconds()
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            duration = f"{int(hours)}h {int(minutes)}m"
            
            # Calcular estado actual
            entry_price = float(position["entry_price"])
            position_status = self.position_tracker.calculate_current_position_status(position, current_price)
            
            # Formatear ganancia/pérdida actual
            current_profit = position_status["current_profit_loss"]
            if current_profit > 0:
                profit_text = f"🟢 +{current_profit:.2f}%"
            else:
                profit_text = f"🔴 {current_profit:.2f}%"
            
            # Determinar tipo de posición
            if position["alert_type"] == "drop":
                position_type = "🔴 Bajada"
                expected_change = f"Bajada esperada: {abs(float(position['expected_change_pct'])):.2f}%"
            else:
                position_type = "🟢 Subida"
                expected_change = f"Subida esperada: {float(position['expected_change_pct']):.2f}%"
            
            # Formatear precios
            entry_price_str = format_price(entry_price)
            current_price_str = format_price(current_price)
            
            response += (
                f"• ID: `{position['id']}` - {position_type}\n"
                f"  Abierta: {date_str} ({duration})\n"
                f"  {expected_change}, Horizonte: {position['horizon']}\n"
                f"  Precio entrada: {entry_price_str}, Actual: {current_price_str}\n"
                f"  Estado actual: {profit_text}\n\n"
            )
        
        # Añadir nota final
        response += (
            "*Nota:* Las posiciones se cierran automáticamente después del período "
            "indicado en el horizonte temporal. El resultado se mostrará en el historial "
            "de operaciones (/operations)."
        )
        
        return response
    
    def register_telegram_commands(self, notifier):
        """
        Registra comandos de Telegram para el sistema de pronóstico.
        
        Args:
            notifier: Módulo notificador del bot
        """
        if not notifier:
            print("❌ Notificador no disponible, no se pueden registrar comandos")
            return
        
        # Comando para generar un nuevo pronóstico
        def cmd_forecast(args, bot, user_id=None, chat_id=None):
            self.set_bot(bot)
            return self.get_forecast_command_response(args, chat_id)
            
        # Comando para generar un pronóstico financiero
        def cmd_financial_forecast(args, bot, user_id=None, chat_id=None):
            self.set_bot(bot)
            try:
                # Importar el asistente financiero
                from src.financial_assistant import get_asset_forecast
                
                # Parsear argumentos
                parts = args.strip().split() if args else [self.bot.market_data.symbol.split('-')[0]]
                symbol = parts[0].upper()
                
                # Enviar mensaje inicial
                if chat_id:
                    from utils.telegram_utils import send_chat_action, send_telegram_message
                    send_chat_action("typing", chat_id)
                    waiting_message = f"🧠 Generando pronóstico financiero para {symbol}...\n\nEsto puede tardar unos segundos. Por favor, espera mientras nuestro asistente financiero analiza el mercado."
                    send_telegram_message(waiting_message, chat_id=chat_id)
                
                # Obtener pronóstico
                forecast = get_asset_forecast(symbol)
                
                # Obtener enlace a TradingView
                from src.notifier import get_tradingview_link
                chart_link = get_tradingview_link(symbol)
                
                # Componer respuesta
                response = f"{forecast}\n\n[Ver gráfico en TradingView]({chart_link})"
                
                return response
            except Exception as e:
                return f"❌ Error al generar pronóstico financiero: {str(e)}"
        
        # Comando para mostrar estadísticas de precisión
        def cmd_accuracy(args, bot):
            self.set_bot(bot)
            return self.get_forecast_accuracy_response()
        
        # Comando para mostrar alertas de bajada
        def cmd_dropalerts(args, bot):
            self.set_bot(bot)
            return self.get_drop_alerts_response()
        
        # Comando para mostrar alertas de subida
        def cmd_risealerts(args, bot):
            self.set_bot(bot)
            return self.get_rise_alerts_response()
        
        # Comando para mostrar operaciones
        def cmd_operations(args, bot):
            self.set_bot(bot)
            return self.get_operations_response()
        
        # Comando para mostrar posiciones abiertas
        def cmd_positions(args, bot):
            self.set_bot(bot)
            return self.get_positions_response()
        
        # Registrar comandos
        notifier.register_command('forecast', cmd_forecast, "Muestra el pronóstico financiero con análisis de tendencia y soporte/resistencia")
        notifier.register_command('accuracy', cmd_accuracy, "Muestra estadísticas de precisión del sistema de pronóstico")
        notifier.register_command('dropalerts', cmd_dropalerts, "Muestra alertas de bajada y verifica las pendientes")
        notifier.register_command('risealerts', cmd_risealerts, "Muestra alertas de subida y verifica las pendientes")
        notifier.register_command('operations', cmd_operations, "Muestra operaciones completadas basadas en alertas verificadas")
        notifier.register_command('positions', cmd_positions, "Muestra posiciones abiertas actualmente")
        
        print("✅ Comandos de pronóstico registrados en Telegram")
