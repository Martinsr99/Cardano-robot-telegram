"""
Forecast Manager - Gestiona el almacenamiento y recuperación de pronósticos
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

class ForecastManager:
    """
    Clase para gestionar pronósticos, incluyendo almacenamiento, recuperación y evaluación.
    """
    def __init__(self, data_dir: str = "forecast_system/data"):
        """
        Inicializa el gestor de pronósticos.
        
        Args:
            data_dir: Directorio donde se almacenarán los pronósticos
        """
        self.data_dir = data_dir
        self.forecasts_file = os.path.join(data_dir, "forecasts_history.json")
        self.evaluations_file = os.path.join(data_dir, "forecast_evaluations.json")
        self.drop_alerts_file = os.path.join(data_dir, "drop_alerts.json")
        self.rise_alerts_file = os.path.join(data_dir, "rise_alerts.json")
        self.operations_file = os.path.join(data_dir, "forecast_operations.json")
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Cargar pronósticos existentes
        self.forecasts = self._load_forecasts()
        self.evaluations = self._load_evaluations()
        self.drop_alerts = self._load_drop_alerts()
        self.rise_alerts = self._load_rise_alerts()
        self.operations = self._load_operations()
    
    def _load_forecasts(self) -> List[Dict[str, Any]]:
        """Carga los pronósticos históricos desde el archivo"""
        if os.path.exists(self.forecasts_file):
            try:
                with open(self.forecasts_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar pronósticos de {self.forecasts_file}")
                return []
        return []
    
    def _load_evaluations(self) -> List[Dict[str, Any]]:
        """Carga las evaluaciones de pronósticos desde el archivo"""
        if os.path.exists(self.evaluations_file):
            try:
                with open(self.evaluations_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar evaluaciones de {self.evaluations_file}")
                return []
        return []
    
    def _save_forecasts(self):
        """Guarda los pronósticos en el archivo"""
        with open(self.forecasts_file, 'w') as f:
            json.dump(self.forecasts, f, indent=2)
    
    def _save_evaluations(self):
        """Guarda las evaluaciones en el archivo"""
        with open(self.evaluations_file, 'w') as f:
            json.dump(self.evaluations, f, indent=2)
    
    def add_forecast(self, forecast_data: Dict[str, Any]) -> str:
        """
        Añade un nuevo pronóstico al historial.
        
        Args:
            forecast_data: Datos del pronóstico
            
        Returns:
            ID del pronóstico
        """
        # Generar ID único para el pronóstico
        forecast_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Añadir timestamp
        forecast_entry = {
            "id": forecast_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": forecast_data
        }
        
        # Añadir a la lista de pronósticos
        self.forecasts.append(forecast_entry)
        
        # Guardar
        self._save_forecasts()
        
        return forecast_id
    
    def get_latest_forecast(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el pronóstico más reciente.
        
        Returns:
            Pronóstico más reciente o None si no hay pronósticos
        """
        if not self.forecasts:
            return None
        
        # Ordenar por timestamp y obtener el más reciente
        sorted_forecasts = sorted(self.forecasts, key=lambda x: x["timestamp"], reverse=True)
        return sorted_forecasts[0]
    
    def get_forecast_by_id(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un pronóstico por su ID.
        
        Args:
            forecast_id: ID del pronóstico
            
        Returns:
            Pronóstico o None si no se encuentra
        """
        for forecast in self.forecasts:
            if forecast["id"] == forecast_id:
                return forecast
        return None
    
    def evaluate_forecast(self, forecast_id: str, actual_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Evalúa un pronóstico comparándolo con los precios reales.
        
        Args:
            forecast_id: ID del pronóstico a evaluar
            actual_prices: Diccionario con precios reales para diferentes horizontes temporales
            
        Returns:
            Resultados de la evaluación
        """
        forecast = self.get_forecast_by_id(forecast_id)
        if not forecast:
            raise ValueError(f"Pronóstico con ID {forecast_id} no encontrado")
        
        forecast_data = forecast["data"]
        
        # Calcular errores para cada horizonte temporal
        evaluation = {
            "forecast_id": forecast_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "errors": {}
        }
        
        # Evaluar precio más probable a 24h
        if "short_term" in forecast_data and "actual_24h" in actual_prices:
            predicted = forecast_data["short_term"]["likely"]
            actual = actual_prices["actual_24h"]
            error_pct = abs(predicted - actual) / actual * 100
            evaluation["errors"]["short_term"] = {
                "predicted": predicted,
                "actual": actual,
                "error_pct": error_pct,
                "within_range": (
                    forecast_data["short_term"]["min"] <= actual <= forecast_data["short_term"]["max"]
                )
            }
        
        # Evaluar precio a medio plazo (3-5 días)
        if "medium_term" in forecast_data and "actual_3d" in actual_prices:
            predicted = forecast_data["medium_term"]["likely"]
            actual = actual_prices["actual_3d"]
            error_pct = abs(predicted - actual) / actual * 100
            evaluation["errors"]["medium_term"] = {
                "predicted": predicted,
                "actual": actual,
                "error_pct": error_pct,
                "within_range": (
                    forecast_data["medium_term"]["min"] <= actual <= forecast_data["medium_term"]["max"]
                )
            }
        
        # Evaluar precio a largo plazo (1-2 semanas)
        if "long_term" in forecast_data and "actual_7d" in actual_prices:
            predicted = forecast_data["long_term"]["likely"]
            actual = actual_prices["actual_7d"]
            error_pct = abs(predicted - actual) / actual * 100
            evaluation["errors"]["long_term"] = {
                "predicted": predicted,
                "actual": actual,
                "error_pct": error_pct,
                "within_range": (
                    forecast_data["long_term"]["min"] <= actual <= forecast_data["long_term"]["max"]
                )
            }
        
        # Calcular precisión general
        if evaluation["errors"]:
            error_values = [e["error_pct"] for e in evaluation["errors"].values()]
            within_range_values = [e["within_range"] for e in evaluation["errors"].values()]
            
            evaluation["overall"] = {
                "mean_error_pct": np.mean(error_values),
                "within_range_pct": sum(within_range_values) / len(within_range_values) * 100
            }
        
        # Guardar evaluación
        self.evaluations.append(evaluation)
        self._save_evaluations()
        
        return evaluation
    
    def get_forecast_accuracy_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de precisión de los pronósticos.
        
        Returns:
            Estadísticas de precisión
        """
        if not self.evaluations:
            return {"message": "No hay evaluaciones disponibles"}
        
        # Convertir a DataFrame para análisis
        df = pd.DataFrame([
            {
                "timestamp": e["timestamp"],
                "forecast_id": e["forecast_id"],
                "short_term_error": e["errors"].get("short_term", {}).get("error_pct", np.nan),
                "medium_term_error": e["errors"].get("medium_term", {}).get("error_pct", np.nan),
                "long_term_error": e["errors"].get("long_term", {}).get("error_pct", np.nan),
                "short_term_within_range": e["errors"].get("short_term", {}).get("within_range", False),
                "medium_term_within_range": e["errors"].get("medium_term", {}).get("within_range", False),
                "long_term_within_range": e["errors"].get("long_term", {}).get("within_range", False),
                "overall_error": e.get("overall", {}).get("mean_error_pct", np.nan),
                "overall_within_range": e.get("overall", {}).get("within_range_pct", np.nan)
            }
            for e in self.evaluations
        ])
        
        # Calcular estadísticas
        stats = {
            "count": len(df),
            "short_term": {
                "mean_error_pct": df["short_term_error"].mean(),
                "within_range_pct": df["short_term_within_range"].mean() * 100
            },
            "medium_term": {
                "mean_error_pct": df["medium_term_error"].mean(),
                "within_range_pct": df["medium_term_within_range"].mean() * 100
            },
            "long_term": {
                "mean_error_pct": df["long_term_error"].mean(),
                "within_range_pct": df["long_term_within_range"].mean() * 100
            },
            "overall": {
                "mean_error_pct": df["overall_error"].mean(),
                "within_range_pct": df["overall_within_range"].mean()
            },
            "trend": self._calculate_accuracy_trend(df)
        }
        
        return stats
    
    def _calculate_accuracy_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula la tendencia de precisión a lo largo del tiempo.
        
        Args:
            df: DataFrame con evaluaciones
            
        Returns:
            Tendencia de precisión
        """
        # Convertir timestamp a datetime
        df["datetime"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("datetime")
        
        # Calcular tendencia de error (últimos 10 vs primeros 10)
        if len(df) >= 20:
            first_10 = df.head(10)
            last_10 = df.tail(10)
            
            trend = {
                "short_term_error_change": last_10["short_term_error"].mean() - first_10["short_term_error"].mean(),
                "medium_term_error_change": last_10["medium_term_error"].mean() - first_10["medium_term_error"].mean(),
                "long_term_error_change": last_10["long_term_error"].mean() - first_10["long_term_error"].mean(),
                "overall_error_change": last_10["overall_error"].mean() - first_10["overall_error"].mean(),
                "improving": last_10["overall_error"].mean() < first_10["overall_error"].mean()
            }
        else:
            trend = {"message": "No hay suficientes datos para calcular tendencia"}
        
        return trend
    
    def get_recent_evaluations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las evaluaciones más recientes.
        
        Args:
            limit: Número máximo de evaluaciones a devolver
            
        Returns:
            Lista de evaluaciones
        """
        sorted_evals = sorted(self.evaluations, key=lambda x: x["timestamp"], reverse=True)
        return sorted_evals[:limit]
    
    def _load_drop_alerts(self) -> List[Dict[str, Any]]:
        """Carga las alertas de bajada desde el archivo"""
        if os.path.exists(self.drop_alerts_file):
            try:
                with open(self.drop_alerts_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar alertas de bajada de {self.drop_alerts_file}")
                return []
        return []
    
    def _save_drop_alerts(self):
        """Guarda las alertas de bajada en el archivo"""
        with open(self.drop_alerts_file, 'w') as f:
            json.dump(self.drop_alerts, f, indent=2)
    
    def register_drop_alert(self, forecast_id: str, drop_data: Dict[str, Any]) -> str:
        """
        Registra una alerta de bajada para su posterior verificación.
        
        Args:
            forecast_id: ID del pronóstico que generó la alerta
            drop_data: Datos de la alerta de bajada
            
        Returns:
            ID de la alerta
        """
        # Generar ID único para la alerta
        alert_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Crear entrada de alerta
        alert_entry = {
            "id": alert_id,
            "forecast_id": forecast_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "drop_horizon": drop_data.get("drop_horizon", "unknown"),
            "drop_pct": drop_data.get("drop_pct", 0),
            "current_price": drop_data.get("current_price", 0),
            "verified": False,
            "verification_timestamp": None,
            "was_correct": None,
            "actual_drop_pct": None,
            "verification_price": None
        }
        
        # Añadir a la lista de alertas
        self.drop_alerts.append(alert_entry)
        
        # Guardar
        self._save_drop_alerts()
        
        return alert_id
    
    def verify_drop_alert(self, alert_id: str, current_price: float) -> Dict[str, Any]:
        """
        Verifica si una alerta de bajada fue correcta.
        
        Args:
            alert_id: ID de la alerta a verificar
            current_price: Precio actual para la verificación
            
        Returns:
            Resultados de la verificación
        """
        # Buscar la alerta
        alert = None
        for a in self.drop_alerts:
            if a["id"] == alert_id:
                alert = a
                break
        
        if not alert:
            raise ValueError(f"Alerta con ID {alert_id} no encontrada")
        
        # Si ya está verificada, devolver los resultados
        if alert["verified"]:
            return alert
        
        # Calcular el cambio de precio
        initial_price = alert["current_price"]
        actual_drop_pct = (current_price - initial_price) / initial_price * 100
        
        # Determinar si la alerta fue correcta
        # Una alerta de bajada es correcta si el precio bajó al menos un 2%
        was_correct = actual_drop_pct <= -2.0
        
        # Actualizar la alerta
        alert["verified"] = True
        alert["verification_timestamp"] = datetime.datetime.now().isoformat()
        alert["was_correct"] = was_correct
        alert["actual_drop_pct"] = actual_drop_pct
        alert["verification_price"] = current_price
        
        # Guardar
        self._save_drop_alerts()
        
        return alert
    
    def verify_pending_drop_alerts(self, current_price: float) -> List[Dict[str, Any]]:
        """
        Verifica todas las alertas de bajada pendientes según su horizonte temporal.
        
        Args:
            current_price: Precio actual para la verificación
            
        Returns:
            Lista de alertas verificadas
        """
        verified_alerts = []
        now = datetime.datetime.now()
        
        for alert in self.drop_alerts:
            # Omitir alertas ya verificadas
            if alert["verified"]:
                continue
            
            # Obtener timestamp de la alerta
            alert_timestamp = datetime.datetime.fromisoformat(alert["timestamp"])
            
            # Determinar si ha pasado suficiente tiempo según el horizonte
            should_verify = False
            
            if alert["drop_horizon"] == "corto plazo (24h)":
                # Verificar después de 24-30 horas
                hours_passed = (now - alert_timestamp).total_seconds() / 3600
                should_verify = hours_passed >= 24
            
            elif alert["drop_horizon"] == "medio plazo (3-5 días)":
                # Verificar después de 4 días
                days_passed = (now - alert_timestamp).days
                should_verify = days_passed >= 4
            
            elif alert["drop_horizon"] == "largo plazo (1-2 semanas)":
                # Verificar después de 10 días
                days_passed = (now - alert_timestamp).days
                should_verify = days_passed >= 10
            
            # Verificar la alerta si es necesario
            if should_verify:
                verified_alert = self.verify_drop_alert(alert["id"], current_price)
                verified_alerts.append(verified_alert)
        
        return verified_alerts
    
    def get_drop_alerts_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de precisión de las alertas de bajada.
        
        Returns:
            Estadísticas de precisión
        """
        if not self.drop_alerts:
            return {"message": "No hay alertas de bajada registradas"}
        
        # Filtrar alertas verificadas
        verified_alerts = [a for a in self.drop_alerts if a["verified"]]
        
        if not verified_alerts:
            return {"message": "No hay alertas de bajada verificadas"}
        
        # Calcular estadísticas generales
        total_verified = len(verified_alerts)
        correct_alerts = [a for a in verified_alerts if a["was_correct"]]
        total_correct = len(correct_alerts)
        accuracy = total_correct / total_verified * 100 if total_verified > 0 else 0
        
        # Calcular estadísticas por horizonte
        horizons = {}
        for horizon in ["corto plazo (24h)", "medio plazo (3-5 días)", "largo plazo (1-2 semanas)"]:
            horizon_alerts = [a for a in verified_alerts if a["drop_horizon"] == horizon]
            if horizon_alerts:
                correct = len([a for a in horizon_alerts if a["was_correct"]])
                horizons[horizon] = {
                    "total": len(horizon_alerts),
                    "correct": correct,
                    "accuracy": correct / len(horizon_alerts) * 100,
                    "avg_predicted_drop": np.mean([a["drop_pct"] for a in horizon_alerts]),
                    "avg_actual_drop": np.mean([a["actual_drop_pct"] for a in horizon_alerts])
                }
        
        # Calcular tendencia de precisión
        trend = "mejorando" if accuracy >= 60 else "estable" if accuracy >= 40 else "empeorando"
        
        return {
            "total_alerts": len(self.drop_alerts),
            "verified_alerts": total_verified,
            "correct_alerts": total_correct,
            "accuracy": accuracy,
            "horizons": horizons,
            "trend": trend
        }
    
    def get_recent_drop_alerts(self, limit: int = 10, verified_only: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene las alertas de bajada más recientes.
        
        Args:
            limit: Número máximo de alertas a devolver
            verified_only: Si es True, solo devuelve alertas verificadas
            
        Returns:
            Lista de alertas
        """
        if verified_only:
            alerts = [a for a in self.drop_alerts if a["verified"]]
        else:
            alerts = self.drop_alerts
        
        sorted_alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)
        return sorted_alerts[:limit]
    
    def _load_rise_alerts(self) -> List[Dict[str, Any]]:
        """Carga las alertas de subida desde el archivo"""
        if os.path.exists(self.rise_alerts_file):
            try:
                with open(self.rise_alerts_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar alertas de subida de {self.rise_alerts_file}")
                return []
        return []
    
    def _save_rise_alerts(self):
        """Guarda las alertas de subida en el archivo"""
        with open(self.rise_alerts_file, 'w') as f:
            json.dump(self.rise_alerts, f, indent=2)
    
    def register_rise_alert(self, forecast_id: str, rise_data: Dict[str, Any]) -> str:
        """
        Registra una alerta de subida para su posterior verificación.
        
        Args:
            forecast_id: ID del pronóstico que generó la alerta
            rise_data: Datos de la alerta de subida
            
        Returns:
            ID de la alerta
        """
        # Generar ID único para la alerta
        alert_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Crear entrada de alerta
        alert_entry = {
            "id": alert_id,
            "forecast_id": forecast_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "rise_horizon": rise_data.get("rise_horizon", "unknown"),
            "rise_pct": rise_data.get("rise_pct", 0),
            "current_price": rise_data.get("current_price", 0),
            "verified": False,
            "verification_timestamp": None,
            "was_correct": None,
            "actual_rise_pct": None,
            "verification_price": None,
            "operation_id": None  # ID de la operación asociada (si existe)
        }
        
        # Añadir a la lista de alertas
        self.rise_alerts.append(alert_entry)
        
        # Guardar
        self._save_rise_alerts()
        
        # Comprobar si hay alertas de bajada verificadas para crear una operación
        self._check_and_create_operation(alert_entry, "rise")
        
        return alert_id
    
    def verify_rise_alert(self, alert_id: str, current_price: float) -> Dict[str, Any]:
        """
        Verifica si una alerta de subida fue correcta.
        
        Args:
            alert_id: ID de la alerta a verificar
            current_price: Precio actual para la verificación
            
        Returns:
            Resultados de la verificación
        """
        # Buscar la alerta
        alert = None
        for a in self.rise_alerts:
            if a["id"] == alert_id:
                alert = a
                break
        
        if not alert:
            raise ValueError(f"Alerta con ID {alert_id} no encontrada")
        
        # Si ya está verificada, devolver los resultados
        if alert["verified"]:
            return alert
        
        # Calcular el cambio de precio
        initial_price = alert["current_price"]
        actual_rise_pct = (current_price - initial_price) / initial_price * 100
        
        # Determinar si la alerta fue correcta
        # Una alerta de subida es correcta si el precio subió al menos un 2%
        was_correct = actual_rise_pct >= 2.0
        
        # Actualizar la alerta
        alert["verified"] = True
        alert["verification_timestamp"] = datetime.datetime.now().isoformat()
        alert["was_correct"] = was_correct
        alert["actual_rise_pct"] = actual_rise_pct
        alert["verification_price"] = current_price
        
        # Guardar
        self._save_rise_alerts()
        
        # Comprobar si hay alertas de bajada verificadas para crear una operación
        if was_correct:
            self._check_and_create_operation(alert, "rise")
        
        return alert
    
    def verify_pending_rise_alerts(self, current_price: float) -> List[Dict[str, Any]]:
        """
        Verifica todas las alertas de subida pendientes según su horizonte temporal.
        
        Args:
            current_price: Precio actual para la verificación
            
        Returns:
            Lista de alertas verificadas
        """
        verified_alerts = []
        now = datetime.datetime.now()
        
        for alert in self.rise_alerts:
            # Omitir alertas ya verificadas
            if alert["verified"]:
                continue
            
            # Obtener timestamp de la alerta
            alert_timestamp = datetime.datetime.fromisoformat(alert["timestamp"])
            
            # Determinar si ha pasado suficiente tiempo según el horizonte
            should_verify = False
            
            if alert["rise_horizon"] == "corto plazo (24h)":
                # Verificar después de 24-30 horas
                hours_passed = (now - alert_timestamp).total_seconds() / 3600
                should_verify = hours_passed >= 24
            
            elif alert["rise_horizon"] == "medio plazo (3-5 días)":
                # Verificar después de 4 días
                days_passed = (now - alert_timestamp).days
                should_verify = days_passed >= 4
            
            elif alert["rise_horizon"] == "largo plazo (1-2 semanas)":
                # Verificar después de 10 días
                days_passed = (now - alert_timestamp).days
                should_verify = days_passed >= 10
            
            # Verificar la alerta si es necesario
            if should_verify:
                verified_alert = self.verify_rise_alert(alert["id"], current_price)
                verified_alerts.append(verified_alert)
        
        return verified_alerts
    
    def get_rise_alerts_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de precisión de las alertas de subida.
        
        Returns:
            Estadísticas de precisión
        """
        if not self.rise_alerts:
            return {"message": "No hay alertas de subida registradas"}
        
        # Filtrar alertas verificadas
        verified_alerts = [a for a in self.rise_alerts if a["verified"]]
        
        if not verified_alerts:
            return {"message": "No hay alertas de subida verificadas"}
        
        # Calcular estadísticas generales
        total_verified = len(verified_alerts)
        correct_alerts = [a for a in verified_alerts if a["was_correct"]]
        total_correct = len(correct_alerts)
        accuracy = total_correct / total_verified * 100 if total_verified > 0 else 0
        
        # Calcular estadísticas por horizonte
        horizons = {}
        for horizon in ["corto plazo (24h)", "medio plazo (3-5 días)", "largo plazo (1-2 semanas)"]:
            horizon_alerts = [a for a in verified_alerts if a["rise_horizon"] == horizon]
            if horizon_alerts:
                correct = len([a for a in horizon_alerts if a["was_correct"]])
                horizons[horizon] = {
                    "total": len(horizon_alerts),
                    "correct": correct,
                    "accuracy": correct / len(horizon_alerts) * 100,
                    "avg_predicted_rise": np.mean([a["rise_pct"] for a in horizon_alerts]),
                    "avg_actual_rise": np.mean([a["actual_rise_pct"] for a in horizon_alerts])
                }
        
        # Calcular tendencia de precisión
        trend = "mejorando" if accuracy >= 60 else "estable" if accuracy >= 40 else "empeorando"
        
        return {
            "total_alerts": len(self.rise_alerts),
            "verified_alerts": total_verified,
            "correct_alerts": total_correct,
            "accuracy": accuracy,
            "horizons": horizons,
            "trend": trend
        }
    
    def get_recent_rise_alerts(self, limit: int = 10, verified_only: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene las alertas de subida más recientes.
        
        Args:
            limit: Número máximo de alertas a devolver
            verified_only: Si es True, solo devuelve alertas verificadas
            
        Returns:
            Lista de alertas
        """
        if verified_only:
            alerts = [a for a in self.rise_alerts if a["verified"]]
        else:
            alerts = self.rise_alerts
        
        sorted_alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)
        return sorted_alerts[:limit]
    
    def _load_operations(self) -> List[Dict[str, Any]]:
        """Carga las operaciones desde el archivo"""
        if os.path.exists(self.operations_file):
            try:
                with open(self.operations_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error al cargar operaciones de {self.operations_file}")
                return []
        return []
    
    def _save_operations(self):
        """Guarda las operaciones en el archivo"""
        with open(self.operations_file, 'w') as f:
            json.dump(self.operations, f, indent=2)
    
    def _check_and_create_operation(self, alert: Dict[str, Any], alert_type: str) -> Optional[str]:
        """
        Comprueba si se puede crear una operación completa con esta alerta.
        Una operación completa consiste en una alerta de subida y una de bajada verificadas.
        
        Args:
            alert: Alerta que podría formar parte de una operación
            alert_type: Tipo de alerta ('rise' o 'drop')
            
        Returns:
            ID de la operación creada o None
        """
        # Si la alerta ya está asociada a una operación, no hacer nada
        if alert.get("operation_id"):
            return None
        
        # Buscar alertas del tipo opuesto que estén verificadas y correctas
        if alert_type == "rise":
            opposite_alerts = [a for a in self.drop_alerts if a["verified"] and a["was_correct"] and not a.get("operation_id")]
        else:  # drop
            opposite_alerts = [a for a in self.rise_alerts if a["verified"] and a["was_correct"] and not a.get("operation_id")]
        
        if not opposite_alerts:
            return None
        
        # Ordenar por timestamp (más reciente primero)
        opposite_alerts = sorted(opposite_alerts, key=lambda x: x["timestamp"], reverse=True)
        opposite_alert = opposite_alerts[0]
        
        # Crear operación
        operation_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        if alert_type == "rise":
            entry_alert = opposite_alert  # La bajada es la entrada
            exit_alert = alert  # La subida es la salida
            entry_price = entry_alert["verification_price"]
            exit_price = exit_alert["current_price"]
        else:
            entry_alert = opposite_alert  # La subida es la entrada
            exit_alert = alert  # La bajada es la salida
            entry_price = entry_alert["verification_price"]
            exit_price = exit_alert["current_price"]
        
        # Calcular ganancia/pérdida
        profit_pct = (exit_price - entry_price) / entry_price * 100
        
        # Crear registro de operación
        operation = {
            "id": operation_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "entry_alert_id": entry_alert["id"],
            "entry_alert_type": "drop" if alert_type == "rise" else "rise",
            "entry_price": entry_price,
            "entry_timestamp": entry_alert["verification_timestamp"],
            "exit_alert_id": exit_alert["id"],
            "exit_alert_type": alert_type,
            "exit_price": exit_price,
            "exit_timestamp": datetime.datetime.now().isoformat(),
            "profit_pct": profit_pct,
            "status": "closed"
        }
        
        # Añadir a la lista de operaciones
        self.operations.append(operation)
        
        # Actualizar alertas con el ID de la operación
        if alert_type == "rise":
            for a in self.rise_alerts:
                if a["id"] == alert["id"]:
                    a["operation_id"] = operation_id
                    break
            
            for a in self.drop_alerts:
                if a["id"] == opposite_alert["id"]:
                    a["operation_id"] = operation_id
                    break
        else:
            for a in self.drop_alerts:
                if a["id"] == alert["id"]:
                    a["operation_id"] = operation_id
                    break
            
            for a in self.rise_alerts:
                if a["id"] == opposite_alert["id"]:
                    a["operation_id"] = operation_id
                    break
        
        # Guardar cambios
        self._save_operations()
        self._save_rise_alerts()
        self._save_drop_alerts()
        
        return operation_id
    
    def get_operations_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de las operaciones.
        
        Returns:
            Estadísticas de operaciones
        """
        if not self.operations:
            return {"message": "No hay operaciones registradas"}
        
        # Calcular estadísticas generales
        total_operations = len(self.operations)
        profitable_operations = [op for op in self.operations if op["profit_pct"] > 0]
        total_profitable = len(profitable_operations)
        win_rate = total_profitable / total_operations * 100 if total_operations > 0 else 0
        
        # Calcular ganancia/pérdida promedio
        avg_profit = np.mean([op["profit_pct"] for op in self.operations])
        
        # Calcular ganancia/pérdida total
        total_profit = sum([op["profit_pct"] for op in self.operations])
        
        return {
            "total_operations": total_operations,
            "profitable_operations": total_profitable,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "total_profit": total_profit
        }
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las operaciones más recientes.
        
        Args:
            limit: Número máximo de operaciones a devolver
            
        Returns:
            Lista de operaciones
        """
        sorted_ops = sorted(self.operations, key=lambda x: x["timestamp"], reverse=True)
        return sorted_ops[:limit]
