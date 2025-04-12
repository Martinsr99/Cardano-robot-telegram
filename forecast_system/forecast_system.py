"""
Forecast System - Sistema principal de pronóstico con retroalimentación
"""

import os
import sys
import json
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Importar componentes del sistema
from forecast_system.forecast_manager import ForecastManager
from forecast_system.visualization.forecast_visualizer import ForecastVisualizer
from forecast_system.models.forecast_model import ForecastModel

class ForecastSystem:
    """
    Sistema principal de pronóstico con retroalimentación.
    """
    def __init__(self, data_dir: str = "forecast_system/data"):
        """
        Inicializa el sistema de pronóstico.
        
        Args:
            data_dir: Directorio base para datos
        """
        self.data_dir = data_dir
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Inicializar componentes
        self.forecast_manager = ForecastManager(data_dir=data_dir)
        self.visualizer = ForecastVisualizer()
        self.model = ForecastModel()
        
        # Inicializar estado
        self.last_forecast_id = None
        self.last_evaluation = None
    
    def register_forecast(self, forecast_data: Dict[str, Any]) -> str:
        """
        Registra un nuevo pronóstico en el sistema.
        
        Args:
            forecast_data: Datos del pronóstico
            
        Returns:
            ID del pronóstico
        """
        # Aplicar mejora de IA si hay modelos entrenados
        model_info = self.model.get_model_info()
        has_trained_models = any(info["trained"] for info in model_info.values())
        
        if has_trained_models:
            # Mejorar pronóstico con IA
            improved_forecast = self.model.improve_forecast(forecast_data)
            forecast_id = self.forecast_manager.add_forecast(improved_forecast)
        else:
            # Registrar pronóstico original
            forecast_id = self.forecast_manager.add_forecast(forecast_data)
        
        # Guardar ID del último pronóstico
        self.last_forecast_id = forecast_id
        
        return forecast_id
    
    def evaluate_latest_forecast(self, actual_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Evalúa el pronóstico más reciente.
        
        Args:
            actual_prices: Diccionario con precios reales para diferentes horizontes temporales
            
        Returns:
            Resultados de la evaluación
        """
        # Obtener último pronóstico
        latest_forecast = self.forecast_manager.get_latest_forecast()
        if not latest_forecast:
            raise ValueError("No hay pronósticos para evaluar")
        
        # Evaluar pronóstico
        evaluation = self.forecast_manager.evaluate_forecast(
            latest_forecast["id"], actual_prices
        )
        
        # Guardar última evaluación
        self.last_evaluation = evaluation
        
        return evaluation
    
    def evaluate_forecast_by_id(self, forecast_id: str, actual_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Evalúa un pronóstico específico.
        
        Args:
            forecast_id: ID del pronóstico a evaluar
            actual_prices: Diccionario con precios reales para diferentes horizontes temporales
            
        Returns:
            Resultados de la evaluación
        """
        # Evaluar pronóstico
        evaluation = self.forecast_manager.evaluate_forecast(forecast_id, actual_prices)
        
        # Guardar última evaluación
        self.last_evaluation = evaluation
        
        return evaluation
    
    def train_model(self) -> Dict[str, Any]:
        """
        Entrena el modelo de IA con los datos históricos.
        
        Returns:
            Resultados del entrenamiento
        """
        # Obtener todos los pronósticos y evaluaciones
        forecasts = self.forecast_manager.forecasts
        evaluations = self.forecast_manager.evaluations
        
        # Entrenar modelo
        results = self.model.train(forecasts, evaluations)
        
        return results
    
    def generate_report(self, price_history: pd.DataFrame, future_prices: Optional[pd.DataFrame] = None) -> Dict[str, str]:
        """
        Genera un informe completo del sistema de pronóstico.
        
        Args:
            price_history: DataFrame con historial de precios
            future_prices: DataFrame con precios futuros si están disponibles
            
        Returns:
            Diccionario con rutas de los archivos generados
        """
        report_files = {}
        
        # Generar gráfico de precisión a lo largo del tiempo
        if len(self.forecast_manager.evaluations) >= 3:
            accuracy_path = self.visualizer.plot_accuracy_over_time(
                self.forecast_manager.evaluations
            )
            report_files["accuracy_over_time"] = accuracy_path
        
        # Generar gráfico de distribución de errores
        if len(self.forecast_manager.evaluations) >= 3:
            distribution_path = self.visualizer.plot_accuracy_distribution(
                self.forecast_manager.evaluations
            )
            report_files["error_distribution"] = distribution_path
        
        # Generar informe del último pronóstico si hay evaluación
        if self.last_forecast_id and self.last_evaluation:
            forecast = self.forecast_manager.get_forecast_by_id(self.last_forecast_id)
            if forecast:
                forecast_report = self.visualizer.generate_forecast_report(
                    forecast, self.last_evaluation, price_history, future_prices
                )
                report_files.update(forecast_report)
        
        return report_files
    
    def check_last_forecast(self, current_price: float) -> Dict[str, Any]:
        """
        Comprueba el último pronóstico contra el precio actual.
        
        Args:
            current_price: Precio actual
            
        Returns:
            Resultados de la comprobación
        """
        # Obtener último pronóstico
        latest_forecast = self.forecast_manager.get_latest_forecast()
        if not latest_forecast:
            return {"message": "No hay pronósticos para comprobar"}
        
        forecast_data = latest_forecast["data"]
        forecast_timestamp = datetime.fromisoformat(latest_forecast["timestamp"])
        current_timestamp = datetime.now()
        
        # Calcular tiempo transcurrido
        elapsed_time = current_timestamp - forecast_timestamp
        elapsed_days = elapsed_time.total_seconds() / (24 * 3600)
        
        # Determinar qué horizonte temporal comprobar
        if elapsed_days < 1.5:  # Menos de 1.5 días -> corto plazo
            horizon = "short_term"
            horizon_name = "corto plazo (24h)"
        elif elapsed_days < 5:  # Menos de 5 días -> medio plazo
            horizon = "medium_term"
            horizon_name = "medio plazo (3-5 días)"
        elif elapsed_days < 14:  # Menos de 14 días -> largo plazo
            horizon = "long_term"
            horizon_name = "largo plazo (1-2 semanas)"
        else:
            return {"message": "El pronóstico es demasiado antiguo para comprobar"}
        
        # Comprobar si el horizonte existe en el pronóstico
        if horizon not in forecast_data:
            return {"message": f"No hay datos de {horizon_name} en el pronóstico"}
        
        # Extraer datos del pronóstico
        min_price = forecast_data[horizon]["min"]
        max_price = forecast_data[horizon]["max"]
        likely_price = forecast_data[horizon]["likely"]
        
        # Comprobar si el precio actual está dentro del rango
        within_range = min_price <= current_price <= max_price
        
        # Calcular error respecto al precio más probable
        error = abs(current_price - likely_price)
        error_pct = error / likely_price * 100
        
        # Preparar resultados
        results = {
            "forecast_id": latest_forecast["id"],
            "forecast_timestamp": forecast_timestamp.isoformat(),
            "elapsed_days": elapsed_days,
            "horizon": horizon,
            "horizon_name": horizon_name,
            "current_price": current_price,
            "predicted_min": min_price,
            "predicted_max": max_price,
            "predicted_likely": likely_price,
            "within_range": within_range,
            "error": error,
            "error_pct": error_pct
        }
        
        # Añadir mensaje descriptivo
        if within_range:
            results["message"] = (
                f"✅ El precio actual (${current_price:.4f}) está dentro del rango "
                f"pronosticado para {horizon_name}: ${min_price:.4f} - ${max_price:.4f}"
            )
        else:
            results["message"] = (
                f"❌ El precio actual (${current_price:.4f}) está fuera del rango "
                f"pronosticado para {horizon_name}: ${min_price:.4f} - ${max_price:.4f}"
            )
        
        # Añadir mensaje sobre precisión
        results["accuracy_message"] = (
            f"Error respecto al precio más probable (${likely_price:.4f}): "
            f"{error_pct:.2f}%"
        )
        
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del sistema de pronóstico.
        
        Returns:
            Estadísticas del sistema
        """
        # Obtener estadísticas de precisión
        accuracy_stats = self.forecast_manager.get_forecast_accuracy_stats()
        
        # Obtener información del modelo
        model_info = self.model.get_model_info()
        
        # Contar pronósticos y evaluaciones
        forecast_count = len(self.forecast_manager.forecasts)
        evaluation_count = len(self.forecast_manager.evaluations)
        
        # Calcular tasa de mejora si hay suficientes evaluaciones
        improvement_rate = None
        if "trend" in accuracy_stats and "overall_error_change" in accuracy_stats["trend"]:
            error_change = accuracy_stats["trend"]["overall_error_change"]
            if error_change < 0:
                improvement_rate = abs(error_change)
                improvement_message = f"El sistema está mejorando (reducción de error: {improvement_rate:.2f}%)"
            else:
                improvement_rate = error_change
                improvement_message = f"El sistema no está mejorando (aumento de error: {improvement_rate:.2f}%)"
        else:
            improvement_message = "No hay suficientes datos para calcular la tasa de mejora"
        
        # Preparar estadísticas
        stats = {
            "forecast_count": forecast_count,
            "evaluation_count": evaluation_count,
            "accuracy_stats": accuracy_stats,
            "model_info": model_info,
            "improvement_rate": improvement_rate,
            "improvement_message": improvement_message,
            "last_forecast_id": self.last_forecast_id,
            "has_last_evaluation": self.last_evaluation is not None
        }
        
        return stats
    
    def get_forecast_summary(self, forecast_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene un resumen de un pronóstico específico o del último.
        
        Args:
            forecast_id: ID del pronóstico (opcional, si no se proporciona se usa el último)
            
        Returns:
            Resumen del pronóstico
        """
        # Determinar qué pronóstico usar
        if forecast_id:
            forecast = self.forecast_manager.get_forecast_by_id(forecast_id)
        else:
            forecast = self.forecast_manager.get_latest_forecast()
        
        if not forecast:
            return {"message": "No hay pronóstico disponible"}
        
        # Extraer datos del pronóstico
        forecast_data = forecast["data"]
        forecast_timestamp = datetime.fromisoformat(forecast["timestamp"])
        
        # Preparar resumen
        summary = {
            "id": forecast["id"],
            "timestamp": forecast_timestamp.isoformat(),
            "formatted_date": forecast_timestamp.strftime("%Y-%m-%d %H:%M"),
            "horizons": {}
        }
        
        # Añadir datos para cada horizonte temporal
        for horizon in ["short_term", "medium_term", "long_term"]:
            if horizon in forecast_data:
                horizon_data = forecast_data[horizon]
                
                # Determinar nombre del horizonte
                if horizon == "short_term":
                    horizon_name = "Corto plazo (24h)"
                    target_date = forecast_timestamp + timedelta(days=1)
                elif horizon == "medium_term":
                    horizon_name = "Medio plazo (3-5 días)"
                    target_date = forecast_timestamp + timedelta(days=4)
                else:
                    horizon_name = "Largo plazo (1-2 semanas)"
                    target_date = forecast_timestamp + timedelta(days=10)
                
                # Añadir datos al resumen
                summary["horizons"][horizon] = {
                    "name": horizon_name,
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "min": horizon_data["min"],
                    "max": horizon_data["max"],
                    "likely": horizon_data["likely"],
                    "ai_adjusted": horizon_data.get("ai_adjusted", False)
                }
        
        # Añadir metadatos adicionales
        summary["ai_improved"] = forecast_data.get("ai_improved", False)
        summary["confidence"] = forecast_data.get("confidence", 0)
        
        # Añadir datos de tendencia si están disponibles
        if "trend_direction" in forecast_data:
            summary["trend"] = {
                "direction": forecast_data["trend_direction"],
                "strength": forecast_data.get("trend_strength", 0)
            }
        
        # Añadir niveles de soporte y resistencia si están disponibles
        if "support" in forecast_data and "resistance" in forecast_data:
            summary["levels"] = {
                "support": forecast_data["support"],
                "resistance": forecast_data["resistance"]
            }
        
        return summary
